"""Production entrypoint for Tier 3: gunicorn -w 1 -b 0.0.0.0:5000 wsgi:app

dispatcher_tier3.py's own `python3 dispatcher_tier3.py` runs Flask's
development server, which isn't meant for a long-running public webhook
deployment. This module does the same configure() step (env validation,
starting the background poll/dispatch worker) but exposes the resulting
`app` for a real WSGI server to serve instead.

Run exactly one worker (`-w 1`), never more, and never a multi-process
deployment: Tier 3 keeps per-process state (dispatch_lock, dispatch_requested,
the background worker thread, the one-time verification-token bootstrap) that
isn't shared or coordinated across processes - see dispatcher_tier3.py's own
module docstring and the dispatch_lock comment for why only one dispatcher
process should ever run per Notion database.

WEBHOOK_PORT in .env is ignored here - bind the port with gunicorn's own -b
flag instead.
"""

from dispatcher_tier3 import app, configure

configure()

__all__ = ["app"]
