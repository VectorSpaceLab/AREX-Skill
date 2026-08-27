# Model Troubleshooting

## Purpose

Read this when `get_model`, pretrained loading, or `model.info()` fails after the config and task category already look plausible.

## Unknown or reserved model name

### Symptom
- `For <category> task, model name can't be __base__`
- Unknown model-family error from the registry.

### Cause
- The task category is right, but the family name is not a concrete registered model.

### Recovery
- Compare the desired family name against `references/model-overview.md`.
- Check the config key `model.<category>.name` rather than guessing at a source-folder name.

## Pretrained head mismatch

### Symptom
- The checkpoint loads but the head or class count is wrong.
- Detection or segmentation weights appear to fit the backbone but not the final outputs.

### Cause
- The checkpoint belongs to a different task head or class count.

### Recovery
- Reconfirm the task family, the dataset category, and the class-count argument.
- Use finetuning or a matching head configuration instead of forcing the checkpoint into the wrong head.

## Tokenizer or byte-encoding problems

### Symptom
- CLIP or ByteFormer fails before the model can run.
- The model build wants missing tokenizer files, byte settings, or prompt-related inputs.

### Cause
- Multimodal or byte-based families depend on extra files and config settings outside the pure image backbone.

### Recovery
- Inspect the data/config path for tokenizer and byte-encoding keys.
- Verify that the recipe includes the expected merges, encoder JSON, or byte-save settings.

## Missing optional model helpers

### Symptom
- `model.info()` or FLOP-related logic fails.
- Exportability checks are unavailable.

### Cause
- An optional helper such as `fvcore` or an export-specific dependency is not installed.

### Recovery
- Treat the helper as optional unless the user explicitly asked for it.
- Use the build-only smoke first, then add the missing dependency only if the workflow needs it.

## Exportability problems

### Symptom
- The model cannot be exported by the CoreML path.
- A conversion or JIT step fails even though the training model works.

### Cause
- The family does not expose an exportable representation, or the export path expects different preprocessing.

### Recovery
- Confirm whether the family exposes `get_exportable_model()`.
- If not, switch to the conversion sub-skill for the exact export contract and limitations.

## When to stop and switch

- If the error is really about YAML keys, dataset roots, or tokenizer paths, switch to `data-and-config`.
- If the error is really about a training/eval wrapper, switch to `training-and-evaluation`.
- If the error is really about export or profiling, switch to `conversion-and-profiling`.
