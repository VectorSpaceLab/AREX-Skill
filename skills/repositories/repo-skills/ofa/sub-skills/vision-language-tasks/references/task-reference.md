# Task Reference

## Caption

- Typical data file: caption TSV family.
- Selected columns used in the repo scripts: `1,4,2`.
- Main metric: CIDEr / COCO caption metrics.
- Bundled helper: `scripts/coco_caption_eval.py`.
- Common flags: `--eval-cider`, `--eval_bleu`, `--scst`, `--eval_args`.

## VQA

- Typical data file: VQA TSV family.
- Selected columns used in the repo scripts: `0,5,2,3,4`.
- Main metric: accuracy.
- Modes: all-candidate evaluation, beam-search evaluation, unconstrained/open-ended training, and zero-shot variants.
- Common sidecar file: `trainval_ans2label.pkl` or an equivalent answer dictionary.
- Common flags: `--beam-search-vqa-eval`, `--unnormalized`, `--temperature`, `--val-inference-type`.

## RefCOCO / RefCOCO+ / RefCOCOg

- Typical data file: RefCOCO TSV family.
- Selected columns used in the repo scripts: `0,4,2,3`.
- Main metric: accuracy from bounding-box overlap.
- Common flags: `--beam`, `--min-len`, `--max-len-b`, `--no-repeat-ngram-size`.
- Prompt tuning, adapters, and bitfit variants are usually routed from the refcoco scripts.

## SNLI-VE

- Typical data file: SNLI-VE TSV family.
- Selected columns used in the repo scripts: `0,2,3,4,5`.
- Main metric: accuracy / `snli_score`.
- Common flags: `--prompt-type`, `--add-caption`, `--zero-shot` for the zeroshot route.

## OCR

- Typical data file: OCR TSV family.
- Selected columns used in the repo scripts: `0,1,2`.
- Main metric: exact-match accuracy plus normalized edit distance / NED.
- Common flags: `--max-len-b=64`, `--is-document` for document-style resizing.

## Image classification

- Typical data file: ImageNet TSV family.
- Selected columns used in the repo scripts: `0,2`.
- Main metric: top-1 accuracy.
- Common sidecar file: `class2label_new.pkl` or equivalent class mapping.

## Shared reminders

- The workflow commands usually pass `--model-overrides` to inject the task-specific data and selected columns.
- The same checkpoint often cannot be reused safely across task families without checking the task and dictionary layout.
- Always confirm the task family before copying a command from memory.
