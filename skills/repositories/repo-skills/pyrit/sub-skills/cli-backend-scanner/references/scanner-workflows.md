# Scanner Workflows

## Safe discovery workflow

1. Run `scripts/pyrit_cli_smoke.py --json` to confirm console scripts exist.
2. Start or select a backend only with user approval:
   - existing backend: `pyrit_scan --server-url http://localhost:8000 --list-scenarios`
   - local backend: `pyrit_scan --start-server --list-scenarios`
3. List available objects before constructing a run: scenarios, initializers, targets, converters, and datasets.
4. Route scenario semantics to `attacks-scenarios`; route target/scorer credentials to `targets-scorers`.

## Example command construction pattern

For a bounded rapid-response style run, assemble fields in this order:

```text
pyrit_scan <scenario-name> \
  --target <registered-target-name> \
  --techniques <technique-name-or-tag> \
  --dataset-names <dataset-name> \
  --max-dataset-size <small-integer> \
  --max-concurrency <bounded-integer> \
  --memory-labels '{"experiment":"label"}'
```

Do not run this pattern until the backend has the target/scorer credentials and the user has approved the dataset/objective scope.

## Result inspection

Use `--scenario-results <id> --view overview` for a summary and `--view attacks` with `--attack-result-ids`/`--limit` for attack rows. If results are missing, confirm that the client is pointed at the same backend and memory database as the run.

## Interactive shell workflow

Use `pyrit_shell --server-url <url>` when the user wants an interactive client. The shell still depends on backend registrations and credentials; shell availability is not proof that a target can send prompts.

## Stop workflow

Use `pyrit_scan --stop-server` only for a local server that this session owns or the user explicitly wants to stop. Do not stop shared services without approval.
