# CLI Reference

The Python client package exposes two equivalent command names:

```bash
mem-cli --help
memmachine --help
```

Both commands use the same parser. Put global client flags before the main
subcommand.

## Global Flags And Environment Variables

| Flag | Environment default | Meaning |
| --- | --- | --- |
| `--base-url` | `MEMORY_BACKEND_URL` | MemMachine server URL. |
| `--api-key` | `MEMMACHINE_API_KEY` | Bearer API key for authenticated deployments. |
| `--timeout` | `MEMMACHINE_TIMEOUT` | Client request timeout. |
| `--max-retries` | `MEMMACHINE_MAX_RETRIES` | Retry count for retryable failures. |

Do not print secret API keys. When showing commands, use placeholders such as
`"$MEMMACHINE_API_KEY"`.

## Health, Metrics, And Config

```bash
mem-cli --base-url "http://localhost:8080" health
mem-cli --base-url "http://localhost:8080" metrics
mem-cli --base-url "http://localhost:8080" config resources
```

Use `health` before live memory operations. Use `config resources` only when the
server exposes configuration APIs and the user has permission to inspect them.

## Project Commands

Project context flags are `--org-id` and `--project-id`.

```bash
mem-cli projects list
mem-cli projects create --org-id "my-org" --project-id "my-project" \
  --description "Demo project"
mem-cli projects get --org-id "my-org" --project-id "my-project"
mem-cli projects get-or-create --org-id "my-org" --project-id "my-project"
mem-cli projects episode-count --org-id "my-org" --project-id "my-project"
mem-cli projects delete --org-id "my-org" --project-id "my-project"
```

Ask before running `delete`. For create/get-or-create, include resource options
only when the server-side backend resources are known.

## Memory Add

```bash
mem-cli memory add "Alice prefers aisle seats." \
  --org-id "my-org" --project-id "my-project" \
  --metadata user_id=alice \
  --metadata agent_id=assistant \
  --metadata session_id=session-001 \
  --metadata category=travel
```

Other useful flags:

- `--role` for message role, such as `user` or `assistant`.
- `--producer` and `--produced-for` for producer attribution.
- `--extra-metadata` for a JSON object when key-value pairs are insufficient.
- `--create` to create the project if it is missing.

## Memory Search

```bash
mem-cli memory search "What seating does Alice prefer?" \
  --org-id "my-org" --project-id "my-project" \
  --metadata user_id=alice \
  --limit 5
```

Advanced search options:

```bash
mem-cli memory search "travel preferences" \
  --org-id "my-org" --project-id "my-project" \
  --filter "metadata.category = 'travel'" \
  --set-metadata '{"user_id":"alice"}' \
  --expand-context 1 \
  --score-threshold 0.2 \
  --agent-mode
```

Use `--agent-mode` only after verifying that server-side retrieval-agent LLM and
reranker resources are configured. A simple search is safer for first checks.

## Memory List And Delete

```bash
mem-cli memory list --org-id "my-org" --project-id "my-project" \
  --type episodic --page-size 20 --page-num 0

mem-cli memory delete-episodic --org-id "my-org" --project-id "my-project" \
  --id "episode-id"

mem-cli memory delete-semantic --org-id "my-org" --project-id "my-project" \
  --id "semantic-id"
```

Deletion is destructive. Confirm the target IDs and type before running.

## JSON And Metadata Parsing

- `--metadata key=value` can be repeated for string metadata.
- `--extra-metadata` and `--set-metadata` accept JSON objects.
- Keep shell quoting simple. On POSIX shells, wrap JSON in single quotes; on
  PowerShell, use the shell's JSON quoting conventions.
- Project context is not memory metadata. Always supply `--org-id` and
  `--project-id` for project-scoped operations.

## Safe CLI Smoke

From this sub-skill directory:

```bash
python scripts/mem_cli_smoke.py --help
python scripts/mem_cli_smoke.py --show-example search
python scripts/mem_cli_smoke.py --command mem-cli --check-help
```

The bundled smoke script checks parser/help and prints examples; it does not
contact a server unless you copy and run the generated command yourself.
