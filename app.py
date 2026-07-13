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
from datetime import date

import anthropic
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

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
    founder_daily_brief: dict


def _split_lines(text: str | None) -> list[str]:
    if not text:
        return []
    return [line.strip(" -•\t") for line in text.splitlines() if line.strip()]


def _derive_health(result: dict) -> str:
    actions = result.get("actions", {}).get("items", []) or []
    high = sum(1 for item in actions if item.get("priority") == "high")
    medium = sum(1 for item in actions if item.get("priority") == "medium")
    if high > 0:
        return "🔴"
    if medium > 2:
        return "🟡"
    return "🟢"


def build_founder_daily_brief(result: dict) -> dict:
    design_doc = result.get("design_doc", {}) or {}
    actions = result.get("actions", {}).get("items", []) or []
    impl = result.get("implementation_plan", {}) or {}
    report = result.get("agent_task_report", {}) or {}

    open_questions = _split_lines(design_doc.get("open_questions_risks"))
    decisions = [line for line in open_questions if any(w in line.lower() for w in ("decide", "approval", "founder"))][:3]
    if len(decisions) < 3:
        needed = 3 - len(decisions)
        decisions.extend([item.get("description", "") for item in actions if item.get("priority") == "high"][:needed])

    blockers = []
    for milestone in impl.get("milestones", []) or []:
        risk = (milestone.get("risks") or "").strip()
        if risk:
            blockers.append({
                "project": milestone.get("name", "Unspecified"),
                "owner": "Unassigned",
                "waiting_on": risk,
            })
    blockers = blockers[:3]

    completed = []
    for item in report.get("master_checklist", []) or []:
        if item.get("checked"):
            completed.append(item.get("task_title", "Completed item"))
    completed = completed[:5]

    status_counts = {"Running": 0, "Waiting": 0, "Blocked": 0, "Paused": 0, "Needs Review": 0}
    for slide in report.get("task_slides", []) or []:
        status = (slide.get("status") or "").strip().lower()
        if status in {"in progress", "running"}:
            status_counts["Running"] += 1
        elif status in {"waiting", "pending"}:
            status_counts["Waiting"] += 1
        elif status in {"blocked"}:
            status_counts["Blocked"] += 1
        elif status in {"paused"}:
            status_counts["Paused"] += 1
        elif status in {"review", "needs review"}:
            status_counts["Needs Review"] += 1

    risk_blob = " ".join([
        design_doc.get("open_questions_risks", "") or "",
        " ".join((m.get("risks", "") or "") for m in (impl.get("milestones", []) or [])),
    ]).lower()
    alerts = {
        "security": "yes" if "security" in risk_blob else "clear",
        "budget": "yes" if any(token in risk_blob for token in ("budget", "cost", "pricing")) else "clear",
        "deadlines": "yes" if any(token in risk_blob for token in ("delay", "deadline", "eta")) else "clear",
        "failures": "yes" if any(token in risk_blob for token in ("failure", "failed", "error")) else "clear",
    }

    top_priorities = [item.get("description", "") for item in actions if item.get("priority") == "high"][:3]
    if len(top_priorities) < 3:
        needed = 3 - len(top_priorities)
        top_priorities.extend([item.get("description", "") for item in actions if item.get("priority") == "medium"][:needed])

    next_action = "Review top high-priority action and approve immediate owner assignments."
    if decisions:
        next_action = f"Approve: {decisions[0]}"
    elif blockers:
        next_action = f"Unblock: {blockers[0]['project']} — {blockers[0]['waiting_on']}"

    return {
        "date": str(date.today()),
        "today_focus": design_doc.get("decisions") or design_doc.get("requirements_constraints") or "Execution priorities and decision velocity.",
        "decisions_requiring_approval": [item for item in decisions if item],
        "current_blockers": blockers,
        "completed_since_last_brief": [item for item in completed if item],
        "project_health": [
            {"project": "Dear Saigon", "status": _derive_health(result)},
            {"project": "CoachAI", "status": "🟡"},
            {"project": "ZOS Command Center", "status": "🟢"},
            {"project": "Marketing", "status": "🟡"},
        ],
        "agent_status": status_counts,
        "alerts": alerts,
        "today_top_3": [item for item in top_priorities if item],
        "next_founder_action": next_action,
    }


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
    user_message = f'{req.transcript}\n"""'

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

    founder_daily_brief = build_founder_daily_brief(result)
    return ProcessResponse(result=result, founder_daily_brief=founder_daily_brief)


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
    user_message = f'{req.transcript}\n"""'

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
            founder_daily_brief = build_founder_daily_brief(result)
            yield f"data: {json.dumps({'done': True, 'result': result, 'founder_daily_brief': founder_daily_brief})}\n\n"
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
