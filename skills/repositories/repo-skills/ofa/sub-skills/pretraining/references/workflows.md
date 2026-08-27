# Pretraining Workflows

## Purpose

Use this page when you need to prepare or reason about OFA multimodal pretraining.

## What pretraining uses

- `vision_language_examples.tsv`
- `text_examples.tsv`
- `image_examples.tsv`
- `detection_examples.tsv`
- `negative_sample/` containing `all_captions.txt`, `object.txt`, and `type2ans.json`

## Workflow shape

1. Prepare the four TSV families.
2. Confirm the negative-sample directory.
3. Decide whether the run will restore from a checkpoint or start from scratch.
4. Launch the task with the pretraining script and the correct selected columns.

## Important considerations

- Continuous pretraining is the recommended path when a pretrained checkpoint is available.
- The `unify_task` pretraining path mixes vision-language, text, image, and detection examples.
- The data bundle is small enough to validate structurally, but not small enough to ignore selected columns.

## Use the validator first

Run `scripts/validate_pretraining_inputs.py` before a GPU job. It checks row widths, image decoding, integer-code fields, and the negative-sample folder.

## Common decisions

- If the checkpoint exists and is compatible, restore it.
- If the checkpoint is missing, make the scratch-vs-restore choice explicit before launch.
- If any TSV is missing, do not launch the job yet; fix the workspace layout first.
