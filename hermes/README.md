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
- `Created At` — **Created time** (Notion's automatic property, not a plain
  `Date` field — it must self-populate on row creation, or FIFO ordering
  silently breaks for any task where a human forgot to set it)
- `Completed At` — Date, set to "now" when `Status` becomes `completed`
  (see the Tier 1 automation below; needed for the "Done This Week" view)

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
3. Add a second automation **Stamp Completion Time** (covers every `Type`,
   not just `automation` — tasks finished by a human or an external worker
   need `Completed At` set too, or they're invisible to the view below):
   - Trigger: `Status is set to completed`
   - Action: set `Completed At` to "now"
4. Add views: `📋 Pending Queue` (filter `pending`, sort `Created At` asc),
   `⚡ Running Tasks` (filter `running`), `✅ Done This Week` (filter
   `completed` + `Completed At` within this week — not `Created At`, which
   would miss anything completed later than it was created), `📊 Pipeline
   Board` (board grouped by `Status`).

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
cp .env.example .env   # set WEBHOOK_PORT, MAX_PARALLEL_TASKS, and one of the webhook secrets below
python3 dispatcher_tier3.py
```

`python3 dispatcher_tier3.py` runs Flask's own development server — fine
locally, not for a real deployment (no production hardening, single
connection at a time by default). For anything actually exposed to Notion's
webhooks, run it through a production WSGI server instead:

```bash
pip install gunicorn
gunicorn -w 1 -b 0.0.0.0:5000 wsgi:app
```

Use exactly one worker (`-w 1`) and never scale this to multiple processes —
see the comment on `dispatch_lock` in `dispatcher_tier3.py` for why. `wsgi.py`
runs the same startup validation `main()` does; `WEBHOOK_PORT` only matters
for the `python3 dispatcher_tier3.py` path, since gunicorn's `-b` sets the
port here instead.

`WEBHOOK_SECRET` or `NOTION_WEBHOOK_SECRET` is required — the process refuses
to start without one of them (or with `WEBHOOK_SECRET` left as the
`.env.example` placeholder), since an unauthenticated `/webhook` lets anyone
who can reach it trigger dispatches. The one exception is a fresh Notion-only
install, where `NOTION_WEBHOOK_SECRET` can't be known until the handshake
below arrives: set `WEBHOOK_SETUP_MODE=1` instead to start without either
secret — every endpoint except the verification handshake itself still
requires a real secret, there just isn't one yet. `MAX_PARALLEL_TASKS` must
be between 1 and 100.

Endpoints:
- `POST /webhook` — trigger an immediate dispatch pass. Accepts either:
  - a generic caller sending the `X-Webhook-Secret` header (set `WEBHOOK_SECRET`), or
  - a real Notion webhook subscription: Notion's one-time `verification_token`
    handshake, verified via the `X-Notion-Signature` HMAC header against
    `NOTION_WEBHOOK_SECRET` for every event after that
    (see [Notion's webhook docs](https://developers.notion.com/reference/webhooks))
- `GET /status` — health check (requires no auth, so it never calls Notion
  itself — `running_tasks` reflects the last dispatch pass, at most
  `POLL_INTERVAL_SECONDS` stale)

**Registering a real Notion webhook subscription:** the handshake carries no
signature, so it's only accepted while `WEBHOOK_SETUP_MODE=1`. To register:
1. Set `WEBHOOK_SETUP_MODE=1` and start the dispatcher.
2. Create the webhook subscription in Notion's integration settings, pointed
   at this server's `/webhook`.
3. Read the token Notion sent from `hermes/.notion_verification_token`
   (written with `0600` permissions — never logged), and set it as
   `NOTION_WEBHOOK_SECRET`.
4. Delete that file, unset `WEBHOOK_SETUP_MODE`, and restart.

**Run only one dispatcher process per database.** The parallel-task cap and
the pending→running transition are only serialized within a single process.
Running Tier 2 and Tier 3 at once, or more than one instance of either,
against the same database can let two dispatchers both claim the same
pending task or jointly exceed `MAX_PARALLEL_TASKS`.

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
| `wsgi.py` | Production entrypoint for Tier 3 (`gunicorn -w 1 wsgi:app`) |
| `docs/index.html` | Illustrated documentation site (overview, setup, API reference, troubleshooting) |
| `docs/dashboard.html` | Sample metrics dashboard template |
| `ONBOARDING.md` | Team-facing one-pager for creating and tracking tasks |
| `requirements.txt` / `requirements-dev.txt` | Runtime deps / adds pytest for `tests/` |
| `tests/` | Unit tests (mocked Notion API, no live database needed) |
