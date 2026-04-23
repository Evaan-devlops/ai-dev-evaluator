from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.integrations import (
    ConnectorExecuteRequest,
    ConnectorExecuteResponse,
    ConnectorRequest,
    DatabaseConfigureRequest,
    execute_connector_request,
    _find_postgres_cli,
)
from app.api.llm import (
    LLMEmbeddingRequest,
    LLMGenerateRequest,
    generate_embedding_with_provider,
    generate_text_with_provider,
)

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])

Provider = Literal["mock", "gemini", "openai", "nvidia"]
LayerType = Literal["system", "user", "history", "knowledge", "tools", "state"]
DataSourceMode = Literal["mock", "manual", "actual"]


class EvaluationProviderConfig(BaseModel):
    provider: Provider
    model: str
    api_key: str = ""
    temperature: float = 0.2
    max_output_tokens: int = 1200


class EvaluationParameterPayload(BaseModel):
    id: str
    label: str
    description: str = ""


class ManualLayerPayload(BaseModel):
    id: LayerType
    enabled: bool
    content: str = ""


class NamedConnectorRequest(ConnectorRequest):
    id: str = ""
    name: str = ""


class KnowledgeApiRequest(BaseModel):
    ingestion: NamedConnectorRequest
    search: NamedConnectorRequest


class EvaluatePrdRequest(BaseModel):
    prd: str
    existing_parameters: list[EvaluationParameterPayload] = Field(default_factory=list)
    provider_config: EvaluationProviderConfig


class EvaluatePrdResponse(BaseModel):
    ok: bool
    parameters: list[EvaluationParameterPayload]
    rationale: str


class EvaluateModelResponseRequest(BaseModel):
    prd: str
    evaluation_parameters: list[EvaluationParameterPayload]
    user_prompt: str
    model_response: str
    provider_config: EvaluationProviderConfig
    data_source: DataSourceMode = "manual"
    manual_layers: list[ManualLayerPayload] = Field(default_factory=list)
    actual_data_integrations: list[NamedConnectorRequest] = Field(default_factory=list)
    knowledge_api: KnowledgeApiRequest | None = None
    tool_apis: list[NamedConnectorRequest] = Field(default_factory=list)
    database_config: DatabaseConfigureRequest | None = None
    system_prompt_text: str = ""
    rag_service_url: str = ""
    rag_document_id: str = ""


class EvaluateModelResponseResponse(BaseModel):
    ok: bool
    score_breakdown: dict[str, int]
    quality_score: int
    score_max: int
    insight: str
    suggestions: list[str]
    evaluation_provider: str
    reference_response: str
    selected_layers: list[LayerType]
    used_context: dict[str, str]
    latency_ms: int


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return stripped


def _parse_json_object(text: str) -> dict[str, Any]:
    cleaned = _strip_code_fence(text)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise HTTPException(status_code=400, detail="LLM did not return valid JSON.")
        try:
            parsed = json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail=f"LLM returned malformed JSON: {exc.msg}") from exc

    if not isinstance(parsed, dict):
        raise HTTPException(status_code=400, detail="LLM JSON payload must be an object.")
    return parsed


def _slugify(value: str) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "-" for char in value.strip())
    while "--" in normalized:
        normalized = normalized.replace("--", "-")
    return normalized.strip("-") or "parameter"


def _fallback_parameters(prd: str, existing: list[EvaluationParameterPayload]) -> list[EvaluationParameterPayload]:
    if existing:
        return existing

    if not prd.strip():
        return [
            EvaluationParameterPayload(id="accuracy", label="Accuracy", description="Faithfulness to the requested product behavior."),
            EvaluationParameterPayload(id="clarity", label="Clarity", description="Clear and easy-to-follow response."),
            EvaluationParameterPayload(id="actionability", label="Actionability", description="Specific next steps or decision support."),
        ]

    keywords = [
        ("requirements-coverage", "Requirements Coverage", "How well the response covers the PRD requirements."),
        ("policy-alignment", "Policy Alignment", "How accurately the response follows the PRD constraints and policies."),
        ("user-experience", "User Experience", "How well the response supports the intended UX or user journey."),
        ("edge-cases", "Edge Case Handling", "How well the response accounts for failure cases and exceptions."),
    ]
    return [EvaluationParameterPayload(id=item[0], label=item[1], description=item[2]) for item in keywords]


