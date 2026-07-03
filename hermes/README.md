# Hermes Task Dispatcher

Hermes prioritizes and routes tasks stored in a Notion database using a
cheapest-first strategy, at three tiers of automation.

## Schema

Hermes runs against a Notion database with these properties (this matches
the live **🧠 Hermes Tasks** database — Tier 2/3 code assumes exactly this
schema, not the capitalized `Pending`/`Pipeline`/`Cost` names from an earlier
draft of this doc):

- `Task Name` — Title
- `Status` — Select: `pending`, `running`, `completed`, `failed`
- `Type` — Select: `automation`, `research`, `report`, `content`
- `Input Data` — Text
- `Output` — Text
- `Created At` — Date

There is **no `Cost` property in Notion.** The live database has no formula
to sort by cost, so cheapest-first priority (`automation`=1, `research`=3,
`report`=5, `content`=7, anything else=10) is computed in Python — see
`TYPE_COST` in `notion_client.py` — and applied client-side after fetching
pending tasks. Tier 2 and Tier 3 both do this. Keep that mapping in sync
with the `Type` options if they ever change.

## Tier 1 — Manual (Notion only, no code)

Because the cost mapping only exists in Python, a pure-Notion button can't
replicate cheapest-first ordering — it can only sort by a real property. Set
up Tier 1 as FIFO (oldest pending task first) instead:

1. Add a **Button** property named `▶️ Start Next Task`:
   - Find pages: `Status is pending`, sorted by `Created At` ascending, limit 1
   - Edit pages: set `Status` to `running`
2. Add an automation **Auto-Complete Automation Tasks**:
   - Trigger: `Status is set to running` and `Type is automation`
   - Action: set `Status` to `completed`
3. Add views: `📋 Pending Queue` (filter `pending`, sort `Created At` asc),
   `⚡ Running Tasks` (filter `running`), `✅ Done This Week` (filter
   `completed` + `Created At` within this week), `📊 Pipeline Board` (board
   grouped by `Status`).

Tier 1 is FIFO-only; only Tier 2/3 apply cheapest-first priority.

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
