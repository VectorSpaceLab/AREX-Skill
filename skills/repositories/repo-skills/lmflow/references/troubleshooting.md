# Troubleshooting

## Purpose

Read this for cross-cutting LMFlow install/import/runtime issues before asking a future agent to retry a workflow.

## Common Failures

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ModuleNotFoundError` for `lmflow` | Package not installed into the environment used for the check | Run the baseline editable install and retry the import from the environment Python. |
| `ModuleNotFoundError: No module named 'ray.data'` during pipeline imports | Full Ray extra is missing, or a partial/namespace `ray` path is shadowing the real package | Install the `ray` extra in a clean environment and rerun from a directory without stray `ray` namespace packages. |
| `No module named 'vllm'` or `No module named 'sglang'` | Optional inference engine extra not installed | Install exactly one engine extra in its own environment. |
| `vLLM and SGLang` both requested in one environment | Their CUDA/PyTorch stacks conflict | Split them into separate prefixes. |
| `ValueError` about missing `type` or `instances` in datasets | JSON does not match LMFlow's required schema | Use the dataset validator script and fix the LMFlow JSON layout. |
| `Output directory already exists and is not empty` | Training output path is reused without overwrite/resume | Choose a new output path or intentionally pass overwrite/resume after checking checkpoints. |
| `CUDA is not available on this machine, but GPU execution was requested` | CPU-only environment or GPU not visible to the process | Use CPU-compatible settings or prepare a CUDA build on a GPU host. |
| `Multimodal not available` | Pillow/multimodal extra missing | Install the `multimodal` extra and verify image data paths. |
| `wandb` prompts or login failures | W&B is enabled by default in some launchers | Log in intentionally or set `--report_to none` / disable W&B mode. |
| `transformers` template or version mismatch | Template requires a newer Transformers release | Upgrade the package or use a template supported by the installed version. |

## What To Check Next

- Use `scripts/check_lmflow_environment.py` to confirm imports, route maps, and CUDA visibility.
- Use `data-and-templates/scripts/validate_lmflow_dataset.py` for dataset schema problems.
- Use `training-and-optimization/scripts/build_finetune_command.py` for safe command construction before a long run.
- Use `inference-and-evaluation/scripts/build_inference_command.py` for engine-specific generation commands.
- Use `post-training-alignment/scripts/build_alignment_command.py` when the task is preference optimization or RAFT.
