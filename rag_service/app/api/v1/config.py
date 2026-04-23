from __future__ import annotations

from urllib.parse import quote, unquote, urlparse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.session import configure_database_url

router = APIRouter()


class DatabaseConfigRequest(BaseModel):
    connection_string: str = ""
    database_port: str = "5432"
    database_superuser: str = "postgres"
    password: str = ""
    db_name: str = ""


class DatabaseConfigResponse(BaseModel):
    ok: bool
    normalized_connection_string: str
    message: str


def _normalize_database_url(payload: DatabaseConfigRequest) -> str:
    raw_connection = payload.connection_string.strip()
    if raw_connection:
        value = raw_connection.split("=", 1)[1].strip() if raw_connection.upper().startswith("DATABASE_URL=") else raw_connection
        parsed = urlparse(value)
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

    auth = quote(user)
    if password:
        auth = f"{auth}:{quote(password)}"
    return f"postgresql://{auth}@{host}:{port}/{quote(db_name)}"


@router.post("/config/db", response_model=DatabaseConfigResponse)
async def configure_database(payload: DatabaseConfigRequest) -> DatabaseConfigResponse:
    database_url = _normalize_database_url(payload)
    try:
        # Import models before create_all so SQLAlchemy metadata is fully populated.
        import app.db.models  # noqa: F401

        await configure_database_url(database_url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Database configuration failed: {exc}") from exc

    return DatabaseConfigResponse(
        ok=True,
        normalized_connection_string=database_url,
        message="myRAG is connected to PostgreSQL and pgvector is enabled.",
    )
