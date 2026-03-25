"""
Orchestrator Agent — The Master Brain 🧠
=========================================
Meta-agent that represents the orchestration layer itself.
Unlike other agents that manage a single Fabric item, this agent
manages the routing, planning, and coordination of ALL other agents.

It participates in the knowledge system (instructions.md, fewshot_examples.md,
known_issues.md, sample_prompts.md) so the LLM planner can learn from past
orchestration patterns.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fabric_mas.core.base_agent import AgentResult, BaseAgent, OperationType


class OrchestratorAgent(BaseAgent):
    """
    Meta-agent representing the orchestration layer.

    This agent doesn't execute `fab` CLI commands directly.
    Instead it provides:
    - Self-description for the registry
    - Knowledge files that the LLM planner can reference
    - Prompt memory (sample_prompts.md) that grows over time
    """

    ITEM_TYPE = "Orchestrator"
    ITEM_CODE = "ORCH"
    FAB_NOUN = ""  # No CLI noun — this is a meta-agent
    AGENT_FOLDER_NAME = "orchestrator-agent"

    def create(self, params: Dict[str, Any]) -> AgentResult:
        return self._make_result(
            OperationType.CREATE,
            False,
            "Orchestrator is a meta-agent — it does not create Fabric items directly. "
            "Use a specific item agent instead.",
        )

    def update(self, item_id: str, params: Dict[str, Any]) -> AgentResult:
        return self._make_result(
            OperationType.UPDATE,
            False,
            "Orchestrator is a meta-agent — it does not update Fabric items directly.",
        )

    def delete(self, item_id: str) -> AgentResult:
        return self._make_result(
            OperationType.DELETE,
            False,
            "Orchestrator is a meta-agent — it does not delete Fabric items directly.",
        )

    def analyze(self, item_id: Optional[str] = None, **kwargs: Any) -> AgentResult:
        """Return a summary of the orchestrator's knowledge and prompt history."""
        stats = {
            "knowledge_loaded": self.knowledge.has_knowledge,
            "instructions_chars": len(self.knowledge.instructions),
            "fewshot_chars": len(self.knowledge.fewshot_examples),
            "known_issues_chars": len(self.knowledge.known_issues),
            "sample_prompts_chars": len(self.knowledge.sample_prompts),
        }
        return self._make_result(
            OperationType.ANALYZE,
            True,
            f"Orchestrator knowledge stats: {stats}",
            data=stats,
        )

    def deploy(self, item_id: str, target: str, **kwargs: Any) -> AgentResult:
        return self._make_result(
            OperationType.DEPLOY,
            False,
            "Orchestrator is a meta-agent — it does not deploy Fabric items directly.",
        )
