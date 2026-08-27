# XTuner V1 Training Workflows

This reference describes safe operating flows for XTuner V1 supervised fine-tuning, pretraining, and multimodal SFT. Commands use the installed package module entry point (`python -m xtuner.v1.train.cli.sft`) so they do not depend on a source checkout.

## 1. Choose direct arguments or `--config`

XTuner V1 SFT has exactly two launch modes:

| Mode | Use when | Avoid when |
|---|---|---|
| Direct `TrainingArguments` | Simple LLM SFT with one model path, one dataset file/dir/glob, standard OpenAI/FTDP tokenization, common optimizer/LR/loss/FSDP knobs, and a short run. | You need custom dataset/tokenizer code, MLLM dataset lists, explicit checkpoint path resume, profiler hooks, custom model objects, or advanced save/export intervals. |
| Python config file via `--config` | MLLM SFT, pretraining, multiple datasets with sampling ratios, custom tokenization, custom model config, explicit `TrainerConfig`, checkpoint/resume/profile settings, and repeatable experiments. | You only need to swap `--load-from`, `--dataset`, `--chat-template`, `--total-step`, or `--work-dir` for a quick SFT. |

The two modes are mutually exclusive. XTuner raises `ValueError: Cannot specify both \`config\` and \`arguments\`.` when `--config` is mixed with direct model/dataset/training flags. If neither mode is provided, it raises `ValueError: Must specify either \`config\` or \`arguments\`.`

## 2. Build a direct Qwen3 SFT launch

For simple Qwen3 SFT over an OpenAI-format JSONL, use the bundled command builder first:

```bash
python sub-skills/training/scripts/build_sft_command.py \
  --nproc-per-node 8 \
  --load-from /models/Qwen3-8B/snapshots/<revision> \
  --chat-template qwen3 \
  --dataset /data/openai_sft.jsonl \
  --total-step 100 \
  --work-dir /runs/qwen3-openai-sft \
  --run-sft-default-env \
  --tee-log
```

The helper prints a shell command like:

```bash
mkdir -p /runs/qwen3-openai-sft
XTUNER_ACTIVATION_OFFLOAD=0 XTUNER_GC_ENABLE=1 XTUNER_USE_FA3=1 TORCH_LOGS=recompiles PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True XTUNER_DETERMINISTIC=false torchrun --nproc-per-node 8 --nnodes 1 --node-rank 0 --master-addr 127.0.0.1 --master-port 6000 --tee 3 -m xtuner.v1.train.cli.sft --load-from /models/Qwen3-8B/snapshots/<revision> --chat-template qwen3 --dataset /data/openai_sft.jsonl --total-step 100 --work-dir /runs/qwen3-openai-sft 2>&1 | tee -a /runs/qwen3-openai-sft/node_0.txt
```

Run the generated command only after confirming that:

- The model path is the actual Hugging Face snapshot directory, not a cache parent. A local snapshot should contain `config.json` plus tokenizer/model files.
- The dataset argument resolves to one or more `.jsonl` files. Schema and packing checks are owned by `data-preparation`.
- `--total-step` and `--epoch-num` are not both set.
- The requested `--nproc-per-node` matches available accelerators and the FSDP/TP/EP sizing plan.

### Direct-mode model choices

Direct mode accepts either:

- `--load-from <hf-model-path-or-id>`: XTuner tries to infer model config from Hugging Face `AutoConfig`. If `--tokenizer-path` is omitted, the same path is used as tokenizer path.
- `--model-cfg <alias-or-python-file>`: use a built-in alias or a Python file that exposes `model`. If no `--load-from` is supplied, training starts from the model config and may use the toy tokenizer unless `--tokenizer-path` is set.

For ordinary fine-tuning, provide `--load-from` and normally leave `--tokenizer-path` unset only when `--load-from` is a valid HF snapshot. For scratch/pretraining experiments, prefer Python config mode so tokenizer, data, and checkpoint behavior are explicit.

## 3. Launch with a Python config file

Use config mode when the experiment is not expressible as standard direct arguments. The config file must define a top-level `trainer` value. XTuner loads it with `Config.fromfile(config)["trainer"]`, creates `Trainer.from_config(trainer)`, and calls `trainer.fit()`.

```bash
torchrun --nproc-per-node 8 \
  --nnodes 1 \
  --node-rank 0 \
  --master-addr 127.0.0.1 \
  --master-port 6000 \
  --tee 3 \
  -m xtuner.v1.train.cli.sft \
  --config /experiments/qwen3_sft_config.py
```

A minimal config skeleton:

