# Welcome to Hermes

Hermes is our task management system: it automatically prioritizes work so
you can focus on doing, not managing.

## Creating a task (30 seconds)

1. Open the Hermes database.
2. Click **+ New**.
3. Fill in:
   - **Task Name** — what needs to be done
   - **Type** — `automation`, `research`, `report`, or `content`
   - **Status** — leave as `pending`
   - **Input Data** — optional context for whoever/whatever picks it up
4. Press Enter.

## How tasks get processed

The Tier 2/3 dispatchers always pick the cheapest (lowest-effort) pending
task first — there's no `Cost` property in Notion, priority is computed from
`Type` in code. The manual Tier 1 button doesn't have that logic, so it just
takes the oldest pending task instead (FIFO). Tasks move through
**pending → running → completed** (or **failed** if something goes wrong).

| Type | Cost | Use for |
|------|------|---------|
| automation | 1 | Quick, repetitive tasks (data entry, simple updates) |
| research | 3 | Information gathering |
| report | 5 | Document/report creation |
| content | 7 | Writing/creative work |

## Views

- **📋 Pending Queue** — what's waiting, sorted by Created At
- **⚡ Running Tasks** — what's being worked on now
- **✅ Done This Week** — what's been completed
- **📊 Pipeline Board** — visual overview grouped by status

## FAQ

**How long before a task starts?** Automation tasks are picked up on the
next dispatcher cycle (minutes). Other types depend on team capacity.

**Can I make a task urgent?** Ask an admin to move it in the queue manually
— there's no per-task cost override, priority is fixed by `Type`.

**How do I know when my task is done?** Check the "Done This Week" view, or
the task's `Output` field.
