---
name: data-preparation
description: "Prepare, validate, and troubleshoot sd-scripts training data
  before LoRA, fine-tuning, Textual Inversion, ControlNet, or inpainting
  training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data Preparation

Use this sub-skill when a user needs to build or debug sd-scripts dataset inputs before launching training. It covers dataset TOML files, DreamBooth directory subsets, fine-tuning metadata JSON/JSONL, captions/tags, validation splits, bucketing/resolution choices, cached latents/text-encoder outputs, and safe data sanity checks.

Route actual training commands to `../training`. Route generation prompt files to `../generation`. Route LoRA merge/convert or checkpoint utilities to `../model-utilities`.

## Fast Path

1. Decide the dataset style per `[[datasets]]` block:
   - DreamBooth: every subset has `image_dir` and no `metadata_file`.
   - Fine-tuning: every subset has `metadata_file`; `image_dir` is required when metadata paths are relative.
   - ControlNet-style paired data: every subset has `image_dir` and `conditioning_data_dir`.
2. Put shared defaults in `[general]`, dataset-level shape/batch/bucket settings in `[[datasets]]`, and directory/metadata-specific settings in `[[datasets.subsets]]`.
3. Validate the TOML and metadata before training:

```bash
python skills/sd-scripts/sub-skills/data-preparation/scripts/validate_dataset_inputs.py --dataset-config dataset_config.toml
```

4. If the config passes, use `../training` to construct the matching `accelerate launch ... --dataset_config dataset_config.toml` command.

## References

- `references/data-formats.md`: TOML structure, metadata formats, caption/tag rules, and validation split precedence.
- `references/workflows.md`: Practical data prep flows for DreamBooth, fine-tuning metadata, ControlNet/masked loss, resize/bucketing, and cache helpers.
- `references/troubleshooting.md`: Common errors and corrective actions.
- `scripts/validate_dataset_inputs.py`: Read-only local preflight for TOML, JSON/JSONL, directories, metadata paths, image presence, mixed subset modes, and likely cache-only entries.

## Safety Notes

- The bundled validator is read-only and does not load sd-scripts, model weights, VAE, CLIP, T5, BLIP, WD14, ONNX, TensorFlow, or torch.
- Cache and caption/tag generation tools can write many files or download models. Treat them as explicit user-approved preprocessing steps, not as automatic validation.
- Do not mix DreamBooth and fine-tuning subsets inside one `[[datasets]]`. Split them into separate `[[datasets]]` blocks if a training script supports both.
- Inpainting training with `--train_inpainting` needs source images at training time and is incompatible with latent caching flags.
