# Model Profile CLI

LangChain model profile data is maintained with the `langchain-model-profiles` package. The CLI command is `langchain-profiles`, and its primary operation is `refresh`.

## When To Use

Use this workflow when a provider package's model capability data changes, a task mentions `ModelProfile`, `_profiles.py`, `profile_augmentations.toml`, context windows, modalities, tool-calling flags, structured-output flags, or provider model metadata.

Route provider API behavior and model implementation logic to the integration-owning sub-skill. This reference only covers profile-data maintenance and validation.

## Data Directory Rule

`--data-dir` must point to the provider package's data directory that contains `profile_augmentations.toml`, not to the package root and not to the model-profiles package root.

Examples of correct shapes:

```bash
cd libs/model-profiles
uv sync --group test
uv run langchain-profiles refresh --provider openai --data-dir ../partners/openai/langchain_openai/data
uv run langchain-profiles refresh --provider anthropic --data-dir ../partners/anthropic/langchain_anthropic/data
```

The CLI writes generated profile data to `_profiles.py` inside the selected data directory. Treat `_profiles.py` as generated output and prefer updating `profile_augmentations.toml` plus rerunning the CLI instead of manual edits.

## External Directory Confirmation

The CLI validates and resolves the data directory. If the target directory is outside the current working directory, it prints a warning and asks for confirmation. For data directories outside `libs/model-profiles`, run from `libs/model-profiles` and pipe an explicit confirmation only when the path is intentionally outside that current directory:

```bash
echo y | uv run langchain-profiles refresh --provider google --data-dir /path/to/external/provider/data
```

Do not use an absolute local path in generated skill content or public docs. In runtime work, prefer repository-relative paths when the provider package is inside the same checkout.

## What Refresh Does

The refresh command:

- Downloads model data from `https://models.dev/api.json` with an HTTP timeout.
- Fails if the provider ID is missing from the downloaded data.
- Loads provider-level and model-level overrides from `profile_augmentations.toml` when present.
- Includes models that exist only in augmentations.
- Warns if generated profile keys are not declared by `langchain_core.language_models.model_profile.ModelProfile`.
- Writes `_profiles.py` atomically and refuses unsafe symlink/path escapes.

Because this command fetches network data and mutates generated files, do not run it as a default no-network verification check. Ask for approval when network or generated-file changes are outside the user's request.

## Safe Validation Around Profiles

For pure code changes to the CLI, use unit tests with mocked network responses:

```bash
cd libs/model-profiles
uv sync --group test
uv run --group test pytest tests/unit_tests/test_cli.py
```

For profile refresh changes, validate both generated content and package checks:

```bash
cd libs/model-profiles
uv sync --group test --group lint --group typing
uv run --group test pytest tests/unit_tests/test_cli.py
uv run --group lint ruff check .
uv run --group typing mypy .
```

After intentionally refreshing a provider's data, inspect the diff for:

- Expected model IDs added, removed, or updated.
- Overrides from `profile_augmentations.toml` preserved.
- No hand-written changes inside generated `_profiles.py` beyond CLI output.
- Warnings about undeclared `ModelProfile` keys addressed before publishing provider packages.

## Common Provider IDs

Provider IDs are models.dev provider keys such as `openai`, `anthropic`, `google`, or other provider identifiers supported by the upstream data source. Use the provider's existing augmentation file and generated data location to confirm the exact ID before refreshing.

## Skip Conditions

Skip or defer profile refresh when:

- Network access is not available or not approved.
- `uv` or the model-profiles dependency environment is unavailable.
- The data directory does not contain or intentionally does not use `profile_augmentations.toml` and the user has not confirmed generating a new data directory.
- The target is outside the current directory and the user has not approved the CLI confirmation.
- The task is only a deterministic code/test change unrelated to profile data.
