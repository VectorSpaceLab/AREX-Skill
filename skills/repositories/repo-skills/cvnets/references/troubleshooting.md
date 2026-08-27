# CVNets Troubleshooting

## Purpose

Read this when a CVNets workflow fails before you know which sub-skill owns the problem. The aim is to separate cross-cutting install/import/config issues from the deeper workflow-specific failure modes.

## Install and entry-point problems

### Symptom
- `ModuleNotFoundError: main_train`
- `cvnets-train`, `cvnets-eval`, or `cvnets-convert` fails even though the package is installed.

### Likely cause
- The installed console script cannot resolve the top-level `main_*` module in the current environment.

### Recovery
- Use the bundled wrappers in this skill tree instead of the installed console script.
- Start with `scripts/check_install.py` to confirm the repo root, imports, and backend smoke.
- If you only need a parser or config check, use `scripts/inspect_config.py`.

## Config and override problems

### Symptom
- Warnings about unrecognized YAML entries.
- `ValueError` or a parser error when loading a config.
- `--common.override-kwargs` appears to do nothing.

### Likely cause
- A dotted key is misspelled, an option name uses the wrong dash/underscore convention, or the override key is not already registered.

### Recovery
- Run `scripts/inspect_config.py` on the config and confirm the resolved keys.
- Compare the key spelling against `references/configuration.md`.
- Remember that `--common.override-kwargs` only overrides known options; it does not invent new ones.

## Registry and model-name problems

### Symptom
- `__base__ can't be used as a model name`
- Unknown model or loss name errors.
- A pretrained checkpoint loads but the head shape does not match.

### Likely cause
- The request selected a reserved registry name, a family that is not registered for the chosen category, or a checkpoint trained for a different class count.

### Recovery
- Check `references/model-overview.md` for the concrete family names.
- Revisit `dataset.category` and the matching `model.<category>.name` field.
- If the checkpoint is for a different class count, use the correct head configuration or finetuning path.

## Dependency and backend problems

### Symptom
- `ImportError` for `av`, `torchtext`, `ftfy`, `pycocotools`, `decord`, or `coremltools`.
- Video, CLIP, audio, or export paths fail before model code runs.

### Likely cause
- The current environment only has the base package and not the optional dependency needed by that workflow.

### Recovery
- Install only the dependency required by the workflow you are using.
- For video readers, check the PyAV/decord split in the data reference.
- For CLIP, check the tokenizer files and `torchtext`/`ftfy` support.
- For CoreML, remember that the full deployment path is optional and may require macOS.

## CUDA and DDP problems

### Symptom
- `We need CUDA for training on GPUs.`
- Rank or world-size mismatch warnings.
- Distributed training starts but uses the wrong number of workers.

### Likely cause
- The requested GPU count is not available, or the DDP settings do not match `CUDA_VISIBLE_DEVICES`.

### Recovery
- Confirm the backend with `scripts/check_install.py`.
- Match `--ddp.rank`, `--ddp.world-size`, and `CUDA_VISIBLE_DEVICES` to the visible GPUs.
- For a CPU smoke run, use a config and wrapper invocation that leaves the GPU count at zero.

## Conversion and profiling problems

### Symptom
- CoreML conversion fails or emits a warning about scikit-learn support.
- Benchmark or loss-landscape runs are slow or noisy.

### Likely cause
- CoreML is an optional/macOS-sensitive path, and benchmark parameters are too large for a quick check.

### Recovery
- Treat full deployment validation as optional unless the user explicitly asks for it.
- Use a tiny benchmark configuration first.
- If a model is not exportable, fall back to the training/model sub-skills and confirm the exportable path before retrying.

## When to switch sub-skills

- Training, finetuning, resume, evaluation, or checkpoint questions: use `sub-skills/training-and-evaluation`.
- Model-family choice or registry debugging: use `sub-skills/models-and-architectures`.
- Config, sampler, dataset, tokenization, or modality-layout issues: use `sub-skills/data-and-config`.
- CoreML, benchmark, or loss-landscape issues: use `sub-skills/conversion-and-profiling`.
