# Training Troubleshooting

## No Data Was Specified

Symptom:

```text
At least one train, validation, ImageNet, or audio zero-shot dataset must be specified.
```

Fix:

- For training, pass `--train-data` or use `--dataset-type synthetic` / `synthetic-audio`.
- For eval-only, pass `--val-data`, `--imagenet-val`, `--imagenet-v2`, or an audio zero-shot dataset.
- If `--dataset-type auto` cannot infer the type, pass `--dataset-type csv`, `webdataset`, or another explicit type.

## CSV Columns Or Separator Are Wrong

Symptoms:

- pandas `KeyError` for `filepath`, `title`, or the selected keys.
- Every row appears malformed.
- Image paths are in a column but OpenCLIP cannot find it.

Fix:

```bash
python sub-skills/training/scripts/validate_csv_dataset.py DATA/train.tsv --separator tab --image-key filepath --caption-key title
```

Then mirror the selected keys in training:

```bash
--dataset-type csv --csv-separator $'\t' --csv-img-key filepath --csv-caption-key title
```

Remember that defaults are tab, `filepath`, and `title`, not comma, `image`, and `caption`.

## Numeric Captions

Symptom:

- Captions are integers/floats, or validation warns that caption values are numeric.

Explanation:

OpenCLIP stringifies captions with `str(caption)` before tokenization, so numeric captions do not crash by themselves. They often indicate the wrong caption column was selected.

Fix:

- Validate the file with `validate_csv_dataset.py`.
- If numeric captions are intended labels, convert them to natural-language captions or route to an evaluation/classification workflow instead of contrastive caption training.

## Missing Images

Symptoms:

- `FileNotFoundError` from `Image.open(...)`.
- CSV validation reports missing image paths.

Fix:

- Use absolute image paths in the CSV, or run training from the directory that makes relative paths valid.
- Check for accidental header rows, whitespace, URL strings, or unexpanded shell variables inside the CSV.
- Use the validator's `--base-dir` when previewing relative-path behavior.

## WebDataset Needs Train Sample Count

Symptom:

```text
Currently, the number of dataset samples must be specified for the training dataset. Please specify it via --train-num-samples if no dataset length info is present.
```

Fix:

```bash
--dataset-type webdataset --train-data 'DATA/shards/{000000..000999}.tar' --train-num-samples 1000000
```

For `--dataset-resampled`, choose an epoch size appropriate to your desired training cadence rather than necessarily the full dataset size.

## WebDataset Shards Too Few

Symptom:

```text
number of shards must be >= total workers
```

Fix:

- Ensure `num_shards >= --workers * world_size` for non-resampled training.
- Reduce `--workers`, reduce distributed world size, add more shards, or use `--dataset-resampled` when appropriate.

## Upsampling Factors Rejected

Symptom:

```text
--train_data_upsampling_factors is only supported when sampling with replacement (with --dataset-resampled).
```

Fix:

```bash
--dataset-resampled --train-data 'A::{B}' --train-data-upsampling-factors '1::2'
```

Ensure factor count matches the `::` source count.

## Dict Versus Tuple Batches

Symptoms:

- Custom code expects `(images, texts)` from a dataloader.
- `KeyError` or unpacking failures in downstream code.

Fix:

Task-era loaders emit dict batches:

```python
image = batch["image"]
text = batch["text"]
```

For CLAP:

```python
audio = batch["audio"]
text = batch["text"]
```

Task objects still accept positional image/text calls for compatibility, but dataloaders should be consumed by key.

## Variable Text And `text_valid`

Symptoms:

- Variable-length captions produce shape mismatches.
- A model or tokenizer lacks a `pad_token_id`.
- `torch.compile` recompiles frequently due to changing text lengths.

Fix:

- Use a variable-text-capable model/tokenizer with a reserved pad token.
- Expect `batch["text_valid"]` with right-padded captions.
- Use `--text-pad-multiple 16` or `32` to bound distinct sequence lengths.
- Use `--length-bucketing` to group similar caption lengths in training.
- Route NaFlex and generative token-budget details to `../naflex-generative/SKILL.md`.

## FSDP Ignored Or Checkpoint Mode Changed

Symptoms:

- Warning that `--fsdp` requires distributed mode.
- Warning that sharded checkpointing requires FSDP and falls back to full.

Fix:

