# Hermes Task Dispatcher

Hermes prioritizes and routes tasks stored in a Notion database using a
cheapest-first strategy, at three tiers of automation.

## Tier 1 — Manual (Notion only, no code)

1. Create a Notion database named **Hermes Task Manager** with these properties:
   - `Task Name` — Title (rename the default Name column)
   - `Status` — Select: `Pending`, `Running`, `Completed`
   - `Pipeline` — Select: `Automation`, `Research`, `Report`, `Content`
   - `Cost` — Formula:
     ```
     if(prop("Pipeline") == "Automation", 1,
     if(prop("Pipeline") == "Research", 3,
     if(prop("Pipeline") == "Report", 5,
     if(prop("Pipeline") == "Content", 7, 10))))
     ```
   - `Notes` — Text
   - `Created Time` — Created time
   - `Created By` — Created by
2. Add a **Button** property named `▶️ Start Next Task`:
   - Find pages: `Status is Pending`, sorted by `Cost` ascending, limit 1
   - Edit pages: set `Status` to `Running`
3. Add an automation **Auto-Complete Automation Tasks**:
   - Trigger: `Status is set to Running` and `Pipeline is Automation`
   - Action: set `Status` to `Completed`
4. Add views: `📋 Pending Queue` (filter Pending, sort Cost asc), `⚡ Running
   Tasks` (filter Running), `✅ Done This Week` (filter Completed + Created
   Time within this week), `📊 Pipeline Board` (board grouped by Status).

See `docs/index.html` for the fully illustrated setup guide and
`ONBOARDING.md` for the team-facing one-pager.

## Tier 2 — Scheduled dispatcher (Python, polling)

Automates the Tier 1 button click on a 5-minute interval.

```bash
cd hermes
pip install -r requirements.txt
cp .env.example .env   # fill in NOTION_TOKEN and DATABASE_ID
python3 dispatcher_tier2.py
```

Getting `NOTION_TOKEN` and `DATABASE_ID`:
1. Create an integration at https://www.notion.so/my-integrations and copy
   its token.
2. Share the Hermes database with that integration (••• → Add connections).
3. Copy the 32-character database ID out of the database URL.

## Tier 3 — Real-time dispatcher (Python, webhook + polling)

Adds a webhook endpoint for instant pickup and a parallel-task cap, on top
of a 30-second background poll as a fallback.

```bash
cd hermes
pip install -r requirements.txt
cp .env.example .env   # also set WEBHOOK_PORT and MAX_PARALLEL_TASKS
python3 dispatcher_tier3.py
```

Endpoints:
- `POST /webhook` — trigger an immediate dispatch pass. Accepts either:
  - a generic caller sending the `X-Webhook-Secret` header (set `WEBHOOK_SECRET`), or
  - a real Notion webhook subscription: Notion's one-time `verification_token`
    handshake is accepted automatically, and subsequent events are verified
    via the `X-Notion-Signature` HMAC header against `NOTION_WEBHOOK_SECRET`
    (see [Notion's webhook docs](https://developers.notion.com/reference/webhooks))
- `GET /status` — health check (running task count, max parallel, timestamp)

## Running tests

```bash
cd hermes
pip install -r requirements-dev.txt
python3 -m pytest tests/
```

## Files

| File | Purpose |
|------|---------|
| `notion_client.py` | Shared Notion API wrapper used by both dispatchers |
| `dispatcher_tier2.py` | Tier 2 scheduled dispatcher |
| `dispatcher_tier3.py` | Tier 3 real-time dispatcher with webhook + parallelism |
| `docs/index.html` | Illustrated documentation site (overview, setup, API reference, troubleshooting) |
| `docs/dashboard.html` | Sample metrics dashboard template |
| `ONBOARDING.md` | Team-facing one-pager for creating and tracking tasks |
| `requirements.txt` / `requirements-dev.txt` | Runtime deps / adds pytest for `tests/` |
| `tests/` | Unit tests (mocked Notion API, no live database needed) |
