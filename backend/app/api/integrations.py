from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any, Literal
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/integrations", tags=["integrations"])

RequestMethod = Literal["GET", "POST"]


class ConnectorRequest(BaseModel):
    endpoint: str
    method: RequestMethod = "POST"
    prompt_param: str = "prompt"
    headers: str = ""
    body_template: str = ""
    response_path: str = ""
    content_template: str = "{{text}}"
    fallback_content: str = ""
    curl_command: str = ""


class ConnectorExecuteRequest(BaseModel):
    prompt: str = ""
    connector: ConnectorRequest
    timeout_ms: int = Field(default=20_000, ge=500, le=120_000)


class ConnectorExecuteResponse(BaseModel):
    ok: bool
    status_code: int
    request_url: str
    request_method: str
    extracted_text: str
    raw_preview: str


class DatabaseConfigureRequest(BaseModel):
    connection_string: str = ""
    database_port: str = "5432"
    database_superuser: str = "postgres"
    password: str = ""
    db_name: str = ""
    db_already_exists: bool = True


class DatabaseConfigureResponse(BaseModel):
    ok: bool
    normalized_connection_string: str
    message: str


def _render_template(template: str, variables: dict[str, str]) -> str:
    result = template
    for key, value in variables.items():
        result = result.replace(f"{{{{{key}}}}}", value)
    return result


def _parse_headers(raw: str) -> dict[str, str]:
    text = raw.strip()
    if not text:
        return {}

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid headers JSON: {exc.msg}") from exc

    if not isinstance(parsed, dict):
        raise HTTPException(status_code=400, detail="Headers JSON must be an object.")

    return {str(key): str(value) for key, value in parsed.items()}


def _resolve_path(source: Any, raw_path: str) -> Any:
    path = raw_path.strip()
    if not path:
        return source

    segments = [segment for segment in path.replace("[", ".").replace("]", "").split(".") if segment]
    current = source
    for segment in segments:
        if current is None:
            return None
        if isinstance(current, list):
            try:
                current = current[int(segment)]
            except (ValueError, IndexError):
                return None
            continue
        if isinstance(current, dict):
            current = current.get(segment)
            continue
        return None
    return current


def _stringify_payload(payload: Any) -> str:
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, list) and all(isinstance(item, (str, int, float)) for item in payload):
        return "\n".join(str(item) for item in payload).strip()
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _normalize_url(endpoint: str, prompt_param: str, prompt: str) -> str:
    separator = "&" if "?" in endpoint else "?"
    if not prompt_param:
        return endpoint
    return f"{endpoint}{separator}{quote(prompt_param)}={quote(prompt)}"


async def execute_connector_request(payload: ConnectorExecuteRequest) -> ConnectorExecuteResponse:
    connector = payload.connector
    endpoint = connector.endpoint.strip()
    if not endpoint:
        raise HTTPException(status_code=400, detail="Connector endpoint is required.")

    variables = {
        "prompt": payload.prompt,
        "promptEncoded": quote(payload.prompt),
    }
    request_url = _render_template(endpoint, variables)
    method = connector.method
    headers = _parse_headers(connector.headers)
    request_kwargs: dict[str, Any] = {
        "method": method,
        "url": request_url,
        "headers": headers,
    }

    if method == "GET":
        if connector.prompt_param.strip() and "{{prompt" not in endpoint:
            request_kwargs["url"] = _normalize_url(request_url, connector.prompt_param.strip(), payload.prompt)
    else:
        body_template = connector.body_template.strip()
        request_body = (
            _render_template(body_template, variables)
            if body_template
            else json.dumps({connector.prompt_param.strip() or "prompt": payload.prompt})
        )
        if not any(key.lower() == "content-type" for key in headers):
            headers["Content-Type"] = "application/json"
        request_kwargs["content"] = request_body

    try:
        async with httpx.AsyncClient(timeout=payload.timeout_ms / 1000) as client:
            response = await client.request(**request_kwargs)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:600] if exc.response.text else exc.response.reason_phrase
        raise HTTPException(status_code=400, detail=f"HTTP request failed: {detail}") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=400, detail=f"HTTP request failed: {exc}") from exc

    raw_text = response.text
    parsed: Any = raw_text
    try:
        parsed = response.json()
    except ValueError:
        pass

    extracted = _resolve_path(parsed, connector.response_path)
    selected = parsed if extracted is None else extracted
    text = _stringify_payload(selected)
    json_value = json.dumps(selected, indent=2, ensure_ascii=False) if not isinstance(selected, str) else json.dumps(selected)
    formatted = (
        _render_template(connector.content_template.strip(), {**variables, "text": text, "json": json_value}).strip()
        if connector.content_template.strip()
        else text
    )

    return ConnectorExecuteResponse(
        ok=True,
        status_code=response.status_code,
        request_url=str(request_kwargs["url"]),
        request_method=method,
        extracted_text=formatted or connector.fallback_content.strip(),
        raw_preview=raw_text[:4000],
    )


