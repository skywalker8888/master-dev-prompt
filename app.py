# Master Developer Prompt — FastAPI Server
# Dependencies: pip install fastapi uvicorn anthropic python-dotenv
#
# Usage:
#   export ANTHROPIC_API_KEY=sk-...
#   uvicorn app:app --reload
#
# Then POST to http://localhost:8000/process with JSON body:
#   { "transcript": "your meeting transcript here" }

import hmac
import json
import os
from pathlib import Path
from typing import Annotated

import anthropic
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from transcript_sanitizer import sanitize_transcript

load_dotenv()

app = FastAPI(title="Master Dev Prompt API")


def verify_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    server_key = os.getenv("SERVER_API_KEY")
    if not server_key:
        return  # no key configured → open (local dev)
    if not x_api_key or not hmac.compare_digest(x_api_key, server_key):
        raise HTTPException(status_code=401, detail="Unauthorized")

_PROMPT_PATH = Path(__file__).parent / "master_dev_prompt.txt"
_system_prompt: str | None = None


def _get_system_prompt() -> str:
    global _system_prompt
    if _system_prompt is None:
        if not _PROMPT_PATH.exists():
            raise RuntimeError("master_dev_prompt.txt not found")
        _system_prompt = _PROMPT_PATH.read_text()
    return _system_prompt


class ProcessRequest(BaseModel):
    transcript: str


class ProcessResponse(BaseModel):
    result: dict


@app.post("/process", response_model=ProcessResponse)
def process_transcript(
    req: ProcessRequest,
    _: Annotated[None, Depends(verify_api_key)],
) -> ProcessResponse:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)
    system = _get_system_prompt()
    sanitized_transcript = sanitize_transcript(req.transcript)
    user_message = f'{sanitized_transcript}\n"""'

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8096,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = message.content[0].text
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Model returned invalid JSON: {e}. Raw: {raw[:200]}",
        )

    return ProcessResponse(result=result)


@app.post("/process/stream")
def process_transcript_stream(
    req: ProcessRequest,
    _: Annotated[None, Depends(verify_api_key)],
) -> StreamingResponse:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)
    system = _get_system_prompt()
    sanitized_transcript = sanitize_transcript(req.transcript)
    user_message = f'{sanitized_transcript}\n"""'

    def generate():
        accumulated = ""
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=8096,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            for chunk in stream.text_stream:
                accumulated += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        try:
            result = json.loads(accumulated)
            yield f"data: {json.dumps({'done': True, 'result': result})}\n\n"
        except json.JSONDecodeError as e:
            yield f"data: {json.dumps({'error': str(e), 'raw': accumulated[:300]})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/", response_class=HTMLResponse)
def ui() -> HTMLResponse:
    html = Path(__file__).parent / "static" / "index.html"
    return HTMLResponse(html.read_text() if html.exists() else "<h1>UI not found</h1>", status_code=200 if html.exists() else 404)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "prompt_loaded": _PROMPT_PATH.exists()}
