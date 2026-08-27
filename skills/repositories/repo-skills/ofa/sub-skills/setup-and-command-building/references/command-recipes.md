# Command Recipes

## Purpose

Use this reference when you need a copyable OFA launch shape but do not want to hand-edit a long shell script.

## Shared pattern

Most OFA workflows follow this structure:

```bash
cd <ofa-skill-root>
python scripts/render_ofa_command.py \
  --mode evaluate \
  --repo-root . \
  --task <task-name> \
  --data <dataset.tsv> \
  --path <checkpoint.pt> \
  --user-dir ofa_module \
  --bpe-dir utils/BPE \
  --selected-cols <col-list> \
  --results-path <results-dir> \
  --beam <beam-size>
```

For training, switch `--mode train` and use `--save-dir`, `--criterion`, `--arch`, `--lr`, `--max-epoch`, and `--update-freq` as needed.

## Common command facts

- `--user-dir=ofa_module` is the OFA registration hook used by almost every workflow.
- `--selected-cols` must match the task family and the row shape of the TSV.
- `--model-overrides` is used heavily for evaluation because the checkpoint often needs a data-specific override.
- The repo's shell scripts usually pick a task-specific `MASTER_PORT` and GPU list; change those when running multiple jobs on one host.

## Helpful patterns by workflow family

### Caption / VQA / RefCOCO / SNLI-VE / OCR / ImageNet

- Use `evaluate.py` for inference and task-specific metrics.
- Keep the checkpoint and dataset from the same workflow family.
- Use the relevant selected columns and keep the task name aligned with the dataset layout.

### Pretraining

- Use `train.py` with a mixed TSV input, negative-sample directory, and the pretraining task.
- Treat the restore checkpoint as optional continuous-pretraining state.
- Validate the workspace layout before the first launch.

### Gigaword / GLUE

- These are seq2seq classification or summarization runs.
- Their data rows are much smaller, but the same `train.py` / `evaluate.py` launch pattern still applies.

### MMSpeech

- Pass the speech/text manifest and fbank config through the task overrides.
- Check the phone dictionary and sample rate before launch.

## When to use the renderer

Use `scripts/render_ofa_command.py` when you need to:

- keep the command copyable,
- avoid hard-coded local paths,
- swap from one task family to another,
- or generate a variant without copying shell syntax from the original repo.