async def _summarize_layer_content(
    provider_config: EvaluationProviderConfig,
    layer_id: LayerType,
    content: str,
    prd: str,
    user_prompt: str,
) -> str:
    if not content.strip():
        return ""

    if provider_config.provider == "mock" or not provider_config.api_key.strip():
        return content.strip()

    payload = LLMGenerateRequest(
        provider=provider_config.provider,
        model=provider_config.model,
        api_key=provider_config.api_key,
        input="\n\n".join([
            f"Layer: {layer_id}",
            f"User prompt: {user_prompt}",
            "Summarize this source into compact evaluator context. Keep only the facts needed for scoring the model response against the PRD.",
            "Source payload:",
            content.strip(),
            "PRD:",
            prd.strip(),
        ]),
        system_instruction="Return concise plain text. Do not mention that you are summarizing.",
        temperature=min(provider_config.temperature, 0.3),
        max_output_tokens=min(provider_config.max_output_tokens, 700),
    )
    summarized = await generate_text_with_provider(payload)
    return summarized.strip() or content.strip()


async def _summarize_history_turns(
    provider_config: EvaluationProviderConfig,
    raw_history: str,
    user_prompt: str,
) -> str:
    if provider_config.provider == "mock" or not provider_config.api_key.strip():
        return raw_history.strip()

    payload = LLMGenerateRequest(
        provider=provider_config.provider,
        model=provider_config.model,
        api_key=provider_config.api_key,
        input="\n\n".join([
            "The following is conversation history that may contain multiple turns or sessions.",
            f"Current user prompt: {user_prompt}",
            "Summarize the conversation history into a compact, chronological context narrative.",
            "Preserve key facts, decisions, and user preferences. Omit redundant or off-topic turns.",
            "History:",
            raw_history.strip(),
        ]),
        system_instruction="Return plain text only. Be concise. Do not explain what you are doing.",
        temperature=0.1,
        max_output_tokens=600,
    )
    summarized = await generate_text_with_provider(payload)
    return summarized.strip() or raw_history.strip()


async def _fetch_rag_knowledge(
    rag_service_url: str,
    user_prompt: str,
    document_id: str = "",
) -> str:
    import httpx

    url = rag_service_url.rstrip("/") + "/api/v1/queries/ask"
    if not document_id.strip():
        return ""
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, json={"document_id": document_id.strip(), "query": user_prompt, "top_k": 6})
            resp.raise_for_status()
            data = resp.json()
            answer = data.get("answer", "").strip()
            citations = data.get("citations", [])
            if citations:
                citation_lines = [
                    f"[Source: {c.get('title', 'Unknown')} p.{c.get('page', '?')}]"
                    for c in citations[:4]
                ]
                return answer + "\n" + "\n".join(citation_lines) if answer else "\n".join(citation_lines)
            return answer
    except Exception:
        return ""


