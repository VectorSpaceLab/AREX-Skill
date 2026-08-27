# Repo and Model CLI Reference

## When to read

Read this when you need the exact `openllm repo` or `openllm model` flags and behavior before changing a repository catalog.

## Verified command surface

### `openllm repo list`

Lists configured repositories.

### `openllm repo add NAME REPO_URL`

- `NAME` must be a valid identifier-like repo alias.
- `REPO_URL` must parse as a public Git repository URL.
- OpenLLM normalizes the alias to lowercase.

### `openllm repo remove NAME`

Removes a configured repository alias.

### `openllm repo update`

- Refreshes all configured repositories.
- Uses shallow Git clones and falls back to Dulwich when Git cloning fails.
- Also updates alias files after refresh.

### `openllm repo default`

Prints the local path for the default repository cache.

### `openllm model list [TAG] [--repo REPO_ALIAS]`

- Lists all Bentos, or filters by model name/version/tag prefix.
- `--tag` is accepted as an option in the CLI signature, and the internal behavior also accepts a positional tag filter.
- `--repo` selects a configured repository alias.
- `--verbose` increases detail.

### `openllm model get TAG [--repo REPO_ALIAS]`

- Prints one Bento's metadata.
- Uses the same model resolution path as `model list`.

## Behaviors to remember

- The default repository alias is `default`, and the packaged config also includes `nightly`.
- If a requested repo alias does not exist, OpenLLM prints the available aliases before exiting.
- When multiple Bentos match a tag, OpenLLM asks the user to choose or prints the ambiguous entries.
- `openllm model list` can render a compact JSON-like structure for README generation, but that mode is a maintainer-only path and is not part of normal runtime guidance.