@router.post("/http/execute", response_model=ConnectorExecuteResponse)
async def execute_connector(payload: ConnectorExecuteRequest) -> ConnectorExecuteResponse:
    return await execute_connector_request(payload)


def _parse_db_request(payload: DatabaseConfigureRequest) -> tuple[str, str, str, str, str]:
    raw_connection = payload.connection_string.strip()
    if raw_connection:
        connection_value = raw_connection.split("=", 1)[1].strip() if raw_connection.upper().startswith("DATABASE_URL=") else raw_connection
        parsed = urlparse(connection_value)
        if parsed.scheme not in {"postgresql", "postgres"}:
            raise HTTPException(status_code=400, detail="Only PostgreSQL connection strings are supported.")
        host = parsed.hostname or "localhost"
        port = str(parsed.port or 5432)
        user = unquote(parsed.username or payload.database_superuser or "postgres")
        password = unquote(parsed.password or payload.password)
        db_name = unquote((parsed.path or "").lstrip("/") or payload.db_name)
    else:
        host = "localhost"
        port = payload.database_port.strip() or "5432"
        user = payload.database_superuser.strip() or "postgres"
        password = payload.password
        db_name = payload.db_name.strip()

    if not db_name:
        raise HTTPException(status_code=400, detail="Database name is required.")

    return host, port, user, password, db_name


def _find_postgres_cli(tool: str) -> str:
    resolved = shutil.which(tool)
    if resolved:
        return resolved

    if os.name == "nt":
        roots = [
            Path("C:/Program Files/PostgreSQL"),
            Path("C:/Program Files (x86)/PostgreSQL"),
        ]
        for root in roots:
            if not root.exists():
                continue
            for candidate in sorted(root.glob(f"*/bin/{tool}.exe"), reverse=True):
                if candidate.exists():
                    return str(candidate)

    raise HTTPException(status_code=400, detail=f"Required PostgreSQL CLI tool '{tool}' was not found on this machine.")


def _run_cli(tool: str, args: list[str], password: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password
    command = [_find_postgres_cli(tool), *args]
    return subprocess.run(command, capture_output=True, text=True, env=env, check=False)


@router.post("/db/configure", response_model=DatabaseConfigureResponse)
def configure_database(payload: DatabaseConfigureRequest) -> DatabaseConfigureResponse:
    host, port, user, password, db_name = _parse_db_request(payload)
    auth = quote(user)
    if password:
        auth = f"{auth}:{quote(password)}"
    normalized = f"postgresql://{auth}@{host}:{port}/{db_name}"
    escaped_db_name = db_name.replace("'", "''")

    if not payload.db_already_exists:
        check_existing = _run_cli(
            "psql",
            ["-h", host, "-p", port, "-U", user, "-d", "postgres", "-tAc", f"SELECT 1 FROM pg_database WHERE datname = '{escaped_db_name}'"],
            password,
        )
        if check_existing.returncode != 0:
            detail = (check_existing.stderr or check_existing.stdout).strip()
            raise HTTPException(status_code=400, detail=f"Failed to inspect databases: {detail}")

        if check_existing.stdout.strip() != "1":
            create_result = _run_cli("createdb", ["-h", host, "-p", port, "-U", user, db_name], password)
            if create_result.returncode != 0:
                detail = (create_result.stderr or create_result.stdout).strip()
                raise HTTPException(status_code=400, detail=f"Database creation failed: {detail}")

    test_result = _run_cli("psql", ["-h", host, "-p", port, "-U", user, "-d", db_name, "-tAc", "SELECT current_database();"], password)
    if test_result.returncode != 0:
        detail = (test_result.stderr or test_result.stdout).strip()
        raise HTTPException(status_code=400, detail=f"Database connection failed: {detail}")

    action = "Connected to existing database" if payload.db_already_exists else "Created and connected to database"
    return DatabaseConfigureResponse(
        ok=True,
        normalized_connection_string=normalized,
        message=f"{action} '{db_name}' successfully.",
    )
