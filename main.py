import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from openai import OpenAI
from pydantic import BaseModel, model_validator

load_dotenv()

# Microsoft Foundry OpenAI-compatible API: SDK calls /chat/completions etc. under this base.
DEFAULT_ENDPOINT = "https://knurdzorg-test-resource.services.ai.azure.com/openai/v1"
DEFAULT_DEPLOYMENT = "Kimi-K2.6"

_static_dir = Path(__file__).resolve().parent / "static"


def _normalize_openai_base_url(url: str) -> str:
    """Ensure Foundry URLs use .../openai/v1 when only the hostname was configured."""
    u = url.rstrip("/")
    if u.endswith("/openai/v1"):
        return u
    parsed = urlparse(u)
    if not parsed.scheme or not parsed.netloc:
        return u
    if parsed.netloc.endswith("services.ai.azure.com"):
        path = (parsed.path or "").rstrip("/")
        if path == "" or path == "/":
            return f"{parsed.scheme}://{parsed.netloc}/openai/v1"
    return u


def _get_settings() -> tuple[str, str, str]:
    endpoint = _normalize_openai_base_url(
        os.environ.get("AZURE_AI_ENDPOINT", DEFAULT_ENDPOINT).rstrip("/")
    )
    deployment = os.environ.get("AZURE_AI_DEPLOYMENT", DEFAULT_DEPLOYMENT)
    api_key = os.environ.get("AZURE_AI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Set AZURE_AI_API_KEY (or OPENAI_API_KEY) in your environment or .env file.",
        )
    return endpoint, deployment, api_key


def _client() -> tuple[OpenAI, str]:
    endpoint, deployment, api_key = _get_settings()
    return OpenAI(base_url=endpoint, api_key=api_key), deployment


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    mode: Literal["completion", "response"] = "completion"
    messages: list[ChatMessage] | None = None
    input: str | None = None
    previous_response_id: str | None = None

    @model_validator(mode="after")
    def validate_mode_payload(self) -> "ChatRequest":
        if self.mode == "completion":
            if not self.messages:
                raise ValueError("completion mode requires non-empty messages")
        else:
            if not (self.input is not None and self.input.strip()):
                raise ValueError("response mode requires non-empty input")
        return self


class ChatResponse(BaseModel):
    role: str
    content: str | None
    response_id: str | None = None


app = FastAPI(title="Foundry Chat")


@app.post("/api/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    client, deployment_name = _client()

    if body.mode == "completion":
        assert body.messages is not None
        try:
            completion = client.chat.completions.create(
                model=deployment_name,
                messages=[m.model_dump() for m in body.messages],
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=str(e)) from e

        msg = completion.choices[0].message
        return ChatResponse(role=msg.role, content=msg.content, response_id=None)

    try:
        kwargs: dict[str, object] = {
            "model": deployment_name,
            "input": body.input.strip() if body.input else "",
        }
        if body.previous_response_id:
            kwargs["previous_response_id"] = body.previous_response_id

        response = client.responses.create(**kwargs)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    if response.error is not None:
        detail = getattr(response.error, "message", None) or str(response.error)
        raise HTTPException(status_code=502, detail=detail)

    text = response.output_text.strip() if response.output_text else None
    return ChatResponse(
        role="assistant",
        content=text if text else None,
        response_id=response.id,
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_static_dir / "index.html")


