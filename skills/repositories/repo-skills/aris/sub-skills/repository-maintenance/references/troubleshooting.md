# Repository Maintenance Troubleshooting

## Test Collection Fails

Check whether the test expects `pytest`, `httpx`, `requests`, `lark_oapi`, a CLI, or a fixture helper. Install only the dependency for the selected test surface in a private environment, or classify a credentialed/optional test as skipped. Avoid modifying a user's existing environment without approval.

## Catalog Test Reports Missing or Stale Skills

Compare the mainline `skills/` directories with `tools/skill-groups.tsv`. Exclude shared references and platform mirror trees according to the repository's own test rules. Add or remove catalog rows atomically with the skill change.

## Mirror Drift

Check the mainline skill and the corresponding Codex mirror/overlay. Preserve semantic behavior while adapting tool calls and reviewer mechanics. Run mirror/update tests before broad corpus checks.

## Helper Lint Failure

Replace hardcoded source-repo paths with the documented resolver chain. If the helper is owned by one skill, bundle it under that generated/runtime skill's `scripts/`; if it is shared, keep the resolver and failure policy consistent.

## Provenance Test Failure

Review author/reviewer model-family classification and unknown/collision behavior. A deterministic verifier is a process, not a model family; same-family model pairs must not be auto-accepted.

## MCP Test Failure

Start with JSON-RPC shape and missing-credential paths. Keep API calls mocked. For local HTTP manual review, use a temporary pending directory and test token/thread continuity without opening a browser.
