"""
base_agent.py — Abstract Base Agent for Fabric-MAS
====================================================
Every Fabric item agent inherits from this class.
Provides the canonical five operations, autotrain hooks,
and automatic loading of per-agent knowledge files (.md).

Folder convention (one item = one agent = one folder):
    fabric_mas/agents/<agent-name>/
        ├── __init__.py
        ├── agent.py              # Agent class definition
        ├── instructions.md       # How the agent should behave, API refs
        ├── examples.md           # Few-shot examples + auto-logged prompt history
        └── known_issues.md       # Bugs, workarounds, gotchas
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from fabric_mas.core.cli_wrapper import FabricCLI
from fabric_mas.tools.search_tool import SearchTool

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
class OperationType(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ANALYZE = "analyze"
    DEPLOY = "deploy"


@dataclass
class AgentResult:
    """Standard envelope returned by every agent operation."""
    success: bool
    operation: OperationType
    agent_name: str
    item_type: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    cli_command: Optional[str] = None
    cli_output: Optional[str] = None
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "operation": self.operation.value,
            "agent_name": self.agent_name,
            "item_type": self.item_type,
            "message": self.message,
            "data": self.data,
            "cli_command": self.cli_command,
            "cli_output": self.cli_output,
            "errors": self.errors,
        }

    def __str__(self) -> str:
        status = "✅" if self.success else "❌"
        return f"{status} [{self.agent_name}] {self.operation.value}: {self.message}"


# ---------------------------------------------------------------------------
# Agent Knowledge — loaded from .md files in the agent's folder
# ---------------------------------------------------------------------------
@dataclass
class AgentKnowledge:
    """
    In-memory representation of the agent's knowledge base.
    Each .md file in the agent folder maps to an attribute.
    The orchestrator / LLM can read these at runtime for grounded behaviour.
    """
    instructions: str = ""
    examples: str = ""          # Unified: few-shot examples + auto-logged prompt history
    known_issues: str = ""
    _folder: Optional[Path] = field(default=None, repr=False)

    @classmethod
    def load_from_folder(cls, folder: Path) -> "AgentKnowledge":
        """Read all .md knowledge files from the agent's folder."""
        knowledge = cls(_folder=folder)
        md_map = {
            "instructions.md": "instructions",
            "examples.md": "examples",
            "known_issues.md": "known_issues",
        }
        for filename, attr in md_map.items():
            filepath = folder / filename
            if filepath.exists():
                try:
                    content = filepath.read_text(encoding="utf-8")
                    setattr(knowledge, attr, content)
                    logger.debug("Loaded knowledge: %s (%d chars)", filepath, len(content))
                except Exception as exc:
                    logger.warning("Failed to read %s: %s", filepath, exc)
        return knowledge

    def save_to_folder(self, folder: Optional[Path] = None) -> None:
        """Persist knowledge back to disk (for self-training / memory updates)."""
        target = folder or self._folder
        if target is None:
            logger.warning("No folder set — cannot save knowledge.")
            return
        target.mkdir(parents=True, exist_ok=True)
        md_map = {
            "instructions.md": self.instructions,
            "examples.md": self.examples,
            "known_issues.md": self.known_issues,
        }
        for filename, content in md_map.items():
            if content:
                (target / filename).write_text(content, encoding="utf-8")

    def to_context_string(self) -> str:
        """Combine all knowledge into a single context block for LLM prompts."""
        parts: List[str] = []
        if self.instructions:
            parts.append(f"## Agent Instructions\n{self.instructions}")
        if self.examples:
            parts.append(f"## Examples & Learned Patterns\n{self.examples}")
        if self.known_issues:
            parts.append(f"## Known Issues & Workarounds\n{self.known_issues}")
        return "\n\n---\n\n".join(parts) if parts else "(no knowledge loaded)"

    @property
    def has_knowledge(self) -> bool:
        return bool(self.instructions or self.examples or self.known_issues)

    # ------------------------------------------------------------------
    # Auto-learning — append executed prompts to examples.md
    # ------------------------------------------------------------------
    def log_prompt(
        self,
        prompt: str,
        operation: str,
        result_summary: str,
        *,
        success: bool = True,
    ) -> None:
        """
        Append a prompt + result to examples.md on disk.
        This builds an ever-growing memory of real usage patterns so the LLM
        can ground future planning on actual past executions.
        """
        from datetime import datetime, timezone

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        status = "✅ Success" if success else "❌ Failed"
        entry = (
            f"\n### {timestamp} — {operation.upper()} [{status}]\n"
            f"**Prompt:** {prompt}\n\n"
            f"**Result:** {result_summary}\n\n"
            f"---\n"
        )
        self.examples += entry

        # Persist to disk immediately
        folder = self._folder
        if folder and folder.is_dir():
            ex_path = folder / "examples.md"
            try:
                with open(ex_path, "a", encoding="utf-8") as f:
                    f.write(entry)
                logger.debug("Logged prompt to %s", ex_path)
            except Exception as exc:
                logger.warning("Failed to write prompt log to %s: %s", ex_path, exc)


