# Criteria and Tuning

## Prompt tuning

The repo documents prompt tuning as a set of command-line switches rather than a separate package:

- `--encoder-prompt`
- `--decoder-prompt`
- `--encoder-prompt-length`
- `--decoder-prompt-length`
- `--bitfit`
- `--adapter`
- `--adapter-dim`

These flags are usually combined with a task command such as a RefCOCO finetune or evaluation run.

## Encouraging loss

The encouraging-loss variant is implemented by `criterions/label_smoothed_encouraging_loss.py` and selected with the criterion name `adjust_label_smoothed_encouraging_loss`.

Important flag:

- `--log-end`

Guidance from the repo notes:

- values below 1 give an approximate conservative version,
- larger values strengthen the margin-growth effect but can increase gradient magnitude,
- `0.75` or `0.5` are reasonable first tries.

## Extension planning notes

- Prompt tuning, adapters, and bitfit are usually compatible with downstream finetuning tasks.
- Encouraging loss changes the optimization behavior, so keep an eye on stability and gradient scale.
- Architecture and checkpoint compatibility should be checked before mixing these options with a new task.
