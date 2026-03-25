"""
cli_wrapper.py — Subprocess Wrapper for the Microsoft Fabric CLI (`fab`)
=========================================================================
All agent CLI interactions are funnelled through this class so we can
centralise logging, error handling, retries, and dry-run support.
"""

from __future__ import annotations

import json
import logging
import os
import shlex
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class CLIResult:
    """Raw result of a CLI invocation."""
    exit_code: int
    stdout: str
    stderr: str
    command: str
    elapsed_seconds: float


class FabricCLI:
    """
    Thin wrapper around the `fab` (ms-fabric-cli) command-line tool.

    Features
    --------
    - Automatic workspace-id injection when a default is set.
    - JSON output parsing when --output json is used.
    - Dry-run mode for testing.
    - Configurable timeout and retry.
    """

    def __init__(
        self,
        fab_path: str = "fab",
        default_workspace_id: Optional[str] = None,
        timeout: int = 120,
        retries: int = 2,
        dry_run: bool = False,
    ):
        self.fab_path = fab_path
        self.default_workspace_id = default_workspace_id
        self.timeout = timeout
        self.retries = retries
        self.dry_run = dry_run

    # ------------------------------------------------------------------
    # Low-level execution
    # ------------------------------------------------------------------
    def run(self, command: str) -> Tuple[int, str, str]:
        """
        Execute a raw CLI command string.
        Returns (exit_code, stdout, stderr).
        """
        if self.dry_run:
            logger.info("[DRY-RUN] %s", command)
            return (0, f"[dry-run] {command}", "")

        logger.info("CLI exec: %s", command)
        last_err = ""
        for attempt in range(1, self.retries + 1):
            try:
                start = time.monotonic()
                proc = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
                elapsed = time.monotonic() - start
                result = CLIResult(
                    exit_code=proc.returncode,
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    command=command,
                    elapsed_seconds=round(elapsed, 2),
                )
                if proc.returncode == 0:
                    logger.info(
                        "CLI success (%ss): %s", result.elapsed_seconds, command
                    )
                    return (result.exit_code, result.stdout, result.stderr)
                else:
                    last_err = proc.stderr
                    logger.warning(
                        "CLI attempt %d/%d failed (rc=%d): %s",
                        attempt,
                        self.retries,
                        proc.returncode,
                        proc.stderr.strip(),
                    )
            except subprocess.TimeoutExpired:
                last_err = f"Command timed out after {self.timeout}s"
                logger.error("CLI timeout on attempt %d/%d", attempt, self.retries)
            except Exception as exc:
                last_err = str(exc)
                logger.error("CLI error on attempt %d/%d: %s", attempt, self.retries, exc)

        return (1, "", last_err)

    # ------------------------------------------------------------------
    # Structured helpers
    # ------------------------------------------------------------------
    def run_json(self, command: str) -> Tuple[int, Any, str]:
        """
        Run a command that is expected to return JSON output.
        Returns (exit_code, parsed_json_or_None, stderr).
        """
        if "--output" not in command:
            command += " --output json"
        exit_code, stdout, stderr = self.run(command)
        if exit_code != 0:
            return (exit_code, None, stderr)
        try:
            data = json.loads(stdout)
            return (0, data, "")
        except json.JSONDecodeError as exc:
            logger.warning("JSON parse failed for CLI output: %s", exc)
            return (0, stdout, "")

    def fab(
        self,
        noun: str,
        verb: str,
        *,
        workspace_id: Optional[str] = None,
        flags: Optional[Dict[str, Any]] = None,
        positional: Optional[List[str]] = None,
    ) -> Tuple[int, str, str]:
        """
        Build and execute a structured `fab` command.

        Example:
            cli.fab("lakehouse", "create",
                    flags={"display_name": "Bronze", "description": "Raw layer"})
            # → fab lakehouse create --display-name "Bronze" --description "Raw layer"
        """
        parts = [self.fab_path, noun, verb]

        # Inject workspace
        ws = workspace_id or self.default_workspace_id
        if ws:
            parts.extend(["--workspace-id", f'"{ws}"'])

        # Flags
        if flags:
            for key, value in flags.items():
                flag = f"--{key.replace('_', '-')}"
                if isinstance(value, bool):
                    if value:
                        parts.append(flag)
                elif value is not None:
                    parts.extend([flag, f'"{value}"'])

        # Positional args
        if positional:
            parts.extend(positional)

        command = " ".join(parts)
        return self.run(command)

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    def version(self) -> str:
        """Return the installed `fab` version."""
        _, stdout, _ = self.run(f"{self.fab_path} --version")
        return stdout.strip()

    def check_auth(self) -> bool:
        """Return True if the CLI is authenticated."""
        code, _, _ = self.run(f"{self.fab_path} auth status")
        return code == 0

    def login(self) -> Tuple[int, str, str]:
        """Trigger interactive login."""
        return self.run(f"{self.fab_path} auth login")
