# Master Developer Prompt Kit
### Whisper Flow · buildagentic · McDis Framework

One prompt. One Claude call. Full engineering package from any transcript.

---

## Files

| File | Purpose |
|------|---------|
| `master_dev_prompt.txt` | The system prompt — defines schema + Claude's role |
| `run_master_dev.sh` | Shell script to pipe any transcript through Claude Code or Codex (supports `--mock` or `MOCK_OUTPUT=1` to emit `outputs/sample.json` when a model CLI is unavailable) |
| `validate_output.py` | JSON validator for structure + enum checks |
| `batch_run_master_dev.sh` | Batch processor for all `transcripts/*.txt` files |
| `Makefile` | Local/CI shortcuts (`validate-file`, `validate-outputs`, `ci`) |
| `.github/workflows/validate-master-dev-prompt.yml` | GitHub Actions validation workflow |
| `sample_transcript.txt` | Test transcript (Dear Saigon SMS ordering system) |
| `app.py` | FastAPI HTTP server — `POST /process` calls Claude directly via SDK, `GET /` serves the web UI |
| `static/index.html` | Terminal-style web UI — paste a transcript, get rendered artifacts |

---

## Usage

### 1. Make the script executable (first time only)
```bash
chmod +x run_master_dev.sh
```

### 2. Run with your transcript
```bash
./run_master_dev.sh your_transcript.txt
```

### 3. Save output as JSON
```bash
./run_master_dev.sh your_transcript.txt > output.json
```

### 4. Test with the sample
```bash
./run_master_dev.sh sample_transcript.txt
```

The script auto-detects:
- `claude` CLI first
- falls back to `codex exec` if `claude` is not installed

Optional reliability env vars:
- `MAX_RETRIES` (default `3`)
- `RETRY_DELAY_SECONDS` (default `2`)
- `MASTER_DEV_TIMEOUT_SECONDS` (default `0`, disabled)

Example:
```bash
MAX_RETRIES=5 RETRY_DELAY_SECONDS=3 MASTER_DEV_TIMEOUT_SECONDS=90 \
./run_master_dev.sh sample_transcript.txt > output.json
```

### 5. Validate output JSON
```bash
python3 validate_output.py output.json
```

Validation is strict:
- required object keys must match exactly
- `actions.items`, `implementation_plan.milestones`, `implementation_plan.tech_tasks`, `code_suggestions.snippets`, `agent_task_report.qualification_checks`, `agent_task_report.task_slides`, `agent_task_report.master_checklist`, `agent_task_report.review_checkpoints`, and `agent_task_report.escalation_rules` must each contain at least one item
- enum fields must use the exact allowed values

Or with Make:
```bash
make validate-file FILE=output.json
```

### 6. Batch run all transcripts
Put `.txt` transcripts in `transcripts/`, then run:
```bash
chmod +x batch_run_master_dev.sh
./batch_run_master_dev.sh
```

Custom folders:
```bash
./batch_run_master_dev.sh ./my_transcripts ./my_outputs
```

Validate all generated outputs:
```bash
make validate-outputs
```

Batch behavior:
- successful runs write `outputs/<name>.json`
- schema failures write `outputs/<name>.invalid.json`
- run logs go to `outputs/<name>.log`
- `make validate-outputs` validates only `*.json` and ignores `*.invalid.json`

### 7. CI checks
Local CI-equivalent check:
```bash
make ci
```

GitHub Actions runs the same checks on push and pull request.

---

## Manual (no script)

```bash
{
  cat master_dev_prompt.txt
  cat your_transcript.txt
  echo ""
  echo '"""'
} | claude
```

Codex alternative:

```bash
{
  cat master_dev_prompt.txt
  cat your_transcript.txt
  echo ""
  echo '"""'
} | codex exec --skip-git-repo-check -
```

---

## Output Modes

| Mode | What you get |
|------|-------------|
| `design_doc` | context, requirements, architecture, alternatives, decisions, open questions |
| `pm_summary` | plain-language overview, scope, timeline implications |
| `actions` | tasks with owner, priority (low/medium/high), type |
| `implementation_plan` | milestones with ETA + risks, tech tasks with complexity (S/M/L) |
| `code_suggestions` | real runnable snippets in detected language, stack context |
| `agent_task_report` | urgent assignment/reporting workflow, qualification checks, one-task-per-slide entries, master checklist, review checkpoints, escalation rules |

---

## FastAPI Server

Run the included server for HTTP access and a browser UI:

```bash
export ANTHROPIC_API_KEY=sk-...
pip install fastapi uvicorn anthropic python-dotenv
uvicorn app:app --reload
```

- `GET /` — opens the web UI (paste transcript, get rendered artifacts)
- `POST /process` — returns structured JSON from any transcript
- `GET /health` — liveness check

Optional: set `SERVER_API_KEY` to require an `X-Api-Key` header on all requests.

### Minimal SDK snippet

```python
import anthropic, json

client = anthropic.Anthropic(api_key=YOUR_KEY)

with open("master_dev_prompt.txt") as f:
    system_prompt = f.read()

def run_master_dev(transcript: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8096,
        system=system_prompt,
        messages=[{"role": "user", "content": f'{transcript}\n"""'}]
    )
    return json.loads(response.content[0].text)
```

---

## Autopilot Watcher

Run the watcher to automatically process any transcript dropped into `transcripts/`:

```bash
python3 watcher.py
```

Then drop any `.txt` file into `transcripts/` — the JSON output appears in `outputs/` automatically.

Custom directories:

```bash
python3 watcher.py --transcripts ./my-transcripts --outputs ./my-outputs
```

Stop with `Ctrl+C`. Files already processed (with a matching `.json` in `outputs/`) are skipped automatically.

### Obsidian workflow

Keep the Obsidian vault separate from this repository and use two vault folders:

```text
<vault>/Meeting Transcripts/   # drop .txt transcripts here
<vault>/Meeting Outputs/       # generated .json and .log files appear here
```

Start the watcher with the absolute paths for your vault:

```bash
python3 watcher.py \
  --transcripts "/path/to/vault/Meeting Transcripts" \
  --outputs "/path/to/vault/Meeting Outputs"
```

The watcher observes only the transcript folder, processes `.txt` files once, and leaves non-text Obsidian notes untouched. The folder names and vault location are configurable; no Obsidian path is hard-coded into the project.
