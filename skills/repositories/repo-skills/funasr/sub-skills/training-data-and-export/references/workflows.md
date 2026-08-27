# Training workflows

This reference is for planning and safely launching FunASR training or fine-tuning. It keeps full training out of the default path: validate data and command shape first, then ask the user before starting long runs, model downloads, or multi-GPU jobs.

## Preflight checklist

Before any training command:

1. Identify the model id or local model directory.
2. Prepare `train.jsonl` and `val.jsonl`, or a shard-list file for each split.
3. Run the bundled manifest validator.
4. Decide whether the run is a tiny smoke, a single-process CPU/GPU run, or a distributed run.
5. Decide whether checkpoint resume is desired and where `output_dir` should be written.
6. If the user provides a template config, inspect it for distributed keys and make top-level overrides explicit.

Example preflight:

```shell
python scripts/validate_manifest.py train.jsonl --check-sources --check-source-len
python scripts/validate_manifest.py val.jsonl --check-sources --check-source-len
funasr-train-ds --help
```

## Minimal command shape

For a quick command-line smoke only:

```shell
funasr-train \
  ++model=paraformer-zh \
  ++train_data_set_list=train.jsonl \
  ++valid_data_set_list=val.jsonl \
  ++output_dir=outputs/smoke
```

For the recommended DeepSpeed-capable trainer without enabling DeepSpeed:

```shell
funasr-train-ds \
  ++model="${MODEL_ID_OR_DIR}" \
  ++train_data_set_list="${TRAIN_JSONL}" \
  ++valid_data_set_list="${VALID_JSONL}" \
  ++dataset="AudioDataset" \
  ++dataset_conf.index_ds="IndexDSJsonl" \
  ++dataset_conf.data_split_num=1 \
  ++dataset_conf.batch_sampler="BatchSampler" \
  ++dataset_conf.batch_size=6000 \
  ++dataset_conf.sort_size=1024 \
  ++dataset_conf.batch_type="token" \
  ++dataset_conf.num_workers=4 \
  ++train_conf.max_epoch=50 \
  ++train_conf.log_interval=1 \
  ++train_conf.resume=true \
  ++train_conf.validate_interval=2000 \
  ++train_conf.save_checkpoint_interval=2000 \
  ++train_conf.keep_nbest_models=20 \
  ++train_conf.avg_nbest_model=10 \
  ++optim_conf.lr=0.0002 \
  ++output_dir="${OUTPUT_DIR}"
```

Adjust `batch_size`, `batch_type`, `num_workers`, and epoch counts to the user budget. `batch_type=token` forms dynamic batches by total frame/token length; `batch_type=example` uses a count of examples.

## Distributed launch pattern

Single machine:

```shell
export CUDA_VISIBLE_DEVICES="0,1"
GPU_NUM=$(python - <<'PY'
import os
print(len([x for x in os.environ.get("CUDA_VISIBLE_DEVICES", "").split(",") if x.strip()]))
PY
)

torchrun --nnodes 1 --nproc_per_node "${GPU_NUM}" \
  "$(command -v funasr-train-ds)" ${TRAIN_ARGS}
```

Multi-machine:

```shell
# master node
MASTER_ADDR=192.0.2.10 MASTER_PORT=12345 \
torchrun --nnodes 2 --node_rank 0 --nproc_per_node "${GPU_NUM}" \
  --master_addr "${MASTER_ADDR}" --master_port "${MASTER_PORT}" \
  "$(command -v funasr-train-ds)" ${TRAIN_ARGS}

# worker node
MASTER_ADDR=192.0.2.10 MASTER_PORT=12345 \
torchrun --nnodes 2 --node_rank 1 --nproc_per_node "${GPU_NUM}" \
  --master_addr "${MASTER_ADDR}" --master_port "${MASTER_PORT}" \
  "$(command -v funasr-train-ds)" ${TRAIN_ARGS}
```

If a launcher cannot execute console entry points directly, replace `"$(command -v funasr-train-ds)"` with the package module form supported by the local launcher, such as `python -m funasr.bin.train_ds` in a single-process smoke.

## Distributed config precedence

`funasr-train-ds` resolves these distributed keys specially:

- `use_ddp`
- `use_fsdp`
- `use_deepspeed`
- `deepspeed_config`

Precedence rule:

1. A top-level Hydra override wins, for example `++use_deepspeed=false`.
2. If no top-level key is present, the nested `train_conf` value is used, for example `++train_conf.use_deepspeed=true`.
3. Distributed keys are removed from the trainer-only `train_conf` before constructing the trainer.
4. `use_deepspeed=true` and `use_fsdp=true` are mutually exclusive and should fail fast.
5. DDP is automatic when `WORLD_SIZE > 1` and neither DeepSpeed nor FSDP is enabled.

Best practice: put engine-selection overrides at top level when they are intentional, and keep ordinary trainer parameters under `train_conf`.

```shell
# Top-level override: disables nested DeepSpeed from a template.
funasr-train-ds \
  ++use_deepspeed=false \
  ++deepspeed_config=ds_stage1.json \
  ++train_conf.use_deepspeed=true \
  ++train_conf.log_interval=10 \
  ...
```

In this case `use_deepspeed` is false, `deepspeed_config` is `ds_stage1.json`, DDP is used if `WORLD_SIZE > 1`, and `log_interval` remains a trainer setting.

## Checkpoints and pruning

Important checkpoint settings:

| Setting | Meaning |
|---|---|
| `train_conf.resume` | Resume from checkpoint state when available. |
| `train_conf.validate_interval` | Step interval for validation. |
| `train_conf.save_checkpoint_interval` | Step interval for saving checkpoints. |
| `train_conf.avg_keep_nbest_models_type` | Ranking metric: `acc` means larger is better, `loss` means smaller is better. |
| `train_conf.keep_nbest_models` | Number of ranked validated checkpoints to keep. |
| `train_conf.avg_nbest_model` | Number of best checkpoints averaged at the end. |

Only checkpoints with validation metrics participate in best-model ranking and `keep_nbest_models` pruning. If a checkpoint is saved at an unvalidated step, FunASR keeps it on disk but excludes it from `saved_ckpts`; it should not evict a validated best checkpoint. To make every saved checkpoint ranked, align `save_checkpoint_interval` and `validate_interval`.

## Large-scale data

For very large datasets, create multiple JSONL shards and a list file:

```text
shards/train.000.jsonl
shards/train.001.jsonl
shards/train.002.jsonl
```

Then pass the list file:

```shell
funasr-train-ds \
  ++train_data_set_list=train_shards.list \
  ++valid_data_set_list=val_shards.list \
  ++dataset_conf.data_split_num=256 \
  ...
```

The loader groups list entries sequentially. If data is heterogeneous, shuffle and balance the shard list at generation time; do not rely on `data_split_num` to rebalance it.

## Local inference after training

Local post-training inference is covered in [export-and-onnx.md](export-and-onnx.md). The key decision is whether the output directory contains `configuration.json`. If not, pass `--config-path`, `--config-name`, `++init_param`, `++tokenizer_conf.token_list`, and `++frontend_conf.cmvn_file` explicitly.
