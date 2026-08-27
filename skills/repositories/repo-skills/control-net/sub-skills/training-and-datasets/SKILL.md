---
name: training-and-datasets
description: "Prepare, validate, adapt, and troubleshoot ControlNet training
  datasets and tutorial training workflows for SD1.5 and SD2.1."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ControlNet Training And Datasets

Use this sub-skill when the task is about preparing a ControlNet training dataset, validating Fill50K-style rows, writing a custom PyTorch `Dataset`, adapting the tutorial training pattern for SD1.5 or SD2.1, tuning training knobs, or debugging dataset/training startup failures.

Do not use this sub-skill for image-generation UI workflows, checkpoint-conversion internals, or detector preprocessing. Route those requests to:

- Initial ControlNet checkpoint creation and model/config architecture: [model-and-weight-utilities](../model-and-weight-utilities/SKILL.md).
- Detector-generated control maps and preprocessing pipelines: [annotators-and-preprocessing](../annotators-and-preprocessing/SKILL.md).
- Gradio inference apps and qualitative generation tests: [gradio-inference-apps](../gradio-inference-apps/SKILL.md).

## Fast Routing

- Validate Fill50K or a Fill50K-like dataset before training with the bundled validator; it checks `prompt.json`, row keys, image paths, image readability, shape consistency, and tutorial normalization ranges without importing ControlNet or starting training.
- Author custom datasets by matching the ControlNet data contract: `jpg` is the RGB target image normalized to `[-1, 1]`, `hint` is the RGB control/source image normalized to `[0, 1]`, and `txt` is the prompt string.
- Adapt SD1.5 training with `models/cldm_v15.yaml` and an initialized `control_sd15_ini.ckpt`; adapt SD2.1 training with `models/cldm_v21.yaml` and an initialized `control_sd21_ini.ckpt` or equivalent.
- Start with conservative training knobs (`batch_size=1` to `4`, `learning_rate=1e-5`, `sd_locked=True`, `only_mid_control=False`) and add gradient accumulation or low-VRAM mode only after the dataset and checkpoint load cleanly.
- Treat full tutorial imports/runs as unsafe preflight checks: they require data, checkpoints, GPU memory, and may trigger model/tokenizer downloads.

## Bundled References And Tools

- Read [dataset-format.md](references/dataset-format.md) when validating Fill50K layout, writing a custom `Dataset`, checking `prompt.json` schema, or confirming `jpg`/`txt`/`hint` ranges.
- Read [training-workflows.md](references/training-workflows.md) when adapting the SD1.5 or SD2.1 tutorial training pattern, choosing configs/checkpoints, setting knobs, or planning low-memory runs.
- Read [troubleshooting.md](references/troubleshooting.md) when a dataset, checkpoint, CUDA, Lightning, CLIP, or low-VRAM issue blocks training startup.
- Run [validate_fill50k_dataset.py](scripts/validate_fill50k_dataset.py) for safe dataset preflight checks or to create a tiny local fixture that demonstrates the expected Fill50K structure.

## Safe Validation Command

From any working directory, point the validator at the dataset root that contains `prompt.json`, `source/`, and `target/`:

```bash
python path/to/training-and-datasets/scripts/validate_fill50k_dataset.py --dataset-root path/to/training/fill50k --max-items 100
```

Use `--max-items 0` for a full scan before a long training job. Use `--write-example-fixture path/to/tmp-fill50k --validate-written-fixture` to create and validate a tiny self-contained fixture without network access, checkpoint loading, image generation, or training.
