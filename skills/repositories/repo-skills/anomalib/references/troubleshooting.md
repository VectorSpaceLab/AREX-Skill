# Anomalib Troubleshooting

Use this reference for cross-cutting package problems that are not yet specific enough to belong to one workflow sub-skill.

## Fast triage

1. Run `scripts/check_import.py` to confirm the package imports at all.
2. If the failure is installation or CLI-related, move to `sub-skills/install-and-cli/`.
3. If the failure names a model, datamodule, layout, or registry entry, move to `sub-skills/data-and-models/`.
4. If the failure names metrics, callbacks, loggers, preprocessing, or checkpoint behavior, move to `sub-skills/training-and-evaluation/`.
5. If the failure names export, Torch/OpenVINO inference, or trust gating, move to `sub-skills/deployment-and-inference/`.
6. If the failure names benchmark orchestration or tiled ensemble roots, move to `sub-skills/pipelines-and-benchmarks/`.

## Common package-level failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: anomalib` | The package is not installed in the active environment. | Install the package first, then rerun `scripts/check_import.py`. If you are using the source checkout, switch to the install guidance in `sub-skills/install-and-cli/`. |
| `anomalib -h` shows only the install router | The runtime stack is incomplete. | Treat this as an install problem and read `sub-skills/install-and-cli/references/troubleshooting.md`. |
| `UnknownModelError` or `UnknownDatamoduleError` | The model or data class path does not match the registered anomalib surface. | Use `sub-skills/data-and-models/` to resolve the registry name or class path. |
| CLI examples mention `--data_path`, but the current command rejects it | The example is stale. | Translate it to the current `--data` syntax using `sub-skills/install-and-cli/references/cli-reference.md`. |
| Optional dependency import errors for `openvino`, `onnxscript`, `nncf`, `av`, `pyarrow`, or logger backends | The workflow needs an extra that is not installed. | Keep the minimum environment small, then install the extra only in the sub-skill that owns the workflow. |
| Benchmark or tiled ensemble commands are missing or confusing | The pipeline module or config shape is not ready. | Use `sub-skills/pipelines-and-benchmarks/` for pipeline preflight and root selection. |

## Recovery pattern

- Confirm the package imports.
- Identify whether the issue is install, data/model selection, training, deployment, or pipelines.
- Switch to the relevant sub-skill reference instead of trying to debug from the root.
- If the issue is still unclear, read `references/repo-provenance.md` to confirm the generation baseline.

## Notes

- Keep workflow-specific failures in the nearest sub-skill troubleshooting page.
- Keep root troubleshooting focused on package-wide install/import and routing failures.
