# Model Profiles

## Purpose

Several chat-provider partner packages include model capability data under `langchain_<provider>/data/`. LangChain chat models expose this data through profile fields so code can reason about context windows, modalities, tool calling, structured output, and related capabilities.

The profile data is maintained with the `langchain-model-profiles` package in `libs/model-profiles`. That package provides the `langchain-profiles` CLI and fetches model data from models.dev, then merges provider-specific augmentations and generates `_profiles.py`.

## Provider Data Layout

Provider data directories commonly contain:

- `__init__.py` for package data exports.
- `_profiles.py`, a generated Python profile data file.
- `profile_augmentations.toml` when the provider maintains local augmentations on top of models.dev data.

Representative partners with profile data include OpenAI, Anthropic, DeepSeek, Fireworks, Groq, Hugging Face, MistralAI, Perplexity, OpenRouter, and xAI. Some providers have `_profiles.py` without a local augmentation file.

## Refresh Workflow

Run profile refresh from `libs/model-profiles`, not from the partner package:

```bash
cd libs/model-profiles
uv run langchain-profiles refresh --provider openai --data-dir ../partners/openai/langchain_openai/data
uv run langchain-profiles refresh --provider anthropic --data-dir ../partners/anthropic/langchain_anthropic/data
```

The `--data-dir` value must point to the provider's `data` directory containing `profile_augmentations.toml` when one exists, not to the top-level package directory.

After refresh:

1. Review changes to `_profiles.py` and any augmentation file separately.
2. Check whether generated capability flags, context windows, model aliases, modality support, or structured-output/tool-calling fields changed.
3. Update partner tests that assert profile behavior or model defaults.
4. Run narrow partner tests for profile usage and no-network chat-model behavior.
5. Run `uv run --group test pytest` for `libs/model-profiles` only when CLI behavior changed.

## External Data Directory Confirmation

When refreshing a provider data directory outside the `libs/model-profiles` working tree, the CLI may require confirmation. Use an explicit confirmation pipe only when the path is intentionally outside that working tree and the user has approved the target directory:

```bash
echo y | uv run langchain-profiles refresh --provider google --data-dir ../external-provider/langchain_provider/data
```

Do not use machine-specific local paths in public skill content or generated runtime docs. For normal work in this monorepo, prefer relative paths from `libs/model-profiles` to `../partners/<provider>/langchain_<provider>/data`.

## Generated File Policy

Treat `_profiles.py` as generated data. Avoid hand-editing it as the primary solution for drift. If a generated field is wrong:

- Check whether models.dev changed upstream.
- Check whether `profile_augmentations.toml` should override or add provider-specific facts.
- Refresh through `langchain-profiles` and review the generated diff.
- Add or update tests that explain the intended capability behavior.

Manual edits may be appropriate only as a short-lived diagnostic or when the package explicitly does not have a refresh path. If manual edits are unavoidable, clearly document why and ask for maintainer review.

## Explaining Capability Flag Changes

When a user asks why generated profile flags changed, compare these sources:

1. Previous `_profiles.py` values.
2. New `_profiles.py` values after refresh.
3. `profile_augmentations.toml` changes.
4. Upstream models.dev data changes when available.
5. Partner tests or source code that consume profile fields.

Explain changes in user-facing terms: which model changed, which capability changed, whether it came from upstream or augmentation data, and what LangChain behavior may be affected.

Examples of meaningful profile changes:

- Context window or output token limit changes.
- Tool-calling or structured-output support toggles.
- Image/audio/document modality support changes.
- Model family aliases appearing, disappearing, or mapping to a different canonical model.
- Reasoning, JSON mode, or response-format capability updates.

## Validation Commands

From `libs/model-profiles` when the CLI or refresh pipeline changes:

```bash
uv run --group test pytest tests/unit_tests/
uv run --group lint ruff check .
uv run --group lint mypy .
```

From a partner package after refreshing its data:

```bash
uv run --group test pytest tests/unit_tests/test_chat_models.py
uv run --group test pytest tests/unit_tests/test_standard.py
uv run python scripts/check_version.py
```

Choose files that exist in the target package. If `uv` is unavailable, record that refresh and tests were skipped; do not claim profile data was regenerated.

## Review Checklist

- The provider name passed to `--provider` matches the data source expected by the CLI.
- The `--data-dir` points at the provider `data` directory.
- Generated `_profiles.py` diffs are reviewed rather than accepted blindly.
- Augmentation changes are small, provider-specific, and justified.
- Partner tests cover behavior that depends on changed capability flags.
- No network-heavy provider API calls are run unless the user asked for live validation.