async def _fetch_layer_context(
    provider_config: EvaluationProviderConfig,
    request: EvaluateModelResponseRequest,
    selected_layers: list[LayerType],
) -> dict[str, str]:
    manual_lookup = {layer.id: layer for layer in request.manual_layers}
    hidden_context: dict[str, str] = {}

    for layer_id in selected_layers:
        if layer_id == "user":
            hidden_context[layer_id] = request.user_prompt
            continue

        raw_content = ""
        if request.data_source == "manual":
            raw_content = manual_lookup.get(layer_id, ManualLayerPayload(id=layer_id, enabled=False)).content
        elif request.data_source == "actual":
            connector: ConnectorRequest | None = None
            if layer_id == "system":
                # Try API connector first; fall back to system_prompt_text
                for integration in request.actual_data_integrations:
                    if (integration.id == "system" or integration.name.lower().startswith("system")) and integration.enabled:
                        connector = integration
                        break
                if connector:
                    resp = await execute_connector_request(
                        ConnectorExecuteRequest(prompt=request.user_prompt, connector=connector, timeout_ms=45_000),
                    )
                    raw_content = resp.extracted_text.strip()
                if not raw_content and request.system_prompt_text.strip():
                    raw_content = request.system_prompt_text.strip()
            elif layer_id == "knowledge":
                # Use RAG service if URL is provided, otherwise fall back to connector
                if request.rag_service_url.strip():
                    raw_content = await _fetch_rag_knowledge(
                        request.rag_service_url.strip(),
                        request.user_prompt,
                        request.rag_document_id,
                    )
                if not raw_content and request.knowledge_api:
                    connector = request.knowledge_api.search
            elif layer_id == "tools":
                enabled_tools = [tool for tool in request.tool_apis if tool.enabled]
                if enabled_tools:
                    tool_parts: list[str] = []
                    for tool in enabled_tools:
                        response = await execute_connector_request(
                            ConnectorExecuteRequest(prompt=request.user_prompt, connector=tool, timeout_ms=45_000),
                        )
                        if response.extracted_text.strip():
                            tool_parts.append(f"{tool.name or tool.id or 'Tool API'}\n{response.extracted_text.strip()}")
                    raw_content = "\n\n".join(tool_parts)
            else:
                for integration in request.actual_data_integrations:
                    if integration.id == layer_id or integration.name.lower().startswith(layer_id):
                        connector = integration
                        break
                if connector is None:
                    connector = next((integration for integration in request.actual_data_integrations if integration.id == layer_id), None)

            if connector and not raw_content:
                response = await execute_connector_request(
                    ConnectorExecuteRequest(prompt=request.user_prompt, connector=connector, timeout_ms=45_000),
                )
                raw_content = response.extracted_text.strip()

        if raw_content.strip():
            # History layer: summarize when content likely contains multiple turns
            if layer_id == "history" and _looks_like_multi_turn(raw_content):
                raw_content = await _summarize_history_turns(provider_config, raw_content, request.user_prompt)
            hidden_context[layer_id] = await _summarize_layer_content(
                provider_config,
                layer_id,
                raw_content,
                request.prd,
                request.user_prompt,
            )

    return hidden_context


def _looks_like_multi_turn(content: str) -> bool:
    turn_markers = ("user:", "assistant:", "human:", "ai:", "bot:", "[user]", "[assistant]", "[human]", "[ai]")
    lower = content.lower()
    count = sum(1 for marker in turn_markers if marker in lower)
    return count >= 4 or content.count("\n\n") >= 5


def layer_id_guess(connector: NamedConnectorRequest) -> str:
    connector_id = (connector.id or "").strip()
    if connector_id:
        return connector_id
    name = (connector.name or "").strip().lower()
    for candidate in ("system", "history", "state", "knowledge", "tools"):
        if candidate in name:
            return candidate
    return name or "connector"


async def _determine_selected_layers(request: EvaluateModelResponseRequest) -> list[LayerType]:
    available_layers: list[LayerType] = ["user"]
    if request.data_source == "manual":
        available_layers.extend([layer.id for layer in request.manual_layers if layer.enabled and layer.id != "user" and layer.content.strip()])
    elif request.data_source == "actual":
        has_system_api = any(
            integration.enabled and (integration.id == "system" or integration.name.lower().startswith("system"))
            for integration in request.actual_data_integrations
        )
        if has_system_api or request.system_prompt_text.strip():
            available_layers.append("system")
        for integration in request.actual_data_integrations:
            guessed = layer_id_guess(integration)
            if integration.enabled and guessed in {"history", "state"}:
                available_layers.append(guessed)  # type: ignore[arg-type]
        rag_configured = bool(request.rag_service_url.strip() and request.rag_document_id.strip())
        knowledge_connector_enabled = request.knowledge_api is not None and request.knowledge_api.search.enabled
        if rag_configured or knowledge_connector_enabled:
            available_layers.append("knowledge")
        if any(tool.enabled for tool in request.tool_apis):
            available_layers.append("tools")

    deduped_available = list(dict.fromkeys(available_layers))

    if request.provider_config.provider == "mock" or not request.provider_config.api_key.strip():
        return deduped_available

    planner_payload = LLMGenerateRequest(
        provider=request.provider_config.provider,
        model=request.provider_config.model,
        api_key=request.provider_config.api_key,
        input="\n\n".join([
            "Given the PRD and user prompt, choose which context layers are needed to evaluate the model response.",
            f"Available layers: {', '.join(deduped_available)}",
            f"User prompt: {request.user_prompt}",
            "PRD:",
            request.prd,
            "Return JSON with {\"selected_layers\": [...], \"reasoning\": \"...\"}.",
        ]),
        system_instruction="Only choose from the provided available layers. Always include user if available. Respond with valid JSON only.",
        temperature=min(request.provider_config.temperature, 0.2),
        max_output_tokens=500,
    )
    raw_plan = await generate_text_with_provider(planner_payload)
    parsed = _parse_json_object(raw_plan)
    selected = parsed.get("selected_layers", [])
    if not isinstance(selected, list):
        return deduped_available

    normalized = [layer for layer in deduped_available if layer in selected or layer == "user"]
    return normalized or deduped_available


