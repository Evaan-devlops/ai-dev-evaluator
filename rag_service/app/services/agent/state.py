from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.retrieval import RetrievalCandidate


@dataclass
class AgentState:
    query: str
    document_id: str
    step: int = 0
    accumulated_candidates: list[RetrievalCandidate] = field(default_factory=list)
    context_tokens_used: int = 0
    stopped_because: str = ""
    decision_steps: list[dict] = field(default_factory=list)

    def add_candidates(self, new_candidates: list[RetrievalCandidate]) -> None:
        existing_keys = {c.chunk_id or c.node_id or c.text[:80] for c in self.accumulated_candidates}
        for c in new_candidates:
            key = c.chunk_id or c.node_id or c.text[:80]
            if key not in existing_keys:
                self.accumulated_candidates.append(c)
                self.context_tokens_used += len(c.text) // 4
                existing_keys.add(key)

    def record_step(self, action: str, input_summary: str, result_summary: str) -> None:
        self.decision_steps.append({
            "step": self.step,
            "action": action,
            "input_summary": input_summary,
            "result_summary": result_summary,
        })
