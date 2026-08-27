---
name: "data-preparation"
description: "Routes HunyuanVideo-I2V latent-extraction and metadata-validation
  tasks for LoRA training, including the raw-video schema, bucket/stride rules,
  and the processed JSON and .npy layout."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Data Preparation

Use this sub-skill when the user wants to extract VAE latents from raw videos, validate the raw metadata list, or inspect the processed dataset layout that LoRA training consumes.

## What Belongs Here

- `hyvideo/hyvae_extract/` latent extraction.
- Raw `meta_file.list` + caption JSON validation.
- Processed `json_path/*.json` + `.npy` validation.
- Bucket size, aspect-ratio, and stride behavior.
- Optional text-encoder/tokenizer asset-prep notes when they affect the extraction setup.

## What Does Not Belong Here

- Training a LoRA. Use [`../lora-training/SKILL.md`](../lora-training/SKILL.md).
- Running image-to-video sampling. Use [`../inference/SKILL.md`](../inference/SKILL.md).

## Read First

- [`references/workflows.md`](references/workflows.md) for the extraction flow and the bucket-size guidance.
- [`references/data-formats.md`](references/data-formats.md) for the raw and processed schemas.
- [`references/troubleshooting.md`](references/troubleshooting.md) for decord, metadata, cache, and VAE issues.
- [`../../references/checkpoints.md`](../../references/checkpoints.md) because extraction needs the VAE checkpoint tree.

## Bundled Scripts

- [`scripts/check_dataset_layout.py`](scripts/check_dataset_layout.py) — validate raw or processed dataset structure. This helper lives in the generated skill; invoke it from the real checkout root with an explicit `$SKILL_ROOT` path.
- [`scripts/run_hyvae_extract.py`](scripts/run_hyvae_extract.py) — print or execute the canonical multi-GPU extraction command safely; pass `--repo-root` as the checkout containing `hyvideo/`.

## Typical Workflow

All executable commands below are run from the checkout root. The generated-skill helper path is `$SKILL_ROOT/sub-skills/data-preparation/scripts`, while the source config path is `$CHECKOUT_ROOT/hyvideo/hyvae_extract/vae.yaml`.

1. Validate the raw metadata with `check_dataset_layout.py --mode raw`.
2. Confirm the VAE checkpoint tree with `check_checkpoint_layout.py --mode extraction`.
3. Print the extraction launcher with `run_hyvae_extract.py --repo-root "$CHECKOUT_ROOT" --config "$CHECKOUT_ROOT/hyvideo/hyvae_extract/vae.yaml" --dry-run`.
4. Execute only after the metadata and checkpoint checks are clean.
5. Validate the processed latent JSON directory with `check_dataset_layout.py --mode processed` before handing it to training.

## Constraints to Remember

- The raw metadata list contains one JSON path per line.
- Each raw JSON needs a `video_path` and `raw_caption.long caption` field.
- The processed output must contain `.npy` latents and a sibling `json_path/` directory.
- `use_stride` increases stride to 2 for fps >= 50.
- `enable_multi_aspect_ratio` assumes a square `sample_size` seed and uses the selected bucket list.
