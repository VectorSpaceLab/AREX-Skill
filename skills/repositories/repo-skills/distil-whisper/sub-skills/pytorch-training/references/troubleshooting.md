# PyTorch Training Troubleshooting

## Purpose

Read this when pseudo-labelling, student initialization, distillation, or evaluation fails in the PyTorch stack.

## Common issues

### `No module named 'soundfile'`

- **Symptoms:** `training/run_pseudo_labelling.py` fails before showing help or parsing args.
- **Likely cause:** the audio stack is incomplete.
- **Recovery:** install `soundfile` and re-run the check.

### Dataset column or split mismatches

- **Symptoms:** a dataset loads but the script errors on the text, id, or split columns.
- **Likely cause:** the command does not match the dataset schema in the README example.
- **Recovery:** verify `--text_column_name`, `--id_column_name`, `--dataset_split_name`, and any `+`-separated multi-dataset lists.

### `accelerate launch` or distributed configuration fails

- **Symptoms:** the distillation script starts but errors before training.
- **Likely cause:** `accelerate config` was not run or the launch settings do not match the available hardware.
- **Recovery:** configure Accelerate first, then retry with a tiny smoke command before the full job.

### Hub push or login failures

- **Symptoms:** a command that should push to the Hub fails with an auth error.
- **Likely cause:** missing `huggingface-cli login`, a gated dataset was not accepted, or the target repo cannot be created.
- **Recovery:** log in to the Hub and retry with a smaller public example before using a real training run.

### WER or label-quality issues

- **Symptoms:** training quality is poor, pseudo labels are noisy, or the evaluation looks worse than expected.
- **Likely cause:** the teacher hallucinated, timestamps were omitted, or the WER filter is too permissive.
- **Recovery:** enable timestamped pseudo labels, lower the beam size for faster pseudo-labelling, and keep the WER filter in the distillation loop.

### CPU smoke works but the intended speed path is missing

- **Symptoms:** the command runs, but the user expected a GPU-specific speedup or bf16 path.
- **Likely cause:** the inspection env uses CPU wheels only.
- **Recovery:** treat the CPU result as a correctness check only, then move to a GPU-capable env if the user explicitly needs speed coverage.

## Read next

- Use `../../references/model-overview.md` to choose the teacher or student checkpoint.
- Use `../../scripts/check-env.py` before attempting another install or smoke run.