async def _generate_reference_response(
    provider_config: EvaluationProviderConfig,
    request: EvaluateModelResponseRequest,
    hidden_context: dict[str, str],
) -> str:
    context_blocks = []
    for layer_id, content in hidden_context.items():
        if layer_id == "user":
            continue
        context_blocks.append(f"[{layer_id.upper()}]\n{content}")

    reference_payload = LLMGenerateRequest(
        provider=provider_config.provider,
        model=provider_config.model,
        api_key=provider_config.api_key,
        input="\n\n".join([
            "Generate the evaluator-side reference response for the given user prompt using the PRD and selected context.",
            f"User prompt: {request.user_prompt}",
            "PRD:",
            request.prd,
            "Evaluation parameters:",
            json.dumps([parameter.model_dump() for parameter in request.evaluation_parameters], ensure_ascii=False, indent=2),
            "Selected hidden context:",
            "\n\n".join(context_blocks) or "No additional context",
        ]),
        system_instruction="Produce the best possible final answer to the user. Return plain text only.",
        temperature=request.provider_config.temperature,
        max_output_tokens=request.provider_config.max_output_tokens,
    )
    return (await generate_text_with_provider(reference_payload)).strip()


async def _evaluate_against_reference(
    provider_config: EvaluationProviderConfig,
    request: EvaluateModelResponseRequest,
    reference_response: str,
    hidden_context: dict[str, str],
) -> dict[str, Any]:
    parameters = request.evaluation_parameters or _fallback_parameters(request.prd, [])
    evaluation_payload = LLMGenerateRequest(
        provider=provider_config.provider,
        model=provider_config.model,
        api_key=provider_config.api_key,
        input="\n\n".join([
            "Evaluate the model response against the reference response and PRD.",
            f"User prompt: {request.user_prompt}",
            "PRD:",
            request.prd,
            "Evaluation parameters:",
            json.dumps([parameter.model_dump() for parameter in parameters], ensure_ascii=False, indent=2),
            "Reference response:",
            reference_response,
            "Model response:",
            request.model_response,
            "Hidden evaluation context summary:",
            json.dumps(hidden_context, ensure_ascii=False, indent=2),
            "Return JSON with keys: scores (object of parameter id -> 1..5), insight (string), suggestions (array of strings).",
        ]),
        system_instruction="Respond with valid JSON only. Keep suggestions concise and actionable.",
        temperature=min(provider_config.temperature, 0.2),
        max_output_tokens=900,
    )
    parsed = _parse_json_object(await generate_text_with_provider(evaluation_payload))
    scores = parsed.get("scores", {})
    if not isinstance(scores, dict):
        scores = {}

    normalized_scores: dict[str, int] = {}
    for parameter in parameters:
        raw_value = scores.get(parameter.id)
        try:
            score = int(raw_value)
        except (TypeError, ValueError):
            score = 3
        normalized_scores[parameter.id] = max(1, min(5, score))

    suggestions = parsed.get("suggestions", [])
    if not isinstance(suggestions, list):
        suggestions = []

    return {
        "scores": normalized_scores,
        "insight": str(parsed.get("insight", "Evaluation completed.")),
        "suggestions": [str(item).strip() for item in suggestions if str(item).strip()],
    }


