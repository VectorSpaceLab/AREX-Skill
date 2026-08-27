---
name: data-preparation
description: "Routes ALAE dataset preparation, TFRecord layout validation,
  sample-image setup, style-mixing image layout, and face-alignment workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# ALAE Data Preparation

Use this sub-skill when a task asks for ALAE data inputs: TFRecord conversion or splitting, config dataset paths, sample-image directories, style-mixing `src`/`dst` image folders, or face alignment for FFHQ/CelebA-style inputs.

## Route by request

- **Validate a config or checkout layout first:** read [data-layouts](references/data-layouts.md), then run `scripts/validate_alae_data_layout.py` against the user's config. This is the safest first step before training, reconstruction, style mixing, or metrics.
- **Prepare TFRecords:** read [TFRecord preparation](references/tfrecord-preparation.md). The original dataset scripts are TensorFlow 1.x, raw-data dependent, and often large or network-bound; treat commands there as explicit, checkout-root operations.
- **Align face images:** read [face alignment](references/face-alignment.md), then use `scripts/align_faces_alae.py` with explicit `--input-dir`, `--output-dir`, and `--predictor` paths.
- **Debug data errors:** read [troubleshooting](references/troubleshooting.md) for TensorFlow 1.x API failures, `PYTHONPATH` issues, missing dlib predictors, stale `/data/datasets` assumptions, disk/network side effects, and malformed style/sample layouts.

## Boundaries

- This sub-skill owns dataset paths from ALAE configs: `DATASET.PATH`, `DATASET.PATH_TEST`, `PART_COUNT`, `PART_COUNT_TEST`, `SAMPLES_PATH`, `STYLE_MIX_PATH`, `MAX_RESOLUTION_LEVEL`, and `OUTPUT_DIR` as they affect data readiness.
- Route full training launches and checkpoint interpretation to the training sub-skill (`../training/SKILL.md`).
- Route pretrained model downloads, generation, reconstruction, and style-mixing execution to the generation sub-skill (`../generation/SKILL.md`) after this sub-skill validates input layouts.
- Route FID/PPL/LPIPS metric execution to the metrics sub-skill (`../metrics/SKILL.md`) after TFRecords and paths are validated here.

## Safe bundled helpers

```bash
python scripts/validate_alae_data_layout.py --help
python scripts/align_faces_alae.py --help
```

Both helpers avoid network, training, and hard-coded checkout paths by default. Pass an ALAE checkout root or explicit input/output paths when validating or transforming user data.
