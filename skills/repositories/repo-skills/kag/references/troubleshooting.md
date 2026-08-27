# Troubleshooting

## Purpose

Use this when KAG imports, config loading, registry lookup, or runtime workflows behave unexpectedly.

## Common failures

### `import kag` fails

**Symptoms**

- `FileNotFoundError` mentioning `kag_config.yaml`
- missing dependency errors during import
- `knext` imports work but `kag` does not

**Likely causes**

- no discoverable `kag_config.yaml` in the current directory or its parents
- the package is not installed in the active environment
- a required dependency from `install_requires` is missing

**Recovery**

1. Run `scripts/check_kag_install.py`.
2. If you are outside a project directory, use the bundled install check or a minimal temporary config.
3. Reinstall `openspg-kag` in an isolated environment if the package is missing.

### CLI entry point looks missing

**Symptoms**

- `kag: command not found`
- `knext: command not found`
- help output does not show the expected subcommands

**Likely causes**

- the console scripts were not installed for the active environment
- PATH is pointing at the wrong Python environment

**Recovery**

1. Run `scripts/check_kag_install.py --cli-help`.
2. Confirm the environment's `pip` and `python` match the installed package.
3. Reinstall the distribution in that environment if necessary.

### Config keys or registry names are wrong

**Symptoms**

- `from_config(...)` raises a registry error
- a pipeline or builder type cannot be found
- an example works only after importing local modules first

**Likely causes**

- the `type` value does not match a registered name
- a custom module was never imported, so its registrations never ran
- the wrong config file was discovered

**Recovery**

1. Use `kag interface --list` or `kag interface --cls <ClassName>`.
2. Use `scripts/inspect_kag_config.py` to see the active config.
3. Make sure any custom project modules are imported before `from_config(...)`.

### API keys, models, or vector dimensions are invalid

**Symptoms**

- model checker errors
- embedding dimension mismatch
- provider requests fail early

**Likely causes**

- `api_key`, `base_url`, or `model` is wrong
- the vectorizer produces a dimension different from the project expects
- a provider or local model service is unavailable

**Recovery**

1. Inspect the config with `scripts/inspect_kag_config.py`.
2. Confirm model credentials and base URLs.
3. Verify the embedding dimension before reusing an existing project.

### Project namespace or schema layout is wrong

**Symptoms**

- project creation fails validation
- schema commit cannot find the expected schema file
- builder output is written into the wrong namespace

**Likely causes**

- the namespace is not in the expected capitalized alphanumeric form
- `schema/<Namespace>.schema` does not match the project namespace
- the project directory is missing the expected builder/solver folders

**Recovery**

1. Run `sub-skills/knowledge-construction/scripts/validate_project_layout.py`.
2. Fix the namespace and schema filename mismatch.
3. Re-run the validation before calling `knext project` or `knext schema`.

### Builder or benchmark work mutates data unexpectedly

**Symptoms**

- checkpoints appear in the project tree
- graph data changes when you expected a dry run
- benchmark scripts rewrite YAML files

**Likely causes**

- a builder writer is in delete mode
- a benchmark launcher is executing live build/eval commands
- the job plan was not checked before running

**Recovery**

1. Inspect the project with the bundled layout/config helpers.
2. Use the benchmark planner script before running live commands.
3. Do not remove checkpoints or graph data unless you intend to discard them.

### OpenSPG or service calls are unavailable

**Symptoms**

- `knext project`, `knext schema`, or query commands cannot reach a server
- MCP startup fails after config validation
- query results return `UNKNOWN` or no references

**Likely causes**

- no OpenSPG server is running at the configured host
- the project id or host address does not match the active config
- the chosen workflow requires external credentials or a live backend

**Recovery**

1. Check the host address in the project config.
2. Confirm the project id is the one you intended to use.
3. Stop and ask for credentials or service approval when the workflow truly requires a live backend.

## When to stop

Stop and ask for user approval when a fix requires:

- external API keys or private model credentials
- a live OpenSPG server or cluster job submission
- destructive graph deletion
- a change to the user's existing environment that could break it
