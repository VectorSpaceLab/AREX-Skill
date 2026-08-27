# Pretraining and DeepSpeed Workflows

Use these workflows to prepare and preflight Baichuan-7B training safely. The bundled scripts validate and render commands only; they do not run training.

## Workflow 1: collect training inputs

Before validating or rendering a launch command, identify:

- Active training workspace containing the user's training entrypoint, usually a Baichuan-style `train.py`.
- Corpus directory, default `data_dir`.
- Tokenizer model, default `tokenizer.model`.
- DeepSpeed config, default `config/deepspeed.json`.
- DeepSpeed hostfile, default `config/hostfile`.
- Checkpoint output directory, default `checkpoints`.
- Whether the user expects single-node, multi-node, or placeholder-only planning.
- Whether they want a real launch or only preflight/rendering. Default to preflight/rendering.

Do not import `train.py` to inspect its parser. The source script parses arguments and initializes distributed training at import time.

## Workflow 2: prepare corpus shards

1. Split the corpus into multiple UTF-8 text files.
2. Make the number of shard files an even multiple of total DeepSpeed ranks whenever possible.
3. Keep the corpus directory flat: regular text files only, no subdirectories or generated checkpoint/log folders.
4. Balance shard sizes because file assignment is index modulo world size, not size-aware.
5. Avoid extremely short lines; the source discards lines that tokenize to fewer than 20 token IDs after EOS.
6. Remember that each rank loads its assigned shard contents into memory before training.

Run the validator from any current directory by passing explicit paths:

```bash
python /path/to/pretraining-and-deepspeed/scripts/validate_training_inputs.py \
  --data-dir /path/to/data_dir \
  --tokenizer-path /path/to/tokenizer.model \
  --deepspeed-config /path/to/config/deepspeed.json \
  --hostfile /path/to/config/hostfile \
  --checkpoint-saving-path /path/to/checkpoints
```

If the hostfile is not ready but the expected rank count is known:

```bash
python /path/to/pretraining-and-deepspeed/scripts/validate_training_inputs.py \
  --data-dir /path/to/data_dir \
  --tokenizer-path /path/to/tokenizer.model \
  --deepspeed-config /path/to/config/deepspeed.json \
  --skip-hostfile \
  --world-size 16
```

For a stronger tokenizer check when `sentencepiece` is installed:

```bash
python /path/to/pretraining-and-deepspeed/scripts/validate_training_inputs.py \
  --data-dir /path/to/data_dir \
  --tokenizer-path /path/to/tokenizer.model \
  --deepspeed-config /path/to/config/deepspeed.json \
  --hostfile /path/to/config/hostfile \
  --try-tokenizer-load
```

Interpretation:

- Exit `0`: no validation errors. Warnings may still require review.
- Exit `1`: warnings were treated as fatal because `--strict-warnings` was used.
- Exit `2`: errors were found; do not launch training until fixed.

## Workflow 3: validate DeepSpeed config and hostfile

Use `references/configuration.md` as the semantic map. The minimum launch-critical checks are:

- DeepSpeed config is valid JSON.
- `train_micro_batch_size_per_gpu` is a positive integer.
- `gradient_accumulation_steps` is a positive integer.
- Optimizer block has `type` and `params`.
- ZeRO optimization block exists; source demo uses stage 2.
- bf16/fp16 setting matches the available accelerator plan.
- Hostfile has real hostnames or IPs, not placeholders, and each runnable line has `slots=N`.
- Hostfile slot sum matches the expected total ranks.
- Corpus shard count is compatible with hostfile slot sum.

The validator reports an estimated global batch and minimum complete token IDs needed per rank before each checkpoint interval. Treat these as planning checks, not throughput validation.

## Workflow 4: render the launch command

Render a reviewed shell command without executing it:

```bash
python /path/to/pretraining-and-deepspeed/scripts/render_deepspeed_command.py \
  --hostfile /path/to/config/hostfile \
  --deepspeed-config /path/to/config/deepspeed.json \
  --train-script /path/to/train.py \
  --data-dir /path/to/data_dir \
  --tokenizer-path /path/to/tokenizer.model \
  --checkpoint-saving-path /path/to/checkpoints
```

Use `--plain` when a single shell line is desired:

```bash
python /path/to/pretraining-and-deepspeed/scripts/render_deepspeed_command.py \
  --hostfile /path/to/config/hostfile \
  --deepspeed-config /path/to/config/deepspeed.json \
  --train-script /path/to/train.py \
  --plain
```

The rendered command follows the source launcher shape:

```bash
deepspeed --hostfile HOSTFILE --force_multi TRAIN_SCRIPT --deepspeed --deepspeed_config DEEPSPEED_JSON ...
```

The renderer adds explicit `--data_dir`, `--tokenizer_path`, `--max_length`, `--steps_per_epoch`, and `--checkpoint_saving_path` arguments unless `--omit-default-train-args` is passed. It does not verify that the runtime environment can actually allocate 7B training memory.

## Workflow 5: decide whether a real launch is appropriate

Only consider executing the rendered command after all are true:

- The user explicitly requests a real training run.
- GPU/cluster resources match the hostfile and precision config.
- DeepSpeed and pinned or compatible CUDA packages are installed in the active runtime.
- The tokenizer and corpus pass preflight checks.
- Checkpoint and log directories are writable and kept separate from data shards.
- The user understands that the source training loop runs indefinitely over epochs, saving checkpoints after each `steps_per_epoch` interval.

If any condition is missing, stop at a preflight report and explain the blocker.

## Workflow 6: understand checkpoint outputs

The source training loop does:

```text
while True:
  train(... steps_per_epoch ...)
  epoch += 1
  model_engine.save_checkpoint(checkpoint_saving_path, tag=f"Epoch-{epoch}")
```

Expect checkpoint tags such as `Epoch-1`, `Epoch-2`, and so on under the checkpoint root. DeepSpeed usually writes rank-partitioned model/optimizer state and may write a `latest` marker. Exact filenames depend on DeepSpeed version and ZeRO stage. Because the loop is infinite, production runs need external job limits, monitoring, or manual termination criteria.

## Workflow 7: troubleshoot a failed launch

Use `references/troubleshooting.md` first. Common quick routes:

- `FileNotFoundError` for tokenizer or data: rerun validator with explicit paths.
- `JSONDecodeError` or missing config key: fix DeepSpeed JSON before launch.
- DeepSpeed cannot parse hostfile or SSH workers: replace placeholder hostfile and confirm connectivity outside this skill.
- CUDA or bf16 failure: use a compatible GPU environment; CPU-only checks do not validate full training.
- `IndexError: pop from empty list` in data loading: corpus did not yield enough complete token chunks for at least one rank.