- Launch with distributed training, usually `torchrun --nproc_per_node N -m open_clip_train.main ...`.
- Use `--fsdp --fsdp-checkpoint sharded` together.
- For single-process smoke tests, omit FSDP.

## Compile Step Strategy Fails

Symptom:

```text
--torchcompile-strategy step requires --accum-freq 1 and a precision without GradScaler.
```

Fix:

- Set `--accum-freq 1`.
- Use default `--precision amp_bf16` or `--precision fp32` instead of `--precision amp`.
- If gradient accumulation or fp16 AMP is required, switch to `--torchcompile-strategy task` or `model`.

## Compile With DDP, Grad Checkpointing, Or Dynamic Shapes

Symptoms:

- Dynamo/Inductor graph-splitting errors.
- Recompiles or symbolic-shape failures with GenLIP-like dynamic rows.

Fix:

- Prefer `--torchcompile-strategy task` first.
- For DDP with grad checkpointing or GenLIP dynamic shapes, the trainer disables DDP's dynamo optimizer automatically.
- Use `--text-pad-multiple` and, for NaFlex audio/image, route padding and token-budget tuning to `../naflex-generative/SKILL.md`.

## Distillation Constraints

Symptoms:

- Assertion around `--accum-freq`.
- CoCa or CLAP distillation fails.

Fix:

- Provide both `--distill-model` and `--distill-pretrained`.
- Keep `--accum-freq 1`.
- Do not combine distillation with CoCa.
- CLAP distillation is not supported in the task factory.

## CoCa Loss Looks Wrong

Symptoms:

- Caption labels appear shifted unexpectedly.
- Custom loop double-shifts CoCa labels.

Fix:

`CoCaTask` owns the autoregressive shift: logits are sliced to `[:, :-1]` and labels to `batch["text"][:, 1:]`. Do not also shift inside the model or an external loop unless replacing the task logic entirely.

For caption-only fine-tuning, use:

```bash
--coca-contrastive-loss-weight 0 --coca-caption-loss-weight 1
```

## Remote Sync And Latest Resume

Symptoms:

- `save-most-recent` with `remote-sync` and `resume latest` is rejected.
- `remote-sync-protocol fsspec` with latest resume is rejected.
- Latest checkpoint on remote is stale.

Fix:

- Avoid combining `--resume latest`, `--remote-sync`, and `--save-most-recent`.
- Use `--remote-sync-protocol s3` for latest resume from a remote path.
- Prefer explicit checkpoint paths when recovering from uncertain remote sync state.
- Remember background sync can lag behind local checkpoint creation.

## Checkpoint Prefix Or Shape Quirks

Symptoms:

- Keys start with `module.` when loading non-distributed.
- `logit_scale` or `logit_bias` shape differs between scalar and `[1]`.

Fix:

- Use task checkpoint utilities through the training stack; they strip `module.` when appropriate and reconcile scalar shapes across DDP/FSDP.
- If the problem is inference-only checkpoint conversion/export, route to `../evaluation-conversion/SKILL.md`.

## Optional Dependencies Missing

Symptoms:

- `wandb`, `trackio`, `tensorboard`, `bitsandbytes`, `timm`, `webdataset`, `torchaudio`, or audio packages are missing.

Fix:

- Disable the optional feature when doing a smoke run, such as leaving `--report-to ''`.
- Install only the extras needed for the selected workflow.
- Route CLAP audio optional dependency details to `../audio-clap/SKILL.md`.
- For int8 training, `--use-bnb-linear` is experimental and requires bitsandbytes/triton-compatible installs.

## Torch Or CUDA Precision Problems

Symptoms:

- bfloat16 unsupported on older GPUs.
- fp16 training instability.
- CPU run fails with CUDA default device.

Fix:

- For CPU smoke tests, pass `--device cpu` and keep batches tiny.
- For older GPUs, try `--precision amp` or `fp32` if bfloat16 is unsupported.
- Treat raw `--precision fp16` as risky for training; prefer AMP modes.
- Under FSDP, remember mixed precision is handled by FSDP policy, not autocast.

## Legacy Main Missing Feature

Symptoms:

- Legacy command cannot use CLAP audio, NaFlex, FSDP2, length bucketing, or task/step compile.

Fix:

- Port the command to `python -m open_clip_train.main` when using task-era features.
- Keep `legacy_main` only for older image/text scripts that need decode-first loader compatibility.
