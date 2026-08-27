# CLI Troubleshooting

Use this when timm train/validate/inference commands fail before entering deeper model, data, or training internals.

## Script Is Missing

Symptom: `python: can't open file 'train.py'`, `validate.py` not found, or `distributed_train.sh` not found.

Cause: the root scripts are reference scripts in the repository checkout and are not guaranteed to be packaged in pip releases.

Fix:

- Run from a checkout containing the root scripts.
- Copy the needed scripts into the working project and run those copies.
- Replace `./distributed_train.sh N ...` with `torchrun --nproc_per_node=N train.py ...` when only the shell wrapper is missing.

## Dataset Path or Split Is Wrong

Symptoms: empty dataset, class-folder errors, file-not-found errors, or unexpectedly zero samples.

Fix by workflow:

| Workflow | Correct path pattern |
| --- | --- |
| Training | `--data-dir` is the base containing `train/` and `validation/` unless `--train-split`/`--val-split` are changed. |
| Validation | `--data-dir` commonly points directly to the validation folder for ImageFolder use. |
| Inference | `--data-dir` points to the image folder/dataset split to score. |

For non-ImageFolder backends, also check `--dataset`, split names, download permissions, sample counts, and remote-code trust choices.

## CUDA Defaults on CPU Hosts

The scripts default `--device cuda`. On CPU-only hosts this can fail even for helpfully small examples.

Fix:

```bash
python validate.py --data-dir ./validation --model resnet18 --pretrained --device cpu --batch-size 4 --workers 0
```

Only add `--amp` when the selected device and dtype support autocast. For CPU debug commands, omit `--amp` unless the user specifically wants bfloat16 autocast testing and understands the host support.

## Pretrained Download Failures

Symptoms: network, cache, authentication, or missing-weight errors after `--pretrained` or implicit pretrained fallback.

Relevant behavior:

- `validate.py` and `inference.py` set pretrained automatically when no `--checkpoint` is provided.
- `train.py --pretrained` starts from available pretrained weights; `--pretrained-path` overlays a local pretrained-style file.
- `--checkpoint` loads an explicit checkpoint for validation/inference; `--initial-checkpoint` initializes training from model weights; `--resume` resumes full training state.

Fix: use a local checkpoint/pretrained path when offline, choose a model variant that actually has weights, or remove pretrained expectations for scratch/debug runs.

## Class Map and Result File Errors

Symptoms: class index mismatch, label names missing, result output path failures, or unexpected result extensions.

Fix:

- Ensure `--class-map` matches dataset classes and model class count.
- Create parent directories for `validate.py --results-file`; validation writes directly to the path.
- For inference, prefer `--results-dir DIR --results-file STEM`; the script creates `--results-dir` and appends the extension for each `--results-format`.
- For inference labels, use `--label-type none` when ImageNet label inference is not appropriate.
- `inference.py` imports pandas at startup for result writing, so even `--help` requires `pandas` in the environment; install it or use the bundled command builder for command-only planning.
- If `--results-format parquet` fails, install the pandas parquet backend required by the environment or choose CSV/JSON.

## DDP Launch and `local_rank`

Symptoms: DDP startup hangs, rank/device errors, or confusion about `--local_rank`.

Fix:

- Prefer `torchrun --nproc_per_node=N train.py ...`.
- Match `N` to visible GPUs for single-node CUDA DDP.
- Pass rendezvous options for multi-node runs and verify network/firewall setup.
- Do not manually assign `--local_rank` for normal modern `torchrun`; the launcher sets rank metadata.
- Avoid mixing training DDP with validation/inference `--num-gpu` DataParallel patterns.

## NaFlex Loader and Model Mismatch

Symptoms: shape assertions, missing patch-size methods, sequence length errors, or patchify layout mismatch.

Fix:

- Use `--naflex-loader` only with NaFlex-compatible models or with model kwargs such as `--model-kwargs use_naflex=True` when supported.
- Match train/validation sequence flags: `--naflex-train-seq-lens ...` for training and `--naflex-max-seq-len N` for validation.
- If using variable patch sizes, include compatible model kwargs such as `enable_patch_interpolator=True` and keep `--naflex-patch-size-probs` length equal to `--naflex-patch-sizes`.
- Use `--naflex-patchify-channels-first` only for models expecting channels-first flattened patches.
- Disable augmentation split recipes with NaFlex unless the script explicitly supports the requested combination; training asserts that augmentation splits are not supported in NaFlex mode.

## OOM and Batch Retry

Validation supports `--retry`, which catches recognized batch-size-related runtime errors, reduces batch size, and retries. It is most useful for single-model validation.

Training and inference do not have the same general retry loop. For memory failures:

- Reduce `--batch-size` or `--validation-batch-size`.
- Use `--amp` on supported CUDA hosts.
- Use `--grad-accum-steps` during training to preserve effective batch size.
- Reduce `--img-size`, `--input-size`, `--topk`, heavy augmentation, or model size.
- For DDP, remember memory is controlled by per-process batch size.

## Config and Flag Parsing Issues

Training parses `--config` first and uses YAML values as parser defaults. If a YAML key has the wrong argparse destination name, it may be ignored or fail depending on parser behavior. Validation and inference do not use this config mechanism.

When using a command builder or shell variables, pass multi-token flags exactly as the target parser expects, for example:

```bash
--input-size 3 224 224
--model-kwargs use_naflex=True enable_patch_interpolator=True
--results-format csv json
```
