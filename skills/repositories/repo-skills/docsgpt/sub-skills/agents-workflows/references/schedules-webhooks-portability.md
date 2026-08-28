# Schedules, Webhooks, Seeding, and Portability

## Webhooks

Each agent can expose a tokenized endpoint:

```text
GET|POST /api/webhooks/agents/<webhook_token>
```

A trigger returns `task_id`; poll `/api/task_status?task_id=...` until `SUCCESS` or `FAILURE`. Use `Idempotency-Key` for retries: the same key returns the original task id during the retention window instead of enqueueing twice.

Webhook guidance:

- keep token out of URLs/logs when possible;
- accept a small validated payload;
- define timeout/retry policy with jitter;
- classify `4xx` as permanent except rate limits/conflicts;
- do not treat task enqueue as agent success;
- avoid state-changing tools without approval/idempotency.

## Schedules

Schedules can be agent-bound and RedBeat/Celery-backed. Bound minimum interval, schedules per user, run timeout, misfire grace, failure auto-pause and output retention through deployment settings.

For each schedule record timezone, cron/once expression, agent snapshot expectation, input payload, tool policy, owner, next run, and failure notification. Test a manual run before enabling recurrence.

## Premade-agent seeding

Seed YAML uses top-level `agents`. Common fields:

```yaml
agents:
  - name: Support
    description: Answers product questions
    agent_type: classic
    prompt:
      name: Support prompt
      content: "Answer only from supplied context: {summaries}"
    chunks: "8"
    retriever: "classic"
    source:
      name: Product docs
      url: https://example.invalid/docs
      loader: url
    tools:
      - name: read_webpage
        config: {}
```

`${NAME}` placeholders resolve from environment during seeding. Validate offline, provision Postgres/worker, then use the public module command for initialization. `--force` can replace/reseed state and therefore requires explicit review.

## Export/import

- `GET /api/export_agent?id=<id>` returns portable agent YAML.
- `POST /api/import_agent/plan` parses and resolves references without creation.
- `POST /api/import_agent` creates a draft.
- Secrets/tool credentials are stripped on export and must be re-entered.
- Imported URLs receive the same SSRF validation as newly configured tools.
- Workflow agents are not exportable at this snapshot.

Compare the import plan for source/tool/prompt matches, creations, unresolved references and conflicts before commit. Re-test authorization, credentials and model availability in the target deployment.
