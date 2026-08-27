# OpenPrompt Troubleshooting

## Purpose

Use this for cross-cutting OpenPrompt install, import, dependency, and checkout-staleness issues. Route template, config, and training specifics to the nearest sub-skill troubleshooting file.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: torch` | PyTorch is missing, the wrong wheel is active, or the environment was created without the runtime stack. | Install a CPU or CUDA-compatible torch wheel first, then rerun `scripts/check_openprompt_install.py`. |
| `ModuleNotFoundError: transformers.generation_utils` | A newer Transformers release removed the legacy alias that OpenPrompt 1.0.1 still imports. | Use the pinned inspection stack or the compatibility shim shipped with `pipeline-basics`. |
| `ModuleNotFoundError: sklearn`, `rouge`, or `scipy` during `import openprompt` | Root import reaches the training/metric stack and these optional-looking packages are actually required for the public surface. | Install the runtime stack listed in `references/package-overview.md` before retrying. |
| `pip install openprompt` succeeds but `import openprompt` fails | The published package was installed without the supporting runtime stack or a newer dependency version drifted. | Use the bundled smoke, inspect `pip check`, and compare the checkout with `references/repo-provenance.md`. |
| `FileNotFoundError` for a template/verbalizer/dataset path | A repo example copied a relative path from the source checkout, but the current checkout or generated skill uses a different base directory. | Route to `data-and-config-workflows` for config paths or `template-verbalizer-design` for prompt assets. |
| `torch.cuda.is_available() == False` on a CUDA machine | The environment used a CPU-only torch wheel or the CUDA request was optional and not installed. | Only treat CUDA as a requirement when the selected workflow says so; otherwise remain on the CPU smoke path. |

## Recovery sequence

1. Run `python scripts/check_openprompt_install.py` from the root skill directory.
2. If the import smoke fails, check `pip check` and compare the installed dependency stack with `references/package-overview.md`.
3. If the failure concerns template syntax, prompt assets, dataset config, or runner selection, move to the matching sub-skill instead of patching the root.
4. If the current checkout changed, compare it with `references/repo-provenance.md` before assuming the skill is current.

## When to stop

Stop and ask for additional hardware, data, or download permission when the task needs a real model, a dataset download, or a GPU/backend that the current scope did not select.