```python
from xtuner.v1.config import AdamWConfig, LRConfig, FSDPConfig
from xtuner.v1.datasets.config import DatasetConfig, DataloaderConfig
from xtuner.v1.datasets.sft_tokenize_fn import OpenaiTokenizeFunctionConfig
from xtuner.v1.loss import CELossConfig
from xtuner.v1.model import Qwen3Dense8BConfig
from xtuner.v1.train import TrainerConfig

model_cfg = Qwen3Dense8BConfig()

dataset_config = [
    {
        "dataset": DatasetConfig(
            name="train",
            anno_path="/data/openai_sft.jsonl",
            cache_dir="/runs/cache",
        ),
        "tokenize_fn": OpenaiTokenizeFunctionConfig(
            chat_template="qwen3",
            max_length=4096,
        ),
    }
]

dataloader_cfg = DataloaderConfig(
    dataset_config_list=dataset_config,
    pack_max_length=4096,
    pack_level="soft",
    num_workers=4,
)

trainer = TrainerConfig(
    model_cfg=model_cfg,
    load_from="/models/Qwen3-8B/snapshots/<revision>",
    tokenizer_path="/models/Qwen3-8B/snapshots/<revision>",
    dataloader_cfg=dataloader_cfg,
    optim_cfg=AdamWConfig(lr=6e-5, foreach=False),
    lr_cfg=LRConfig(lr_type="cosine", warmup_ratio=0.03, lr_min=1e-6),
    loss_cfg=CELossConfig(mode="chunk", chunk_size=1024),
    fsdp_cfg=FSDPConfig(recompute_ratio=1.0),
    global_batch_size=8,
    total_step=100,
    work_dir="/runs/qwen3-sft",
)
```

## 4. Pretraining workflow

XTuner V1 pretraining uses the same `TrainerConfig` and `sft.py` training entry, but the Python config normally swaps in a pretraining tokenizer function and pretraining data. Keep pretraining schema/tokenization specifics in `data-preparation`; from this training sub-skill, verify the orchestration:

- Use config mode, not direct SFT arguments, for repeatable pretraining.
- Set `model_cfg`, `tokenizer_path`, `dataloader_cfg`, `optim_cfg`, `lr_cfg`, `loss_cfg`, `global_batch_size`, `total_epoch` or `total_step`, and `work_dir` explicitly.
- Omit `load_from` for true training from scratch; provide it only when continuing from an HF-compatible model or other supported checkpoint flow.
- Use `CELossConfig(mode="chunk", chunk_size=1024)` when memory is tight.
- Use `checkpoint_interval`, `checkpoint_maxkeep`, `snapshot_interval`, and `async_checkpoint` intentionally for long runs.

## 5. MLLM SFT workflow

For multimodal SFT, prefer Python config mode because model config, dataset list, media roots, tokenize functions, collator, and pack lengths usually need explicit coordination.

Operational checklist:

1. Select an MLLM model config and, if needed, a text sub-config.
2. Build a list of dataset entries with `DatasetConfig(class_name="VLMJsonlDataset", media_root=...)` and an MLLM tokenize function.
3. Use a vision-aware collator such as `intern_s1_vl_sft_collator` or `qwen3_vl_sft_collator` as appropriate for the model family.
4. Keep `sample_max_length <= pack_max_length` to avoid unnecessary truncation/OOM.
5. Set `AdamWConfig(foreach=False)` when model components use different device meshes.
6. Use `CELossConfig(mode="chunk", chunk_size=1024)` to reduce memory.
7. Launch with `torchrun ... -m xtuner.v1.train.cli.sft --config <config.py>`.

If errors mention JSONL media fields, image paths, or data protocol fields, route to `data-preparation`. If errors mention attention kernels, model family internals, FP8, MoE, or dispatcher choices, route to `model-backends`.

## 6. Torchrun and environment resources

Use the installed module entry point:

```bash
torchrun --nproc-per-node <gpus-per-node> \
  --nnodes <num-nodes> \
  --node-rank <rank> \
  --master-addr <host> \
  --master-port <port> \
  --tee 3 \
  -m xtuner.v1.train.cli.sft \
  [--config <config.py> | direct TrainingArguments]
```

Common environment knobs adapted from XTuner's own example launcher:

| Variable | Typical use | Notes |
|---|---|---|
| `XTUNER_USE_FA3=1` | Enable flash-attn-3 path on supported Hopper-class setups. | If unsupported or not installed, disable it. Some FA3 paths are not deterministic. |
| `XTUNER_DETERMINISTIC=false` | Avoid deterministic backward constraints when FA3 does not support deterministic backward for a model/head dimension. | Use only when the experiment accepts non-determinism. |
| `XTUNER_ACTIVATION_OFFLOAD=0/1` | Try activation offload for memory pressure. | May trade memory for speed. |
| `XTUNER_GC_ENABLE=1` | Enable XTuner garbage-collection behavior used by example launchers. | Safe default for long runs. |
| `TORCH_LOGS=recompiles` | Diagnose `torch.compile` recompilation. | Useful when step time spikes. |
| `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` | Reduce CUDA allocator fragmentation. | Often useful for long context or variable packed batches. |

