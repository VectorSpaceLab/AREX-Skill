# Evaluation layout

## Prompt inputs
- COCO prompts: `evaluations/t2i/coco_captions.csv`
- Parti prompts: `evaluations/t2i/PartiPrompts.tsv`
- The Python sampler reads the `Prompt` column.

## Sampling output layout
The DDP sampler writes a sample directory that contains:
- `images/000000.png`, `images/000001.png`, ...
- `result.jsonl`
- `captions.txt`

## Evaluation input layout
`evaluations/t2i/evaluation.py` expects:
- `--fake_dir` pointing at the sample directory.
- `--ref_dir` pointing at the dataset root.
- `--ref_data coco2014` when using COCO reference batches.
- `--ref_type val2014` or another matching reference split.

## Metrics
The evaluator reports CLIP score and FID-style statistics depending on the reference data mode and selected backends.

## Practical checks
- Confirm the prompt file has the expected column before starting a large sample job.
- Confirm the sample directory already has an `images/` subfolder before launching evaluation.
- Keep generated captions and prompt files next to the sample batch so the evaluator can find them.
