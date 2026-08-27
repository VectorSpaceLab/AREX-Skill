# OpenFlamingo Model Zoo and Compatibility

## When to read

Read this for package installation choices, dependency compatibility, released checkpoint selection, and the boundary between safe preflight checks and expensive model/data execution.

## Package identity

- Python distribution: `open_flamingo`
- Public import: `open_flamingo`
- Version in the source snapshot: `2.0.1`
- Public API entry points: `create_model_and_transforms` and `Flamingo`

## Installation variants

The package declares these dependency groups:

| Use case | Install shape | Notes |
|---|---|---|
| Model construction/generation | `pip install open-flamingo` or install this package from a source checkout | Installs `einops`, `einops-exts`, `transformers>=4.28.1`, `torch==2.0.1`, `pillow`, `open_clip_torch>=2.16.0`, and `sentencepiece`. |
| Training | `pip install open-flamingo[training]` or install `requirements-training.txt` with the package | Adds `torchvision`, `braceexpand`, `webdataset`, `tqdm`, and `wandb`. |
| Evaluation | Prefer installing `requirements-eval.txt` with the package | The source `eval` extra includes the core metrics dependencies, but the evaluated script imports `sklearn.metrics`; install `scikit-learn` if it is missing. |
| Everything | `pip install open-flamingo[all]` plus any missing eval requirement such as `scikit-learn` | Full benchmark work still needs datasets, checkpoints, and often GPU capacity. |
| Conda-style environment | Use Python 3.9 when matching the repository environment file | The source environment pins Python 3.9 and installs all package requirement files plus the editable package. |

## Verified compatibility notes

- The repository pins `torch==2.0.1`. In the inspection environment, `torch 2.0.1+cu117`, `torchvision 0.15.2`, `open_clip_torch 3.3.0`, and `transformers 4.31.0` imported successfully.
- Very new Transformers releases may disable PyTorch support when `torch<2.1` is installed. If imports say PyTorch is unavailable despite `torch` being installed, use a Transformers release compatible with torch 2.0.1, such as the verified 4.31 series.
- `torch==2.0.1` can emit compatibility warnings with `numpy>=2`; use `numpy<2` if NumPy initialization warnings appear from torch/torchvision.
- Actual generation, RICES feature extraction, evaluation, and training may use CUDA and substantial memory. A CPU import/signature check is only a preflight check, not proof of benchmark or training throughput.

## Released model/checkpoint families

OpenFlamingo combines an OpenCLIP vision encoder with a causal language model. The source snapshot documents these released model families:

| Public checkpoint family | Language model family | Vision encoder | Cross-attention interval | Typical use |
|---|---|---|---:|---|
| OpenFlamingo-3B-vitl-mpt1b | `anas-awadalla/mpt-1b-redpajama-200b` | OpenAI CLIP ViT-L/14 | 1 | Smallest released checkpoint family for generation/evaluation examples. |
| OpenFlamingo-3B-vitl-mpt1b-langinstruct | MPT-1B Dolly-style instruction variant | OpenAI CLIP ViT-L/14 | 1 | Instruction-tuned language behavior. |
| OpenFlamingo-4B-vitl-rpj3b | RedPajama INCITE Base 3B | OpenAI CLIP ViT-L/14 | 2 | Larger RedPajama-based family. |
| OpenFlamingo-4B-vitl-rpj3b-langinstruct | RedPajama INCITE Instruct 3B | OpenAI CLIP ViT-L/14 | 2 | Instruction-tuned RedPajama family. |
| OpenFlamingo-9B-vitl-mpt7b | MPT-7B | OpenAI CLIP ViT-L/14 | 4 | Largest released checkpoint family in this snapshot. |

## Asset and credential boundaries

- Checkpoints are not bundled with the package or this skill. Users must provide a local checkpoint path or authorize a model-hub download.
- Benchmark datasets are not bundled. Evaluation commands require local image, question, annotation, or ImageNet root paths.
- Some model-hub or dataset downloads may need credentials such as a Hugging Face token. Keep tokens out of scripts and command histories when possible.
- For offline use, place model/tokenizer/vision-encoder assets in a local cache and pass `cache_dir`/local paths plus `use_local_files=True` where applicable.

## Fast preflight sequence

1. Run the root environment checker: `python scripts/check_open_flamingo_env.py --json`.
2. For generation work, use `sub-skills/model-usage/scripts/validate_generation_inputs.py` before constructing a model.
3. For training and evaluation commands, use the bundled command builders so required flags and path groups are checked before expensive execution.
4. Treat full model execution as a separate budgeted step requiring data/checkpoint availability and GPU/runtime approval.
