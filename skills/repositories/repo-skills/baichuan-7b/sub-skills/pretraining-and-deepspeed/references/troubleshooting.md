# Pretraining and DeepSpeed Troubleshooting

This guide maps common Baichuan-7B pretraining failures to safe checks. Prefer the bundled scripts before launching DeepSpeed:

- `../scripts/validate_training_inputs.py` for corpus/tokenizer/config/hostfile/checkpoint layout.
- `../scripts/render_deepspeed_command.py` for launch command rendering.

## Safety first

Do not import the original `train.py` just to inspect it. The source module builds an argument parser, calls `deepspeed.add_config_arguments`, parses process arguments, and initializes distributed DeepSpeed at module import time. Treat it as a process entrypoint.

## Missing `tokenizer.model`

Typical symptoms:

- `OSError`, `RuntimeError`, or SentencePiece load failure near `sp.Load(tokenizer_path)`.
- Training fails before data can be tokenized.

Checks and fixes:

1. Download the Baichuan-7B `tokenizer.model` from the official model release or provide an equivalent compatible SentencePiece model.
2. Place it at the active training workspace root or pass `--tokenizer_path /absolute/path/to/tokenizer.model`.
3. Run:

```bash
python /path/to/pretraining-and-deepspeed/scripts/validate_training_inputs.py \
  --data-dir /path/to/data_dir \
  --tokenizer-path /path/to/tokenizer.model \
  --deepspeed-config /path/to/config/deepspeed.json \
  --hostfile /path/to/config/hostfile \
  --try-tokenizer-load
```

If `sentencepiece` is unavailable, the validator can still check file existence without `--try-tokenizer-load`, but that does not prove the model is loadable.

## Empty or malformed corpus directory

Typical symptoms:

- `FileNotFoundError` for `data_dir`.
- `IsADirectoryError` when a nested directory appears under the corpus directory.
- `IndexError: pop from empty list` from `DataEngine.get_data()` when a rank has no complete loaded token chunk.
- Some ranks appear idle because shard assignment is uneven.

Checks and fixes:

1. Use a flat directory of regular UTF-8 text files.
2. Make shard count a multiple of total DeepSpeed ranks.
3. Balance shard sizes; assignment is by file index modulo rank, not by byte count.
4. Remove empty files and avoid very short lines. Lines tokenizing to fewer than 20 IDs after EOS are discarded.
5. Estimate per-rank minimum token IDs for each checkpoint interval:

```text
train_micro_batch_size_per_gpu * steps_per_epoch * (max_length + 1)
```

Run the validator with a known world size if the hostfile is not ready:

```bash
python /path/to/pretraining-and-deepspeed/scripts/validate_training_inputs.py \
  --data-dir /path/to/data_dir \
  --tokenizer-path /path/to/tokenizer.model \
  --deepspeed-config /path/to/config/deepspeed.json \
  --skip-hostfile \
  --world-size 8
```

## Malformed hostfile

Typical symptoms:

- DeepSpeed hostfile parser errors.
- SSH or worker discovery failures.
- Launch uses the repository placeholder lines literally.

The source `config/hostfile` is a placeholder:

```text
[master address] slots=8
[worker address] slots=8
...
```

Replace it with real reachable hosts:

```text
node-a slots=8
node-b slots=8
```

Checks:

- Each non-comment line has one host/IP and `slots=N` with `N > 0`.
- No bracketed placeholder text remains.
- No ellipsis remains.
- Slot sum equals the intended total rank count.
- SSH/connectivity and scheduler allocation are valid outside this skill.

Use the renderer/validator to fail early on placeholders.

## Malformed DeepSpeed JSON

Typical symptoms:

- `json.JSONDecodeError`.
- `KeyError: 'train_micro_batch_size_per_gpu'` in `prepare_data()`.
- DeepSpeed optimizer or ZeRO initialization errors.

Minimum checks:

- JSON root is an object.
- `train_micro_batch_size_per_gpu` is a positive integer.
- `gradient_accumulation_steps` is a positive integer.
- `optimizer.type` and `optimizer.params` exist.
- `zero_optimization.stage` exists; source config used ZeRO stage 2.
- `bf16.enabled` or `fp16.enabled` matches hardware/runtime expectations.

Run:

```bash
python /path/to/pretraining-and-deepspeed/scripts/render_deepspeed_command.py \
  --hostfile /path/to/config/hostfile \
  --deepspeed-config /path/to/config/deepspeed.json \
  --train-script /path/to/train.py
```

If rendering fails, fix config/hostfile first. Use `--skip-validation` only for documentation previews, not launch readiness.

## Dependency pin mismatch or install failure

The repository requirements pin:

```text
deepspeed==0.9.2
numpy==1.23.5
sentencepiece==0.1.97
torch==2.0.0
transformers==4.29.1
xformers==0.0.20
```

Exact installation can fail when old package pins are unavailable for the active Python/CUDA platform. Newer PyTorch/Transformers/xFormers/SentencePiece stacks can be sufficient for source inspection or tiny smokes, but they are not proof of real DeepSpeed training compatibility.

Recovery guidance:

- For actual training, build a cluster-specific environment that can install compatible CUDA wheels and DeepSpeed build requirements.
- Do not treat CPU import success as proof that bf16 DeepSpeed training will run.
- If `xformers` or `deepspeed` builds fail, check CUDA toolkit, PyTorch CUDA ABI, compiler, and package index availability.
- If Transformers emits generation-inheritance warnings in newer versions, route model internals/inference compatibility to `../architecture-and-loading/`; training code was authored for `transformers==4.29.1`.

## Missing GPU, bf16, or cluster resources

Typical symptoms:

- CUDA unavailable or `.cuda()` failure.
- bf16 unsupported errors.
- NCCL, distributed initialization, or network timeout failures.
- Hostfile slots exceed allocated GPUs.

Recovery guidance:

1. Confirm GPU allocation and `torch.cuda.device_count()` in the actual training environment.
2. Match hostfile `slots` to allocated devices per node.
3. Confirm NCCL/network settings, firewall/SSH, scheduler allocation, and shared filesystem assumptions.
4. If the hardware does not support bf16, decide whether to switch precision deliberately and validate the changed DeepSpeed config; do not assume equivalence to the source demo.
5. For a preflight-only task, report the required resource gap instead of launching.

## Checkpoint path surprises

Typical symptoms:

- Checkpoints appear as rank-partitioned DeepSpeed files rather than a single model file.
- Training keeps running after the first checkpoint.
- Checkpoint/log files appear mixed into the data directory.

Source behavior:

```text
model_engine.save_checkpoint(checkpoint_saving_path, tag=f"Epoch-{epoch}")
```

Guidance:

- Keep `checkpoint_saving_path` separate from `data_dir`.
- Expect tags such as `Epoch-1`, `Epoch-2`, etc.
- DeepSpeed may write a `latest` marker and optimizer/model shards depending on version and ZeRO stage.
- The loop is infinite; real jobs need external stop criteria or scheduler wall-time limits.

## Accidental import of `train.py`

Typical symptoms:

- A harmless-looking Python inspection command unexpectedly parses unrelated CLI arguments.
- Distributed initialization starts or fails outside a DeepSpeed launch.
- Tests hang waiting for distributed environment variables.

Fix:

- Do not import `train.py` in tools, tests, notebooks, or validation scripts.
- Extract only static knowledge from the source and use the bundled preflight scripts.
- If you must inspect parser defaults, read this sub-skill's references or run the bundled renderer with explicit arguments.
