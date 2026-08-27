# Hub and CLI Troubleshooting

Use this reference for custom module authoring, `evaluate-cli`, Hub Space publishing, Gradio widget, and `push_to_hub` failures.

## `ModuleNotFoundError: cookiecutter`

Cause: the CLI imports `cookiecutter.main.cookiecutter` at module import time. A minimal Evaluate install may not include the template extra.

Resolution:

- Install the package extras needed for template creation, commonly `evaluate[template]` for this checkout.
- If only inspecting help, run `python scripts/inspect_evaluate_cli.py` first to confirm exactly which import fails.
- Do not run `evaluate-cli create` just to test the import; it is credentialed and mutating.

## `ImportError: cannot import name 'Repository' from 'huggingface_hub'`

Cause: the current CLI source imports `Repository` from `huggingface_hub`. Some newer Hub client versions removed or changed that API.

Resolution:

- Use the inspector script to confirm the failing import.
- Align `huggingface_hub` with the version range expected by this Evaluate checkout, or use an environment where `from huggingface_hub import Repository` succeeds.
- For non-publishing tasks, avoid the CLI and draft the template files manually.
- Do not patch public skill guidance to require a specific local path or environment; keep compatibility notes version-aware.

## `ValueError: Hyphens ('-') are not allowed in module names.`

Cause: `evaluate-cli create` rejects hyphens in the pretty `module_name` before slugging. The slug is derived by lowercasing and replacing spaces with underscores.

Resolution:

- Use spaces instead of hyphens, for example `"Exact Match Plus"` rather than `"exact-match-plus"`.
- Expect the generated module slug to be `exact_match_plus`.

## `ValueError: The module_type needs to be one of metric, comparison, or measurement`

Cause: `--module_type` is validated before any Hub action.

Resolution:

- Use exactly one of `metric`, `comparison`, or `measurement`.
- Match the generated class base and info class to the type: `evaluate.Metric`/`MetricInfo`, `evaluate.Comparison`/`ComparisonInfo`, or `evaluate.Measurement`/`MeasurementInfo`.

## Hub authentication or namespace errors

Common symptoms: `whoami` fails, Space creation fails, clone fails, private Space creation fails, organization permissions are denied, or push is rejected.

Resolution:

- Confirm the user wants a credentialed/network operation before running it.
- Ask the user to authenticate with a Hugging Face token outside the public skill content if needed.
- Use `--organization` only when the token has permission to create Spaces in that organization.
- Use `--private` only when the account or organization can create private Spaces.
- If the Space already exists, choose another module name/namespace or manually clone/update the existing Space after user approval.

## `push_to_hub` task/model/dataset issues

Symptoms and meanings:

- Unsupported `task_type`: Evaluate raises `ValueError` before metadata update.
- Missing dataset: Evaluate logs a warning but may still update metadata.
- Missing model repo: Evaluate raises `ValueError` and does not update metadata.
- Existing metric fields: `overwrite=False` can prevent replacement; `overwrite=True` is intentionally mutating.

Resolution:

- Validate `model_id`, `dataset_type`, `metric_type`, and `task_type` before writing metadata.
- Ask before setting `overwrite=True`.
- Treat all metadata updates as Hub writes requiring network and repository permissions.

## README/module card YAML fails

Cause: generated or edited README frontmatter is invalid YAML. Repository tests load module README frontmatter as a dictionary.

Resolution:

- Keep the leading `---` YAML block valid.
- Quote descriptions containing colons or special characters.
- Ensure list fields such as `datasets` and `tags` are YAML lists.
- Re-check README parsing before publishing.

## Gradio widget fails or behaves oddly

Cause: `launch_gradio_widget` imports Gradio only when launching, infers inputs from `metric.features`, and treats non-string/non-numeric features as JSON strings.

Resolution:

- Install Gradio only when widget execution is required.
- For complex schemas, nested features, multiple input schemas, or better UX, replace the default generated `app.py` with a custom Gradio app.
- Tell users to wrap text inputs in double quotes when the generated widget expects JSON-like strings.
- Keep `_info().features` accurate; widget headers and parsing depend on it.

## Template dependency and reproducibility caveats

The generated `requirements.txt` can reference Evaluate from the main branch. For reproducible Spaces, consider pinning a released Evaluate version or a commit after confirming compatibility. Add extra package dependencies needed by `_compute` or `_download_and_prepare`, but avoid adding broad development dependencies to the Space.