def _escape_sql(value: str) -> str:
    return value.replace("'", "''")


def _database_is_configured(config: DatabaseConfigureRequest | None) -> bool:
    if config is None:
        return False
    return bool(config.connection_string.strip() or config.db_name.strip())


def _parse_db_cli_args(config: DatabaseConfigureRequest) -> tuple[str, str, str, str, str]:
    from app.api.integrations import _parse_db_request

    return _parse_db_request(config)


def _run_psql_sql(config: DatabaseConfigureRequest, sql: str) -> None:
    host, port, user, password, db_name = _parse_db_cli_args(config)
    psql = _find_postgres_cli("psql")
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False, encoding="utf-8") as handle:
        handle.write(sql)
        sql_path = Path(handle.name)

    try:
        import os
        import subprocess

        env = os.environ.copy()
        if password:
            env["PGPASSWORD"] = password

        result = subprocess.run(
            [psql, "-h", host, "-p", port, "-U", user, "-d", db_name, "-f", str(sql_path)],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise HTTPException(status_code=400, detail=f"Database write failed: {detail}")
    finally:
        sql_path.unlink(missing_ok=True)


async def _store_evaluation_artifacts(
    request: EvaluateModelResponseRequest,
    hidden_context: dict[str, str],
    reference_response: str,
    score_breakdown: dict[str, int],
    insight: str,
) -> None:
    if not _database_is_configured(request.database_config):
        return

    config = request.database_config
    assert config is not None

    run_token = datetime.now(timezone.utc).strftime("eval_%Y%m%d%H%M%S%f")
    create_sql = """
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE TABLE IF NOT EXISTS evaluation_runs (
      run_token text PRIMARY KEY,
      user_prompt text NOT NULL,
      prd text NOT NULL,
      model_response text NOT NULL,
      reference_response text NOT NULL,
      score_breakdown jsonb NOT NULL,
      insight text NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS evaluation_context_items (
      id bigserial PRIMARY KEY,
      run_token text NOT NULL,
      layer_id text NOT NULL,
      content text NOT NULL,
      embedding vector(1536),
      metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
      created_at timestamptz NOT NULL DEFAULT now()
    );
    """
    _run_psql_sql(config, create_sql)

    inserts = [
        "BEGIN;",
        (
            "INSERT INTO evaluation_runs (run_token, user_prompt, prd, model_response, reference_response, score_breakdown, insight) "
            f"VALUES ('{_escape_sql(run_token)}', '{_escape_sql(request.user_prompt)}', '{_escape_sql(request.prd)}', "
            f"'{_escape_sql(request.model_response)}', '{_escape_sql(reference_response)}', "
            f"'{_escape_sql(json.dumps(score_breakdown, ensure_ascii=False))}'::jsonb, '{_escape_sql(insight)}');"
        ),
    ]

    for layer_id, content in hidden_context.items():
        embedding = await generate_embedding_with_provider(
            LLMEmbeddingRequest(
                provider=request.provider_config.provider,
                api_key=request.provider_config.api_key,
                text=content,
            ),
        )
        vector_sql = "NULL"
        if embedding:
            vector_sql = f"'[{','.join(f'{value:.8f}' for value in embedding)}]'"

        metadata = json.dumps({"source": "evaluator-hidden-context"}, ensure_ascii=False)
        inserts.append(
            "INSERT INTO evaluation_context_items (run_token, layer_id, content, embedding, metadata) "
            f"VALUES ('{_escape_sql(run_token)}', '{_escape_sql(layer_id)}', '{_escape_sql(content)}', {vector_sql}, "
            f"'{_escape_sql(metadata)}'::jsonb);"
        )

    inserts.append("COMMIT;")
    _run_psql_sql(config, "\n".join(inserts))


@router.post("/process-prd", response_model=EvaluatePrdResponse)
async def process_prd(payload: EvaluatePrdRequest) -> EvaluatePrdResponse:
    prd = payload.prd.strip()
    if not prd:
        raise HTTPException(status_code=400, detail="PRD is required.")

    if payload.provider_config.provider == "mock" or not payload.provider_config.api_key.strip():
        parameters = _fallback_parameters(prd, payload.existing_parameters)
        return EvaluatePrdResponse(
            ok=True,
            parameters=parameters,
            rationale="Used fallback parameter generation because no live provider is configured.",
        )

    llm_payload = LLMGenerateRequest(
        provider=payload.provider_config.provider,
        model=payload.provider_config.model,
        api_key=payload.provider_config.api_key,
        input="\n\n".join([
            "Analyze this PRD and propose the best evaluation parameters for scoring model responses.",
            "Return JSON with keys: parameters (array of {id,label,description}) and rationale (string).",
            "PRD:",
            prd,
            "Existing parameters:",
            json.dumps([parameter.model_dump() for parameter in payload.existing_parameters], ensure_ascii=False, indent=2),
        ]),
        system_instruction="Return valid JSON only. Keep parameter labels specific to the PRD.",
        temperature=min(payload.provider_config.temperature, 0.2),
        max_output_tokens=min(payload.provider_config.max_output_tokens, 900),
    )
    parsed = _parse_json_object(await generate_text_with_provider(llm_payload))
    raw_parameters = parsed.get("parameters", [])

    parameters: list[EvaluationParameterPayload] = []
    if isinstance(raw_parameters, list):
        for index, item in enumerate(raw_parameters):
            if not isinstance(item, dict):
                continue
            label = str(item.get("label", "")).strip()
            if not label:
                continue
            parameters.append(
                EvaluationParameterPayload(
                    id=_slugify(str(item.get("id", "")).strip() or label or f"parameter-{index + 1}"),
                    label=label,
                    description=str(item.get("description", "")).strip(),
                ),
            )

    if not parameters:
        parameters = _fallback_parameters(prd, payload.existing_parameters)

    return EvaluatePrdResponse(
        ok=True,
        parameters=parameters,
        rationale=str(parsed.get("rationale", "PRD processed successfully.")),
    )


@router.post("/evaluate-model-response", response_model=EvaluateModelResponseResponse)
async def evaluate_model_response(payload: EvaluateModelResponseRequest) -> EvaluateModelResponseResponse:
    if not payload.prd.strip():
        raise HTTPException(status_code=400, detail="PRD is required for evaluation.")
    if not payload.user_prompt.strip():
        raise HTTPException(status_code=400, detail="User prompt is required for evaluation.")
    if not payload.model_response.strip():
        raise HTTPException(status_code=400, detail="Model response is required for evaluation.")
    if payload.provider_config.provider == "mock" or not payload.provider_config.api_key.strip():
        raise HTTPException(status_code=400, detail="A live LLM provider and API key are required for result-side evaluation.")

    started_at = datetime.now(timezone.utc)
    if not payload.evaluation_parameters:
        payload = payload.model_copy(update={"evaluation_parameters": _fallback_parameters(payload.prd, [])})

    from app.services.evaluation_agent import EvaluationAgent
    agent = EvaluationAgent(payload.provider_config, payload)
    result = await agent.run()

    score_breakdown = result["scores"]       # per-param 1-10
    quality_score = result["overall_score"]  # 0-100
    score_max = 100
    insight = result["insight"]
    suggestions = result["suggestions"]
    reference_response = result["reference_response"]
    selected_layers = result["selected_layers"]
    used_context = result["used_context"]

    await _store_evaluation_artifacts(
        payload,
        used_context,
        reference_response,
        score_breakdown,
        insight,
    )

    latency_ms = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)
    return EvaluateModelResponseResponse(
        ok=True,
        score_breakdown=score_breakdown,
        quality_score=quality_score,
        score_max=score_max,
        insight=insight,
        suggestions=suggestions,
        evaluation_provider=f"{payload.provider_config.provider}:{payload.provider_config.model}",
        reference_response=reference_response,
        selected_layers=selected_layers,
        used_context=used_context,
        latency_ms=latency_ms,
    )
