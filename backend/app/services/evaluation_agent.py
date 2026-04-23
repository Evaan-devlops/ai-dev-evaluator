"""
Lightweight task-specific evaluation agent — no langchain, no langgraph.

Four bounded steps:
  1. build_system_prompt  — synthesize evaluator persona from PRD
  2. gather_context       — fetch RAG knowledge + layer context + tool results
  3. generate_reference   — produce ideal answer with full context
  4. evaluate             — score model response per dimension (1-10 each) → /100

AgentState is the sole mutable object. Steps are sequential and strictly bounded.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.api.evaluation import (
        EvaluateModelResponseRequest,
        EvaluationParameterPayload,
        EvaluationProviderConfig,
        KnowledgeApiRequest,
        NamedConnectorRequest,
    )

from app.api.llm import LLMGenerateRequest, generate_text_with_provider


# ──────────────────────────────────────────────────────────────────────────────
# State
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class AgentState:
    """Working memory for one evaluation run.  Read by all steps; written only through
    the mutator helpers below so state transitions stay traceable."""
    query: str
    prd: str
    evaluation_params: list[EvaluationParameterPayload]
    model_response: str

    # Populated during run:
    system_prompt: str = ""
    layer_context: dict[str, str] = field(default_factory=dict)
    tool_results: list[str] = field(default_factory=list)
    retrieved_knowledge: str = ""
    reference_response: str = ""
    step_log: list[dict[str, Any]] = field(default_factory=list)

    # Lightweight memory: facts that survive across steps
    memory: dict[str, Any] = field(default_factory=dict)

    def log(self, step: str, note: str) -> None:
        self.step_log.append({"step": step, "note": note, "ts": datetime.now(timezone.utc).isoformat()})

    def param_labels(self) -> str:
        return ", ".join(f"{p.label} ({p.id})" for p in self.evaluation_params)

    def context_summary(self) -> str:
        parts: list[str] = []
        if self.retrieved_knowledge.strip():
            parts.append(f"[KNOWLEDGE]\n{self.retrieved_knowledge.strip()}")
        for layer_id, content in self.layer_context.items():
            if content.strip():
                parts.append(f"[{layer_id.upper()}]\n{content.strip()}")
        if self.tool_results:
            parts.append("[TOOLS]\n" + "\n\n".join(self.tool_results))
        return "\n\n".join(parts) or "No additional context available."


# ──────────────────────────────────────────────────────────────────────────────
# Agent
# ──────────────────────────────────────────────────────────────────────────────

class EvaluationAgent:
    """
    Task-specific bounded evaluation agent.

    Usage:
        agent = EvaluationAgent(provider_config, request)
        result = await agent.run()
    """

    def __init__(
        self,
        provider_config: EvaluationProviderConfig,
        request: EvaluateModelResponseRequest,
    ) -> None:
        self._cfg = provider_config
        self._req = request
        self._state = AgentState(
            query=request.user_prompt,
            prd=request.prd,
            evaluation_params=request.evaluation_parameters or [],
            model_response=request.model_response,
        )

    # ── Step 1: system prompt ─────────────────────────────────────────────────

    def _build_system_prompt(self) -> str:
        s = self._state
        param_list = s.param_labels() or "quality, accuracy, helpfulness"
        return (
            "You are an expert product quality evaluator. "
            "Your role is to assess whether AI model responses satisfy a Product Requirements Document (PRD).\n\n"
            f"Evaluation dimensions: {param_list}\n\n"
            "PRD:\n"
            f"{s.prd.strip()}\n\n"
            "Instructions:\n"
            "- Generate the best possible reference response using the PRD as ground truth.\n"
            "- Score the model response on each dimension from 1 to 10.\n"
            "- An overall score is the weighted average normalized to 100.\n"
            "- Provide specific actionable suggestions that cite PRD requirements.\n"
            "- Be objective. Flag gaps in coverage, factual errors, and tone mismatches."
        )

    # ── Step 2: gather context ────────────────────────────────────────────────

    async def _gather_context(self) -> None:
        from app.api.evaluation import _fetch_rag_knowledge, _determine_selected_layers, _fetch_layer_context
        s = self._state
        req = self._req

        # Knowledge from RAG or search API
        if req.rag_service_url.strip():
            s.retrieved_knowledge = await _fetch_rag_knowledge(
                req.rag_service_url.strip(),
                s.query,
                req.rag_document_id,
            )
            s.log("knowledge", f"RAG returned {len(s.retrieved_knowledge)} chars")
        if not s.retrieved_knowledge.strip() and req.knowledge_api and req.knowledge_api.search.enabled:
            from app.api.integrations import ConnectorExecuteRequest, execute_connector_request
            resp = await execute_connector_request(
                ConnectorExecuteRequest(
                    prompt=s.query,
                    connector=req.knowledge_api.search,
                    timeout_ms=30_000,
                )
            )
            s.retrieved_knowledge = resp.extracted_text.strip()
            s.log("knowledge", f"Search API returned {len(s.retrieved_knowledge)} chars")

        # Layer context (system, history, state, tools)
        selected = await _determine_selected_layers(req)
        layer_ctx = await _fetch_layer_context(self._cfg, req, selected)
        # Store everything except user + knowledge (handled above)
        for lid, content in layer_ctx.items():
            if lid not in ("user", "knowledge"):
                s.layer_context[lid] = content

        # Tool APIs
        if req.tool_apis:
            from app.api.integrations import ConnectorExecuteRequest, execute_connector_request
            for tool in req.tool_apis:
                if not tool.enabled:
                    continue
                try:
                    resp = await execute_connector_request(
                        ConnectorExecuteRequest(prompt=s.query, connector=tool, timeout_ms=20_000)
                    )
                    if resp.extracted_text.strip():
                        s.tool_results.append(f"{tool.name or tool.id or 'Tool'}\n{resp.extracted_text.strip()}")
                except Exception as exc:
                    s.log("tool", f"{tool.name}: {exc}")

        s.memory["context_layers_used"] = list(s.layer_context.keys())
        s.memory["has_knowledge"] = bool(s.retrieved_knowledge.strip())
        s.log("gather_context", f"layers={list(s.layer_context.keys())} tools={len(s.tool_results)}")

    # ── Step 3: generate reference response ──────────────────────────────────

    async def _generate_reference(self) -> None:
        s = self._state
        payload = LLMGenerateRequest(
            provider=self._cfg.provider,
            model=self._cfg.model,
            api_key=self._cfg.api_key,
            system_instruction=s.system_prompt,
            input="\n\n".join(filter(None, [
                "Generate the ideal reference response for the following user prompt.",
                f"User prompt: {s.query}",
                "Context:",
                s.context_summary(),
                "Conversation history (if any):",
                s.layer_context.get("history", "None"),
                "Return plain text only. Be thorough and PRD-compliant.",
            ])),
            temperature=self._cfg.temperature,
            max_output_tokens=self._cfg.max_output_tokens,
        )
        s.reference_response = (await generate_text_with_provider(payload)).strip()
        s.log("reference", f"{len(s.reference_response)} chars generated")

    # ── Step 4: evaluate model response ───────────────────────────────────────

    async def _evaluate(self) -> dict[str, Any]:
        s = self._state
        params_json = json.dumps(
            [p.model_dump() for p in s.evaluation_params],
            ensure_ascii=False,
            indent=2,
        )

        scoring_input = "\n\n".join(filter(None, [
            "Evaluate the MODEL RESPONSE against the REFERENCE RESPONSE and PRD.",
            f"User prompt: {s.query}",
            "Reference response (ideal answer):",
            s.reference_response or "(not available)",
            "Model response (to be scored):",
            s.model_response,
            "Evaluation context summary:",
            s.context_summary(),
            "Evaluation parameters:",
            params_json,
            (
                'Return JSON: {"scores": {<param_id>: <int 1-10>, ...}, '
                '"overall_score": <int 0-100>, '
                '"insight": "<string>", '
                '"suggestions": ["<string>", ...]}'
            ),
        ]))

        payload = LLMGenerateRequest(
            provider=self._cfg.provider,
            model=self._cfg.model,
            api_key=self._cfg.api_key,
            system_instruction=s.system_prompt,
            input=scoring_input,
            temperature=min(self._cfg.temperature, 0.15),
            max_output_tokens=min(self._cfg.max_output_tokens, 1200),
        )
        raw = await generate_text_with_provider(payload)
        return self._parse_evaluation(raw)

    def _parse_evaluation(self, raw: str) -> dict[str, Any]:
        from app.api.evaluation import _parse_json_object
        try:
            parsed = _parse_json_object(raw)
        except Exception:
            parsed = {}

        raw_scores = parsed.get("scores", {})
        if not isinstance(raw_scores, dict):
            raw_scores = {}

        normalized: dict[str, int] = {}
        for param in self._state.evaluation_params:
            try:
                v = int(raw_scores.get(param.id, 5))
            except (TypeError, ValueError):
                v = 5
            normalized[param.id] = max(1, min(10, v))

        # Prefer LLM-provided overall score, else compute from per-param average
        try:
            overall = int(parsed.get("overall_score", 0))
            overall = max(0, min(100, overall))
        except (TypeError, ValueError):
            overall = 0

        if not overall and normalized:
            overall = round(sum(normalized.values()) / (len(normalized) * 10) * 100)

        suggestions = parsed.get("suggestions", [])
        if not isinstance(suggestions, list):
            suggestions = []

        return {
            "scores": normalized,
            "overall_score": overall,
            "insight": str(parsed.get("insight", "Evaluation completed.")),
            "suggestions": [str(s).strip() for s in suggestions if str(s).strip()],
        }

    # ── Orchestrator ─────────────────────────────────────────────────────────

    async def run(self) -> dict[str, Any]:
        """Execute all 4 steps and return the evaluation result."""
        s = self._state

        # Step 1: system prompt
        s.system_prompt = self._build_system_prompt()
        s.log("system_prompt", "built from PRD")

        # Step 2: gather context
        await self._gather_context()

        # Step 3: reference response
        await self._generate_reference()

        # Step 4: evaluate
        evaluation = await self._evaluate()
        s.log("evaluate", f"overall={evaluation['overall_score']}")

        return {
            "scores": evaluation["scores"],
            "overall_score": evaluation["overall_score"],
            "insight": evaluation["insight"],
            "suggestions": evaluation["suggestions"],
            "reference_response": s.reference_response,
            "selected_layers": list(s.layer_context.keys()),
            "used_context": {**s.layer_context, "knowledge": s.retrieved_knowledge},
            "agent_steps": s.step_log,
        }
