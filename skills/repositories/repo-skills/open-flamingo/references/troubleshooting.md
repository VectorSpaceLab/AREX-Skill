# OpenFlamingo Cross-Cutting Troubleshooting

## When to read

Read this when OpenFlamingo installation, imports, dependency versions, package entrypoints, cache/offline behavior, or accelerator assumptions fail before a specific model-usage, training, evaluation, or data-preparation workflow can start.

## Fast diagnosis

```bash
python scripts/check_open_flamingo_env.py --json
```

Use the report to confirm package versions, public API signatures, CUDA availability, and whether packaged train/eval helper files are present.

## Common install/import failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: open_flamingo` | Package is not installed in the active Python environment. | Install `open-flamingo` or install the source package into the environment that will run the task. Then rerun the environment checker. |
| Transformers says PyTorch is unavailable even though `torch` imports | A very new `transformers` release requires newer PyTorch than OpenFlamingo's `torch==2.0.1` pin. | Install a torch-2.0-compatible Transformers release, such as the verified 4.31 series, or refresh the skill if the repository updates its torch pin. |
| Torch/torchvision warns that a module compiled against NumPy 1.x cannot run with NumPy 2.x | `torch==2.0.1` is being used with `numpy>=2`. | Install `numpy<2`, then rerun import/signature checks. |
| `ModuleNotFoundError: sklearn` while importing or running evaluation | The evaluation script imports `sklearn.metrics`, but setup metadata may omit `scikit-learn` from the eval extra. | Install `requirements-eval.txt` or add `scikit-learn` to the evaluation environment. |
| Missing `wordnet` errors during OK-VQA evaluation | OK-VQA postprocessing uses NLTK WordNet data. | In the evaluation environment, run a one-time `import nltk; nltk.download('wordnet')` if network/data policy permits, or stage the NLTK data cache offline. |
| Packaged train/eval entrypoint cannot be found | The installed package layout differs from this source snapshot. | Use a matching OpenFlamingo source checkout/package version or run `refresh-repo-skill` against the new layout. |

## Local import quirks

Some OpenFlamingo training/evaluation files use unqualified imports such as `from data import ...` or `from utils import ...`. The generated skill bundles wrappers that locate the installed package and add the relevant package subdirectory to `sys.path` before executing the packaged entrypoint:

- `sub-skills/training/scripts/run_training_entrypoint.py`
- `sub-skills/evaluation/scripts/run_evaluation_entrypoint.py`
- `sub-skills/evaluation/scripts/run_cache_rices_entrypoint.py`

Prefer the command builders, which point at these wrappers, instead of hand-assembling commands against checkout-relative script paths.

## Cache, network, and credential failures

- `create_model_and_transforms(..., use_local_files=True, cache_dir=...)` still needs all model/tokenizer/OpenCLIP assets to exist locally.
- Model-hub checkpoint downloads may need credentials. Do not embed tokens in reusable scripts; prefer environment variables or pre-staged local files.
- Benchmark datasets and released checkpoints are not bundled. Missing image/question/annotation/checkpoint paths are expected until the user provides them.

## Backend and accelerator failures

- Safe import checks may pass on CPU while generation/training/evaluation still require CUDA memory and compatible wheels.
- `torch.cuda.is_available() == True` proves only framework visibility, not that a chosen model/checkpoint fits memory.
- Distributed training/evaluation defaults to NCCL. If ranks hang, check `MASTER_ADDR`, `MASTER_PORT`, visible GPUs, process count, and whether the cluster launcher already pinned devices.
- For a true required-backend task, verify the actual GPU path with a bounded model/data smoke case before claiming the workflow is fully validated.

## Workflow-specific routing

- Generation tensor/token/cache errors: read `sub-skills/model-usage/references/troubleshooting.md`.
- Training data, FSDP, sample-count, checkpoint, or W&B errors: read `sub-skills/training/references/troubleshooting.md`.
- Benchmark path, metric, RICES, or result-file errors: read `sub-skills/evaluation/references/troubleshooting.md`.
- MMC4 conversion, VQA filling, or schema-validation errors: read `sub-skills/data-preparation/references/troubleshooting.md`.
