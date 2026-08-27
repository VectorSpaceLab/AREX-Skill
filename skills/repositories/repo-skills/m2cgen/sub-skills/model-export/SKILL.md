---
name: model-export
description: "Export a fitted Python ML model to native code with m2cgen via API or CLI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# model-export

Use this skill when a user already has a fitted Python model and wants m2cgen-generated native code.

## Route by intent

- **In-memory Python object**: use `references/api-reference.md`.
- **Serialized model or shell workflow**: use `references/cli-reference.md`.
- **Supported languages, model families, and output shapes**: use `references/model-overview.md`.
- **End-to-end export flows**: use `references/workflows.md`.
- **Failure handling**: use `references/troubleshooting.md`.

## In scope

- Export through the public `m2cgen.export_to_*` functions.
- Export through `python -m m2cgen` or the installed `m2cgen` console script.
- Pickle/joblib input, stdin piping, recursion-limit tuning, and language-specific naming flags.

## Out of scope

- Model training or fitting.
- Executing generated code in foreign runtimes.
- Maintainer release/publishing workflows.
- Bulk generated-example regeneration tooling; treat it as maintainer-side reference material only.
- Any workflow that depends on the original source checkout at runtime.

## Quick check

Run `python scripts/smoke_export.py` for a narrow, deterministic check of public export calls using a model the script creates locally. It executes only the generated Python export; it does not compile or run the other target-language outputs and is not a replacement for end-to-end fixture coverage.

Add `--cli` to exercise the `python -m m2cgen` file and stdin paths. `--joblib` and `--console-script` are optional paths that require `--cli`; passing either without `--cli` is rejected rather than silently reporting a partial check. Neither optional path is exercised by the default command. Read `references/workflows.md` before running it where executing generated Python, invoking a PATH-resolved console script, or the temporary-file lifecycle matters.