"""
base_agent.py — Abstract Base Agent for Fabric-MAS
====================================================
Every Fabric item agent inherits from this class.
Provides the canonical five operations, autotrain hooks,
automatic loading of per-agent knowledge files (.md),
and **naming convention enforcement** from Naming_Convention.md.

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
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fabric_mas.core.cli_wrapper import FabricCLI
from fabric_mas.tools.search_tool import SearchTool
from fabric_mas.tools.telemetry_emitter import emit_event, emit_step_start

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
# Naming Convention — loaded from Naming_Convention.md at project root
# ---------------------------------------------------------------------------
@dataclass
class NamingValidationResult:
    """Result of a naming convention check."""
    valid: bool
    original_name: str
    corrected_name: str
    prefix: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        if self.valid:
            return f"✅ Name '{self.original_name}' is valid"
        return (
            f"⚠️ Name '{self.original_name}' violates naming convention. "
            f"Suggested: '{self.corrected_name}'. Issues: {'; '.join(self.errors)}"
        )


class NamingConvention:
    """
    Loads and enforces naming conventions from Naming_Convention.md.

    The file contains a YAML-like ``validation:`` block that maps each
    Fabric item type to its required prefix.  This class:
    1. Parses those prefixes at load time.
    2. Validates any proposed ``display_name`` against the rules.
    3. Can auto-correct names (add prefix, fix casing, replace invalid chars).

    The file is re-read every time an agent is constructed, so edits to
    ``Naming_Convention.md`` take effect immediately.
    """

    _MAX_LENGTH = 80
    _ALLOWED_PATTERN = re.compile(r"^[A-Z0-9_]+$")

    def __init__(self, convention_file: Optional[Path] = None):
        self._prefixes: Dict[str, str] = {}
        self._raw_content: str = ""
        self._file_path = convention_file or self._default_path()
        self._load()

    @staticmethod
    def _default_path() -> Path:
        """Naming_Convention.md lives at the project root."""
        return Path(__file__).resolve().parent.parent.parent / "Naming_Convention.md"

    def _load(self) -> None:
        """Parse the validation block from Naming_Convention.md."""
        if not self._file_path.exists():
            logger.debug("Naming convention file not found: %s", self._file_path)
            return

        try:
            self._raw_content = self._file_path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.warning("Could not read naming convention file: %s", exc)
            return

        # Parse the YAML-like validation block:
        #   validation:
        #     Lakehouse: "LH_"
        #     Warehouse: "WH_"
        in_validation = False
        for line in self._raw_content.splitlines():
            stripped = line.strip()
            if stripped.startswith("validation:"):
                in_validation = True
                continue
            if in_validation:
                if stripped == "" or stripped.startswith("```") or stripped.startswith("#") or stripped.startswith("---"):
                    if self._prefixes:  # stop after block ends
                        break
                    continue
                # Parse lines like:  Lakehouse: "LH_"
                match = re.match(r'^(\w+):\s*["\']?([A-Z_]+)["\']?\s*$', stripped)
                if match:
                    item_type = match.group(1)
                    prefix = match.group(2)
                    self._prefixes[item_type] = prefix

        if self._prefixes:
            logger.debug(
                "Loaded naming conventions for %d item types", len(self._prefixes)
            )
        else:
            logger.debug("No naming prefixes found in %s", self._file_path)

    @property
    def loaded(self) -> bool:
        return bool(self._prefixes)

    @property
    def content(self) -> str:
        """Full raw content of the naming convention file."""
        return self._raw_content

    def get_prefix(self, item_type: str) -> Optional[str]:
        """
        Get the required prefix for an item type.

        Tries exact match first, then case-insensitive, then partial match.
        """
        # Exact match
        if item_type in self._prefixes:
            return self._prefixes[item_type]
        # Case-insensitive
        lower = item_type.lower()
        for k, v in self._prefixes.items():
            if k.lower() == lower:
                return v
        # Partial (e.g. "Lakehouse" matches "Lakehouse")
        for k, v in self._prefixes.items():
            if lower in k.lower() or k.lower() in lower:
                return v
        return None

    def validate(self, display_name: str, item_type: str) -> NamingValidationResult:
        """
        Validate a display_name against the naming convention.

        Returns a NamingValidationResult with:
        - valid: True if name passes all checks
        - corrected_name: auto-corrected version if invalid
        - errors: list of specific violations found
        """
        errors: List[str] = []
        warnings: List[str] = []
        prefix = self.get_prefix(item_type) or ""

        if not self.loaded:
            return NamingValidationResult(
                valid=True,
                original_name=display_name,
                corrected_name=display_name,
                prefix=prefix,
                warnings=["Naming convention file not loaded — skipping validation"],
            )

        original = display_name
        name = display_name.strip()

        # Rule 1: Convert to UPPER_SNAKE_CASE
        corrected = name.upper().replace(" ", "_").replace("-", "_")
        # Remove consecutive underscores
        corrected = re.sub(r"_+", "_", corrected)
        # Remove leading/trailing underscores
        corrected = corrected.strip("_")

        if corrected != name.upper().strip():
            errors.append(
                f"Must be UPPER_SNAKE_CASE (no spaces/hyphens, A-Z 0-9 _ only)"
            )

        # Rule 2: Check allowed characters
        if not self._ALLOWED_PATTERN.match(corrected):
            # Remove disallowed characters
            corrected = re.sub(r"[^A-Z0-9_]", "", corrected)
            errors.append("Contains disallowed characters (only A-Z, 0-9, _ allowed)")

        # Rule 3: Check prefix
        if prefix and not corrected.startswith(prefix):
            corrected = prefix + corrected
            errors.append(
                f"Missing required prefix '{prefix}' for {item_type}"
            )

        # Rule 4: Check length
        if len(corrected) > self._MAX_LENGTH:
            corrected = corrected[: self._MAX_LENGTH]
            warnings.append(
                f"Name exceeds {self._MAX_LENGTH} chars — truncated"
            )

        valid = len(errors) == 0
        return NamingValidationResult(
            valid=valid,
            original_name=original,
            corrected_name=corrected,
            prefix=prefix,
            errors=errors,
            warnings=warnings,
        )

    def suggest_name(self, item_type: str, *parts: str) -> str:
        """
        Generate a convention-compliant name from parts.

        Example:
            suggest_name("Lakehouse", "Sales", "Bronze") → "LH_SALES_BRONZE"
        """
        prefix = self.get_prefix(item_type) or ""
        clean_parts = []
        for p in parts:
            cleaned = p.upper().replace(" ", "_").replace("-", "_")
            cleaned = re.sub(r"[^A-Z0-9_]", "", cleaned)
            cleaned = cleaned.strip("_")
            if cleaned:
                clean_parts.append(cleaned)
        name = prefix + "_".join(clean_parts)
        name = re.sub(r"_+", "_", name)
        return name[: self._MAX_LENGTH]

    def get_all_prefixes(self) -> Dict[str, str]:
        """Return all item type → prefix mappings."""
        return dict(self._prefixes)


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

        # ── Load naming convention (shared across all agents) ──
        self.naming = NamingConvention()

        logger.info(
            "Agent ready: %s [%s] — knowledge: %s, naming: %s",
            self.ITEM_TYPE,
            self.ITEM_CODE,
            "✓ loaded" if self.knowledge.has_knowledge else "○ empty",
            "✓ loaded" if self.naming.loaded else "○ not found",
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

        Supported operations: create, delete, delete_by_name, analyze, list,
        update, get_definition, update_definition, find_by_name.
        """
        if not self.rest_client:
            return None

        ws = self._resolve_workspace(params.get("workspace_id"))
        if not ws and operation not in ("find_by_name",):
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
                    definition=params.get("definition"),
                )
            elif operation == "delete":
                item_id = params.get("item_id", "")
                if not item_id:
                    # Try delete by name
                    display_name = params.get("display_name", "")
                    if display_name:
                        return self._run_rest("delete_by_name", params)
                    return AgentResult(
                        success=False, operation=OperationType.DELETE,
                        agent_name=self.__class__.__name__,
                        item_type=self.ITEM_TYPE,
                        message="item_id or display_name required for delete",
                        errors=["item_id or display_name missing"],
                    )
                result = self.rest_client.delete_item(ws, item_id)
            elif operation == "delete_by_name":
                display_name = params.get("display_name", "")
                if not display_name:
                    return AgentResult(
                        success=False, operation=OperationType.DELETE,
                        agent_name=self.__class__.__name__,
                        item_type=self.ITEM_TYPE,
                        message="display_name required for delete_by_name",
                        errors=["display_name missing"],
                    )
                item = self.rest_client.find_item_by_name(display_name, ws, self.ITEM_TYPE)
                if not item:
                    return AgentResult(
                        success=False, operation=OperationType.DELETE,
                        agent_name=self.__class__.__name__,
                        item_type=self.ITEM_TYPE,
                        message=f"{self.ITEM_TYPE} '{display_name}' not found in workspace",
                        errors=[f"Item not found: {display_name}"],
                    )
                result = self.rest_client.delete_item(ws, item["id"])
                if result.success:
                    result.data = item  # Include the item metadata in response
            elif operation == "find_by_name":
                display_name = params.get("display_name", "")
                item = self.rest_client.find_item_by_name(display_name, ws, self.ITEM_TYPE)
                if item:
                    import json as _json
                    return AgentResult(
                        success=True,
                        operation=OperationType.ANALYZE,
                        agent_name=self.__class__.__name__,
                        item_type=self.ITEM_TYPE,
                        message=f"Found {self.ITEM_TYPE} '{display_name}'",
                        data=item,
                        cli_command=f"REST API: find {self.ITEM_TYPE} by name",
                        cli_output=_json.dumps(item, indent=2, default=str),
                    )
                return AgentResult(
                    success=False,
                    operation=OperationType.ANALYZE,
                    agent_name=self.__class__.__name__,
                    item_type=self.ITEM_TYPE,
                    message=f"{self.ITEM_TYPE} '{display_name}' not found",
                    errors=[f"Item not found: {display_name}"],
                )
            elif operation == "get_definition":
                item_id = params.get("item_id", "")
                if not item_id:
                    return AgentResult(
                        success=False, operation=OperationType.ANALYZE,
                        agent_name=self.__class__.__name__,
                        item_type=self.ITEM_TYPE,
                        message="item_id required for get_definition",
                        errors=["item_id missing"],
                    )
                result = self.rest_client.get_item_definition(ws, item_id, self.ITEM_TYPE)
            elif operation == "update_definition":
                item_id = params.get("item_id", "")
                definition = params.get("definition", {})
                if not item_id or not definition:
                    return AgentResult(
                        success=False, operation=OperationType.UPDATE,
                        agent_name=self.__class__.__name__,
                        item_type=self.ITEM_TYPE,
                        message="item_id and definition required for update_definition",
                        errors=["item_id or definition missing"],
                    )
                result = self.rest_client.update_item_definition(ws, item_id, definition, self.ITEM_TYPE)
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
                "delete_by_name": OperationType.DELETE,
                "update": OperationType.UPDATE,
                "update_definition": OperationType.UPDATE,
                "analyze": OperationType.ANALYZE,
                "list": OperationType.ANALYZE,
                "get_definition": OperationType.ANALYZE,
                "find_by_name": OperationType.ANALYZE,
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
                    data=result.data if isinstance(result.data, dict) else {"items": result.data},
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

    # ------------------------------------------------------------------
    # Cross-workspace item discovery helpers
    # ------------------------------------------------------------------
    def find_item_by_name(
        self,
        display_name: str,
        workspace_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Find a Fabric item of this agent's type by display name.

        Searches within a specific workspace or across all accessible
        workspaces. Returns dict with id, displayName, workspace_id, etc.
        """
        if not self.rest_client:
            return None
        ws = self._resolve_workspace(workspace_id) if workspace_id else None
        return self.rest_client.find_item_by_name(display_name, ws, self.ITEM_TYPE)

    def resolve_item_id(
        self,
        display_name: str,
        workspace_id: Optional[str] = None,
    ) -> Optional[str]:
        """Resolve item display_name → item_id (within a workspace or globally)."""
        item = self.find_item_by_name(display_name, workspace_id)
        return item.get("id") if item else None

    def get_item_definition(
        self,
        item_id: str,
        workspace_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get the definition (source content) of an item."""
        if not self.rest_client:
            return None
        ws = self._resolve_workspace(workspace_id) or self.workspace_id
        result = self.rest_client.get_item_definition(ws, item_id, self.ITEM_TYPE)
        return result.data if result.success else None

    def update_item_definition(
        self,
        item_id: str,
        definition: Dict[str, Any],
        workspace_id: Optional[str] = None,
    ) -> bool:
        """Update the definition of an item. Returns True on success."""
        if not self.rest_client:
            return False
        ws = self._resolve_workspace(workspace_id) or self.workspace_id
        result = self.rest_client.update_item_definition(ws, item_id, definition, self.ITEM_TYPE)
        return result.success

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
    # Naming convention enforcement
    # ------------------------------------------------------------------
    def validate_and_fix_name(
        self, params: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], NamingValidationResult]:
        """
        Validate and auto-correct ``display_name`` in params against
        the naming convention for this agent's ITEM_TYPE.

        Returns:
            (updated_params, validation_result)

        If the name violates the convention, ``display_name`` is replaced
        with the corrected version and a log message is emitted.
        """
        display_name = params.get("display_name", "")
        if not display_name:
            result = NamingValidationResult(
                valid=True,
                original_name="",
                corrected_name="",
                prefix="",
            )
            return params, result

        result = self.naming.validate(display_name, self.ITEM_TYPE)

        if not result.valid:
            logger.warning(
                "⚠️ Naming convention violation for %s: '%s' → '%s' | %s",
                self.ITEM_TYPE,
                result.original_name,
                result.corrected_name,
                "; ".join(result.errors),
            )
            # Auto-correct the name in params
            params = dict(params)  # shallow copy to avoid mutating original
            params["display_name"] = result.corrected_name

        if result.warnings:
            for w in result.warnings:
                logger.info("📏 Naming note: %s", w)

        return params, result

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
        params = dict(params)
        op_map = {
            "create": self.create,
            "update": self.update,
            "delete": self.delete,
            "analyze": self.analyze,
            "deploy": self.deploy,
        }

        # Extended REST-only operations (no CLI equivalent needed)
        rest_ops = {
            "find_by_name", "delete_by_name",
            "get_definition", "update_definition",
        }

        handler = op_map.get(operation)

        # Telemetry: mark step start
        emit_step_start(
            params.get("job_id", "unknown"),
            f"{self.ITEM_CODE}_{operation}"
        )

        error = None

        # For REST-only operations, route through _run_rest directly
        if operation in rest_ops:
            rest_result = self._run_rest(operation, params)
            if rest_result is not None:
                result = rest_result
            else:
                result = self._make_result(
                    OperationType.ANALYZE, False,
                    f"Operation '{operation}' requires REST client (not available)",
                )
        elif handler is None:
            result = self._make_result(
                OperationType.CREATE,
                False,
                f"Unknown operation '{operation}' for {self.ITEM_TYPE}",
            )
        else:
            try:
                self._autotrain(operation)

                # ── Naming convention enforcement on CREATE ──
                if operation == "create" and "display_name" in params:
                    params, naming_result = self.validate_and_fix_name(params)
                    if not naming_result.valid:
                        logger.info(
                            "📏 Auto-corrected name: '%s' → '%s'",
                            naming_result.original_name,
                            naming_result.corrected_name,
                        )

                if operation == "create":
                    result = handler(params)
                elif operation == "update":
                    result = handler(params.pop("item_id", ""), params)
                elif operation == "delete":
                    result = handler(params.get("item_id", ""))
                elif operation == "analyze":
                    result = handler(**params)
                elif operation == "deploy":
                    result = handler(params.pop("item_id", ""), params.pop("target", ""), **params)
                else:
                    result = handler(params)
            except Exception as exc:
                error = exc
                result = self._make_result(
                    OperationType.CREATE,
                    False,
                    f"{self.ITEM_TYPE} {operation} failed: {exc}",
                    errors=[str(exc)],
                )

        success = result.success

        # Telemetry: emit step result
        emit_event(
            job_id=params.get("job_id", "unknown"),
            job_name=params.get("job_name", self.__class__.__name__),
            agent=self.ITEM_CODE.lower().replace("_", "-"),
            operation=operation,
            cli_command=getattr(self, "_last_command", ""),
            status="ok" if success else "fail",
            tokens=params.get("_tokens", 0),
            detail=str(result)[:200],
            workspace=params.get("workspace", ""),
            item_name=params.get("display_name", params.get("item_name", "")),
            item_type=self.ITEM_TYPE,
            source_workspace=params.get("source_workspace", ""),
            source_item=params.get("source_item", ""),
            error_message=str(error)[:200] if not success and error is not None else "",
            step_key=f"{self.ITEM_CODE}_{operation}",
        )

        return result

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} [{self.ITEM_CODE}] ws={self.workspace_id}>"