The bundled command builder can add these without launching training:

```bash
python sub-skills/training/scripts/build_sft_command.py \
  --config /experiments/sft.py \
  --nproc-per-node 8 \
  --run-sft-default-env \
  --tee-log --work-dir /runs/config-mode-logs
```

## 7. Work directory, checkpoints, resume, and export

XTuner creates or updates a work directory containing training metadata and run outputs. Important behaviors from `Trainer` and `TrainerConfig`:

- `work_dir`: target experiment root. If omitted at `Trainer` level, XTuner resolves to the current working directory; direct CLI defaults to `work_dir`.
- `.xtuner`: metadata file tracking experiments and latest checkpoints.
- Per-run experiment directory: timestamped under `work_dir`, with logs and profiling outputs when enabled.
- DCP checkpoints: saved under `checkpoints/epoch-<epoch>-step-<step>` or snapshot directories. A checkpoint contains weights, dataloader state, scheduler state, `train_state.json`, and serialized trainer config when available.
- `checkpoint_interval=-1`: save only at the end. `None` disables saving. A positive value saves every N steps and at the end.
- `checkpoint_maxkeep`: max DCP checkpoints to keep when cleanup is active.
- `snapshot_interval`: snapshot checkpoint interval; used as a fallback save path when normal checkpoint save is not triggered.
- `async_checkpoint=True`: save DCP asynchronously; useful at scale but introduces async monitor/finalization behavior.
- `hf_interval` / `hf_max_keep` / `async_hf_export`: Hugging Face-format export intervals, only valid when the model can save to HF format or `load_from` is an HF path.

### Resume guidance

For reliable resume, use Python config mode:

```python
from xtuner.v1.train.trainer import LoadCheckpointConfig

trainer = TrainerConfig(
    ...,
    auto_resume=True,  # use latest checkpoint in .xtuner when present
    load_checkpoint_cfg=LoadCheckpointConfig(
        checkpoint_path=None,  # or explicit /runs/.../checkpoints/epoch-1-step-100
        load_optimizer_states=True,
        load_optimizer_args=True,
        load_dataset=True,
        load_scheduler=True,
        offload_optimizer_first_step=False,
    ),
)
```

Notes:

- `auto_resume=True` overrides `load_checkpoint_cfg.checkpoint_path` with the latest checkpoint recorded in `.xtuner` when available.
- Use `offload_optimizer_first_step=True` only when resume memory is tight and you accept the extra CPU/GPU transfer on the first optimizer step.
- Direct CLI exposes checkpoint-related booleans in help, but in this package version direct-argument conversion primarily maps `async_checkpoint`; use config mode for explicit resume path and optimizer/dataloader/scheduler restore policy.
- If a resumed run fails with missing `weights/`, `dataloader/`, `lr_scheduler`, or `train_state.json`, the path is not a complete XTuner DCP checkpoint.

## 8. Profiling and log interpretation

`TrainerConfig` can enable profiler outputs:

```python
trainer = TrainerConfig(
    ...,
    profile_step=[10, 20],
    profile_time=True,
    profile_memory=True,
    prober_list=[],
)
```

XTuner step logs include fields such as:

- `data_time`: time spent waiting for the next batch. High values point to loading, tokenization, media I/O, cache misses, or pack scheduling.
- `time`: model/optimizer step time.
- `text_tokens`, `seqlen_tokens`, and sometimes `img_tokens`: per-rank token counts.
- `total_loss`, `local_loss`, `reduced_llm_loss`, or other loss keys: training loss signals.
- `grad_norm`: clipping/gradient health signal; spikes can precede instability.
- `max_memory` and `reserved_memory`: CUDA memory pressure and fragmentation clues.
- `tgs`, `seqlen_tgs`, `exp_tgs`: throughput metrics.
- `eta`: estimated remaining time.

Use the bundled log summarizer:

```bash
python sub-skills/training/scripts/summarize_xtuner_log.py /runs/qwen3-sft --tail 20
```

A healthy quick smoke typically shows step lines advancing, finite loss, nonzero tokens, bounded `grad_norm`, and memory below device capacity. The first step is often slower due to model/data initialization. Repeated high `data_time` suggests data/cache/media problems; repeated low `tgs` with normal `data_time` suggests model/pack/compile/communication pressure.
