# CLI Reference

Use these commands for events, automations, blocks, variables, assets-adjacent operational checks, and concurrency limits. All commands use the active Prefect profile/API URL; route profile, login, and server startup issues to `../cli-server-operations/SKILL.md`.

## Events

### Emit one event

```bash
prefect events emit EVENT [--resource KEY=VALUE] [--resource-id ID] [--related JSON] [--payload JSON]
```

Aliases: `prefect event emit`.

Examples:

```bash
prefect events emit external.invoice.received \
  --resource-id invoice.2026-0001 \
  --payload '{"amount": 125.5}'
```

```bash
prefect events emit external.file.validated \
  --resource '{"prefect.resource.id":"file.s3.bucket.key","environment":"prod"}' \
  --related '[{"prefect.resource.id":"customer.acme","prefect.resource.role":"customer"}]'
```

Safety: contacts the Prefect API and creates an event.

### Stream events

```bash
prefect events stream [--format json|text] [--output-file PATH] [--account] [--run-once]
```

Examples:

```bash
prefect events stream --format json
prefect events stream --format text --run-once
prefect events stream --format json --output-file events.ndjson
```

Safety: opens a live subscription. `--account` is Cloud/account-wide and may include audit logs.

## Automations

Aliases: `prefect automation` and `prefect automations`.

### Validate locally first

```bash
python ../scripts/validate_automation.py --file automation.yaml
python ../scripts/validate_automation.py --json '{"name":"..."}'
python ../scripts/validate_automation.py --example deployment-event
```

The bundled validator performs schema checks only and does not contact a server.

### Create automations

```bash
prefect automation create --from-file automation.yaml
prefect automation create --from-file automation.json
prefect automation create --from-json '{"name":"observer","trigger":{"type":"event"},"actions":[{"type":"do-nothing"}]}'
```

Input may be one automation object, a list, or an object with `automations: [...]`.

Safety: contacts the Prefect API and creates server-side automations.

### Inspect, pause, resume, update, delete

```bash
prefect automation ls
prefect automation inspect NAME --output json
prefect automation inspect --id UUID --yaml
prefect automation pause NAME
prefect automation resume NAME
prefect automation update --id UUID --from-file automation.yaml
prefect automation delete NAME
```

Safety: inspect/list are read operations; pause/resume/update/delete mutate server-side automations.

## Blocks

Aliases: `prefect block` and `prefect blocks`.

### Discover block types and documents

```bash
prefect block type ls
prefect block type ls --output json
prefect block type inspect secret
prefect block ls
prefect block ls --output json
prefect block inspect secret/my-secret
```

Read-only unless the active API URL points to a workspace where listing is audited.

### Register block types

```bash
prefect block register --module my_package.blocks
prefect block register --file my_block.py
```

Safety: registers or updates block type/schema metadata in the configured API. Use after reviewing the module/file for import side effects.

### Create and delete block documents

```bash
prefect block create BLOCK_TYPE_SLUG
prefect block delete BLOCK_DOCUMENT_SLUG
```

`prefect block create` is interactive for field values; prefer Python `Block.save(...)` for scripted creation. Deleting a block document can break flows, automations, deployments, or variables that reference it.

## Variables

```bash
prefect variable ls [--limit N]
prefect variable inspect NAME
prefect variable get NAME
prefect variable set NAME VALUE [--overwrite] [--tag TAG]
prefect variable unset NAME
prefect variable delete NAME
```

Notes:

- `set` requires `--overwrite` to update an existing variable.
- CLI `VALUE` is received as a shell string; quote it carefully. Use the Python `Variable.set(...)` API when you need native JSON-like values instead of string literals.
- `delete` is an alias for `unset`.

Safety: list/inspect/get are read operations; set/unset/delete mutate server-side variables.

## Global Concurrency Limits

Primary command: `prefect global-concurrency-limit`; alias: `prefect gcl`.

```bash
prefect global-concurrency-limit ls
prefect global-concurrency-limit ls --output json
prefect global-concurrency-limit inspect NAME
prefect global-concurrency-limit inspect NAME --output json
prefect global-concurrency-limit create NAME --limit 5
prefect global-concurrency-limit create NAME --limit 10 --slot-decay-per-second 1.0
prefect global-concurrency-limit update NAME --limit 3
prefect global-concurrency-limit disable NAME
prefect global-concurrency-limit enable NAME
prefect global-concurrency-limit delete NAME
```

`create` parameters:

- `NAME` is required.
- `--limit` / `-l` is required.
- `--disable` creates the limit inactive.
- `--active-slots` defaults to `0`.
- `--slot-decay-per-second` defaults to `0.0`; set it for `rate_limit` use.

Safety: list/inspect are read operations; create/update/enable/disable/delete mutate server-side concurrency limits.

## Tag-Based Task Concurrency Limits

Primary command: `prefect concurrency-limit`; alias: `prefect concurrency-limits`.

```bash
prefect concurrency-limit create TAG CONCURRENCY_LIMIT
prefect concurrency-limit inspect TAG
prefect concurrency-limit inspect TAG --output json
prefect concurrency-limit ls
prefect concurrency-limit delete TAG
```

Use these for task tag limits, not arbitrary Python code sections. Use global concurrency limits with `prefect.concurrency.sync.concurrency` or `prefect.concurrency.asyncio.concurrency` for explicit code-section throttling.

## Help Checks

Before emitting or mutating workspace state, check the exact local command help:

```bash
prefect events emit --help
prefect events stream --help
prefect automation create --help
prefect block type ls --help
prefect variable set --help
prefect global-concurrency-limit create --help
prefect concurrency-limit create --help
```

Use `--profile PROFILE` for one command without changing the active profile, and `--prompt/--no-prompt` where the command supports session parameters.
