# Welcome to Hermes

Hermes is our task management system: it automatically prioritizes work so
you can focus on doing, not managing.

## Creating a task (30 seconds)

1. Open the Hermes database.
2. Click **+ New**.
3. Fill in:
   - **Task Name** — what needs to be done
   - **Pipeline** — `Automation`, `Research`, `Report`, or `Content`
   - **Status** — leave as `Pending`
   - **Notes** — optional context
4. Press Enter.

## How tasks get processed

The dispatcher always picks the cheapest (lowest-effort) pending task first.
Tasks move through **Pending → Running → Completed**.

| Pipeline | Cost | Use for |
|----------|------|---------|
| Automation | 1 | Quick, repetitive tasks (data entry, simple updates) |
| Research | 3 | Information gathering |
| Report | 5 | Document/report creation |
| Content | 7 | Writing/creative work |

## Views

- **📋 Pending Queue** — what's waiting, sorted by priority
- **⚡ Running Tasks** — what's being worked on now
- **✅ Done This Week** — what's been completed
- **📊 Pipeline Board** — visual overview grouped by status

## FAQ

**How long before a task starts?** Automation tasks are picked up on the
next dispatcher cycle (minutes). Other pipelines depend on team capacity.

**Can I make a task urgent?** Set its Cost override manually, or ask an
admin to jump it in the queue.

**How do I know when my task is done?** Check the "Done This Week" view.