# ---------------------------------------------------------------------------
# Base Agent
# ---------------------------------------------------------------------------
class BaseAgent(ABC):
    """
    Abstract base class for all Fabric item agents.

    Concrete agents set:
        ITEM_TYPE         – e.g. "Lakehouse", "Notebook"
        ITEM_CODE         – short code, e.g. "LH", "NB"
        FAB_NOUN          – noun for `fab <noun> ...` CLI commands
        AGENT_FOLDER_NAME – folder name under fabric_mas/agents/ (e.g. "lakehouse-agent")

    Knowledge files (.md) are auto-loaded from the agent's folder on init.
    """

    ITEM_TYPE: str = ""
    ITEM_CODE: str = ""
    FAB_NOUN: str = ""
    AGENT_FOLDER_NAME: str = ""

    def __init__(
        self,
        workspace_id: Optional[str] = None,
        *,
        cli: Optional[FabricCLI] = None,
        rest_client: Optional[Any] = None,
        search: Optional[SearchTool] = None,
        autotrain: bool = True,
    ):
        self.workspace_id = workspace_id
        self.cli = cli or FabricCLI()
        self.rest_client = rest_client  # FabricRestClient (preferred over CLI)
        self.search = search or SearchTool()
        self.autotrain = autotrain
        self._api_cache: Dict[str, Any] = {}

        # ── Load knowledge from agent folder ──
        self.knowledge = self._load_knowledge()
        logger.info(
            "Agent ready: %s [%s] — knowledge: %s",
            self.ITEM_TYPE,
            self.ITEM_CODE,
            "✓ loaded" if self.knowledge.has_knowledge else "○ empty",
        )

    # ------------------------------------------------------------------
    # Knowledge loading
    # ------------------------------------------------------------------
    def _load_knowledge(self) -> AgentKnowledge:
        """Discover the agent's folder and load .md knowledge files."""
        if not self.AGENT_FOLDER_NAME:
            return AgentKnowledge()
        agents_dir = (
            Path(__file__).resolve().parent.parent / "agents" / self.AGENT_FOLDER_NAME
        )
        if agents_dir.is_dir():
            return AgentKnowledge.load_from_folder(agents_dir)
        logger.debug("Agent folder not found: %s", agents_dir)
        return AgentKnowledge()

    def get_agent_folder(self) -> Path:
        """Return the absolute path to this agent's folder."""
        return Path(__file__).resolve().parent.parent / "agents" / self.AGENT_FOLDER_NAME

    # ------------------------------------------------------------------
    # Autotrain — live-fetch the latest API/CLI spec before executing
    # ------------------------------------------------------------------
    def _autotrain(self, operation: str) -> Optional[Dict[str, Any]]:
        """Fetch the latest REST/CLI reference for this item + operation."""
        if not self.autotrain:
            return None
        cache_key = f"{self.ITEM_TYPE}:{operation}"
        if cache_key in self._api_cache:
            return self._api_cache[cache_key]
        query = (
            f"Microsoft Fabric REST API {self.ITEM_TYPE} {operation} "
            f"endpoint parameters 2025"
        )
        logger.info("Autotrain search: %s", query)
        result = self.search.search(query)
        self._api_cache[cache_key] = result
        return result

    # ------------------------------------------------------------------
    # CLI helpers
    # ------------------------------------------------------------------
    def _build_fab_command(self, verb: str, **kwargs: Any) -> str:
        """Build a `fab` CLI command string."""
        parts = ["fab", self.FAB_NOUN, verb]
        for key, value in kwargs.items():
            if value is None:
                continue
            flag = f"--{key.replace('_', '-')}"
            if isinstance(value, bool):
                if value:
                    parts.append(flag)
            else:
                parts.extend([flag, f'"{value}"'])
        return " ".join(parts)

    def _resolve_workspace(self, workspace_id: Optional[str] = None) -> Optional[str]:
        """Resolve workspace name/ID to a GUID using the REST client."""
        ws = workspace_id or self.workspace_id
        if ws and self.rest_client:
            resolved = self.rest_client.resolve_workspace_id(ws)
            if resolved:
                return resolved
        return ws

    def _run_rest(
        self,
        operation: str,
        params: Dict[str, Any],
    ) -> Optional[AgentResult]:
        """
        Execute an operation via REST API instead of CLI.
        Returns None if REST client is not available (falls back to CLI).
        """
        if not self.rest_client:
            return None

        ws = self._resolve_workspace(params.get("workspace_id"))
        if not ws:
            return AgentResult(
                success=False,
                operation=OperationType.CREATE,
                agent_name=self.__class__.__name__,
                item_type=self.ITEM_TYPE,
                message="No workspace ID provided or resolved",
                errors=["workspace_id is required"],
            )

        try:
            if operation == "create":
                result = self.rest_client.create_item(
                    workspace_id=ws,
                    item_type=self.ITEM_TYPE,
                    display_name=params.get("display_name", "Untitled"),
                    description=params.get("description", ""),
                )
            elif operation == "delete":
                item_id = params.get("item_id", "")
                if not item_id:
                    return AgentResult(
                        success=False, operation=OperationType.DELETE,
                        agent_name=self.__class__.__name__,
                        item_type=self.ITEM_TYPE,
                        message="item_id required for delete",
                        errors=["item_id missing"],
                    )
                result = self.rest_client.delete_item(ws, item_id)
            elif operation in ("analyze", "list"):
                result = self.rest_client.list_items(ws, self.ITEM_TYPE)
            elif operation == "update":
                item_id = params.get("item_id", "")
                result = self.rest_client.update_item(
                    ws, item_id,
                    display_name=params.get("display_name"),
                    description=params.get("description"),
                )
            else:
                return None  # Unsupported operation, fall back to CLI

            op_type = {
                "create": OperationType.CREATE,
                "delete": OperationType.DELETE,
                "update": OperationType.UPDATE,
                "analyze": OperationType.ANALYZE,
                "list": OperationType.ANALYZE,
            }.get(operation, OperationType.CREATE)

            if result.success:
                import json as _json
                data_str = _json.dumps(result.data, indent=2, default=str) if result.data else ""
                return AgentResult(
                    success=True,
                    operation=op_type,
                    agent_name=self.__class__.__name__,
                    item_type=self.ITEM_TYPE,
                    message=f"{operation.title()} {self.ITEM_TYPE} succeeded",
                    data=result.data,
                    cli_command=f"REST API: {operation} {self.ITEM_TYPE}",
                    cli_output=data_str,
                )
            else:
                return AgentResult(
                    success=False,
                    operation=op_type,
                    agent_name=self.__class__.__name__,
                    item_type=self.ITEM_TYPE,
                    message=f"{operation.title()} {self.ITEM_TYPE} failed: {result.error}",
                    errors=[result.error],
                    cli_command=f"REST API: {operation} {self.ITEM_TYPE}",
                )
        except Exception as exc:
            logger.error("REST API error: %s", exc)
            return None  # Fall back to CLI

    def _run(self, command: str) -> AgentResult:
        """Execute a fab command and wrap the output in an AgentResult."""
        exit_code, stdout, stderr = self.cli.run(command)
        success = exit_code == 0
        return AgentResult(
            success=success,
            operation=OperationType.CREATE,
            agent_name=self.__class__.__name__,
            item_type=self.ITEM_TYPE,
            message=stdout.strip() if success else stderr.strip(),
            cli_command=command,
            cli_output=stdout,
            errors=[stderr] if stderr and not success else [],
        )

    def _make_result(
        self,
        operation: OperationType,
        success: bool,
        message: str,
        **extra: Any,
    ) -> AgentResult:
        return AgentResult(
            success=success,
            operation=operation,
            agent_name=self.__class__.__name__,
            item_type=self.ITEM_TYPE,
            message=message,
            **extra,
        )

    # ------------------------------------------------------------------
    # Canonical operations (override in subclasses)
    # ------------------------------------------------------------------
    @abstractmethod
    def create(self, params: Dict[str, Any]) -> AgentResult:
        """Create a new Fabric item."""
        ...

    @abstractmethod
    def update(self, item_id: str, params: Dict[str, Any]) -> AgentResult:
        """Update an existing Fabric item."""
        ...

    @abstractmethod
    def delete(self, item_id: str) -> AgentResult:
        """Delete a Fabric item."""
        ...

    @abstractmethod
    def analyze(self, item_id: Optional[str] = None, **kwargs: Any) -> AgentResult:
        """Analyse / inspect an item or list items."""
        ...

    @abstractmethod
    def deploy(self, item_id: str, target: str, **kwargs: Any) -> AgentResult:
        """Deploy / promote an item (e.g. across environments)."""
        ...

    # ------------------------------------------------------------------
    # Dispatch — called by the orchestrator
    # ------------------------------------------------------------------
    def execute(self, operation: str, params: Dict[str, Any]) -> AgentResult:
        """Generic dispatcher invoked by the orchestrator."""
        op_map = {
            "create": self.create,
            "update": self.update,
            "delete": self.delete,
            "analyze": self.analyze,
            "deploy": self.deploy,
        }
        handler = op_map.get(operation)
        if handler is None:
            return self._make_result(
                OperationType.CREATE,
                False,
                f"Unknown operation '{operation}' for {self.ITEM_TYPE}",
            )
        self._autotrain(operation)
        if operation == "create":
            return handler(params)
        elif operation == "update":
            return handler(params.pop("item_id", ""), params)
        elif operation == "delete":
            return handler(params.get("item_id", ""))
        elif operation == "analyze":
            return handler(**params)
        elif operation == "deploy":
            return handler(params.pop("item_id", ""), params.pop("target", ""), **params)
        return handler(params)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} [{self.ITEM_CODE}] ws={self.workspace_id}>"
