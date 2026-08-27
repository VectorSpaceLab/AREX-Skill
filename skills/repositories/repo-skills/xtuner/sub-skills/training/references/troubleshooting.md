# XTuner Training Troubleshooting

Use this guide for XTuner V1 SFT, pretraining, and MLLM fine-tuning launches. When an issue is actually about JSONL contents, media roots, tokenization, or packing schema, route to `data-preparation`. When it is about MoE/FP8/attention kernels/model internals, route to `model-backends`.

## Triage order

1. **Confirm launch mode.** Is the command using `--config` or direct model/dataset/training flags? It must be exactly one mode.
2. **Confirm entry point.** Prefer `torchrun ... -m xtuner.v1.train.cli.sft` so the installed package is used without a source checkout.
3. **Check paths.** Model/tokenizer/config/dataset/work directory paths should exist on every node and every rank. Local HF model paths should point to the snapshot directory containing `config.json`.
4. **Check world size.** `nproc_per_node * nnodes` must be compatible with FSDP/TP/EP/SP/HSDP choices.
5. **Scan logs.** Use `scripts/summarize_xtuner_log.py <log-or-work-dir>` to detect step progress, loss, memory, throughput, warnings, OOM, flash-attn fallback, bitsandbytes warnings, and config/direct conflicts.

## Symptom-to-fix table

| Symptom or message | Likely cause | Fix |
|---|---|---|
| `ValueError: Cannot specify both \`config\` and \`arguments\`.` | Mixed config mode with direct flags such as `--dataset`, `--load-from`, `--chat-template`, or `--total-step`. | Choose one mode. If using `--config`, move all direct options into the Python `TrainerConfig` file. If using direct mode, remove `--config`. |
| `ValueError: Must specify either \`config\` or \`arguments\`.` | Command launched the SFT entry without config and without required direct arguments. | Add `--config <config.py>` or provide direct mode arguments (`--dataset`, `--chat-template`, and `--load-from` or `--model-cfg`). |
| `Only one of \`total_step\` or \`epoch_num\` should be set` | Both direct step and epoch limits were provided. | Keep only one. For short smoke tests, prefer `--total-step <N>`. |
| `\`total_epoch\` or \`total_step\` should be set` | Python config did not set either training length after dataloader resolution. | Add exactly one of `total_step=<int>` or `total_epoch=<int>` to `TrainerConfig`. |
| `Transformer model path should be a valid HuggingFace model path` | `--tokenizer-path` omitted and `--load-from` is not accepted by Hugging Face `AutoConfig`. Common cause: pointing to a cache parent rather than a snapshot. | Point `--load-from` to a directory with `config.json`, or pass an explicit `--tokenizer-path` and `--model-cfg`, or switch to config mode. |
| Local model directory has `blobs/`, `refs/`, `snapshots/` but no `config.json` | The path is the HF cache model root, not a specific revision. | Use `.../snapshots/<revision>` as the model/tokenizer path. |
| Python config file loads but `KeyError: 'trainer'` or similar | Config mode file does not define top-level `trainer`. | Create `trainer = TrainerConfig(...)` in the config file. |
| Model config file says missing `model` | Direct `--model-cfg <file.py>` must expose top-level `model`. | Add `model = <XTunerModelConfig>(...)`, or use full config mode with top-level `trainer`. |
| `Dataset file ... does not exist` | Dataset glob/dir/file did not resolve to existing `.jsonl` files on the running node. | Check shell quoting for globs, mount paths on all nodes, and file suffixes. Use absolute user environment paths or shared storage. |
| `Dataset file must be a JSONL or JSON file` | Direct dataset path points to a non-JSONL file. | Convert/validate data in `data-preparation`; direct mode expects `.jsonl` files unless a dataset config `.py` is used. |
| No step logs after dataset load | Dataset/tokenization/packing is slow, waiting on storage, or distributed rank is stuck. | Check `data_time`, cache settings, media storage, and pack workers. Route schema/cache details to `data-preparation`. |
| `input_ids length ... exceeds model_max_length ... truncated` | Samples exceed max length. | Reduce sample length, increase compatible `max_length`/`pack_max_length` if memory allows, or filter data. Schema decisions belong to `data-preparation`. |
| `CUDA out of memory`, allocator errors, or killed process | Batch/pack length/model/FSDP configuration exceeds memory, or memory fragmented. | Reduce `global_batch_size`, `pack_max_length`, `max_length`, or model size; enable `CELossConfig(mode="chunk")`; increase recompute; consider `--fsdp-config.cpu-offload`; set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`; resume from latest checkpoint after changing only safe runtime knobs. |
| Memory high before first optimizer step during resume | Optimizer state load and checkpoint restore exceed available memory. | In config mode, use `LoadCheckpointConfig(offload_optimizer_first_step=True)` if the extra transfer cost is acceptable. |
| FSDP/HSDP assertion such as HSDP requiring `ep_size == 1` | Incompatible parallel mesh. | Recompute world-size factorization and set `tp_size`, `ep_size`, `sp_size`, and `hsdp_sharding_size` consistently. For MoE/EP details route to `model-backends`. |
| Distributed init/NCCL timeout or hang | Bad master address/port, rank mismatch, network issue, or one rank failed earlier. | Verify `--nnodes`, `--node-rank`, `--nproc-per-node`, `--master-addr`, `--master-port` on all nodes. Inspect earliest rank error, not only rank 0. |
| `flash-attn is not installed, using flex_attention instead` or `Import FlashAttention 2 failed` | Optional flash-attn package is not installed or not compatible with the current torch/CUDA/Python. | This is a performance fallback, not necessarily fatal. Install a compatible flash-attn only if the target backend requires it; otherwise expect lower throughput. Backend compatibility belongs to `model-backends`. |
| `Could not find the bitsandbytes CUDA binary` or bitsandbytes compiled without GPU support | Installed bitsandbytes wheel does not provide a binary for the active CUDA version. | If 8-bit optimizer/quantization is not used, treat as warning. If needed, install a CUDA-compatible bitsandbytes build or change CUDA/torch version. Backend details belong to `model-backends`. |
| `libGL.so.1` import error in MLLM setup | OpenCV desktop wheel expects system GL libraries. | Replace with a headless wheel in the user's environment (`opencv-python-headless`) or install system GL libraries if allowed. |
| `hf_interval`, `hf_max_keep`, or `async_hf_export` assertion | HF export requested but model cannot save in HF format and `load_from` is not an HF path. | Disable HF export settings or use a model/config path that supports HF save. |
| Step throughput drops while `data_time` is low | Compute/communication/compile/pack imbalance. | Check `time`, `tgs`, `seqlen_tgs`, token counts, `TORCH_LOGS=recompiles`, model compile settings, FSDP mesh, and long samples. Use the log summarizer; route backend-heavy causes to `model-backends`. |
| Step throughput drops with high `data_time` | Dataloader, storage, media, tokenization, cache, or pack worker bottleneck. | Check cache directory/tag, file system latency, media root, `num_workers`, and pack settings. Route detailed data investigation to `data-preparation`. |
| Loss is NaN/inf or `grad_norm` explodes | LR too high, bad data labels, unstable dtype/backend, or model/load mismatch. | Lower LR/warmup, inspect bad batches, verify tokenizer/model match, prefer `CELossConfig(mode="chunk")`, and check model/backend route for dtype/kernel issues. |

## Diagnosing the required hard cases

### Case 1: build a Qwen3 SFT command for local OpenAI JSONL

Use direct mode and the helper:

```bash
python sub-skills/training/scripts/build_sft_command.py \
  --nproc-per-node 8 \
  --load-from /models/Qwen3-8B/snapshots/<revision> \
  --chat-template qwen3 \
  --dataset /data/local_openai.jsonl \
  --total-step 100 \
  --work-dir /runs/qwen3-local-openai \
  --tee-log
```

If the helper errors before printing a command, fix that error first. The most common mistakes are missing dataset file, model path not pointing at a snapshot with `config.json`, and setting both `--total-step` and `--epoch-num`.

### Case 2: diagnose config mixed with direct flags

Bad command pattern:

```bash
torchrun -m xtuner.v1.train.cli.sft \
  --config /experiments/sft.py \
  --load-from /models/Qwen3-8B/snapshots/<revision> \
  --dataset /data/train.jsonl \
  --chat-template qwen3
```

Why it fails: `--config` makes XTuner expect `Config.fromfile(config)["trainer"]`, while any direct training flag creates `arguments`. The CLI explicitly rejects both at once.

Fix options:

- **Config mode:** remove `--load-from`, `--dataset`, and `--chat-template` from the command. Put equivalent values inside `trainer = TrainerConfig(...)` in `/experiments/sft.py`.
- **Direct mode:** remove `--config` and provide all required direct arguments.

## Checkpoint/resume recovery playbook

1. Inspect `.xtuner` in the work directory if available and find the latest checkpoint path.
2. Confirm the checkpoint directory contains `weights/`, dataloader state, scheduler state, and `train_state.json`.
3. Prefer config mode for resume:

```python
from xtuner.v1.train.trainer import LoadCheckpointConfig

trainer = TrainerConfig(
    ...,
    auto_resume=True,
    load_checkpoint_cfg=LoadCheckpointConfig(
        checkpoint_path=None,
        load_optimizer_states=True,
        load_optimizer_args=True,
        load_dataset=True,
        load_scheduler=True,
    ),
)
```

4. If auto-resume selects the wrong checkpoint, set `auto_resume=False` and pass an explicit `checkpoint_path`.
5. If optimizer-state loading OOMs, try `offload_optimizer_first_step=True` or resume model-only intentionally by disabling optimizer/dataloader/scheduler restore, noting that this changes training continuity.
6. If the original run died during async checkpoint finalization, prefer the most recent complete non-partial checkpoint. Missing `weights/` or `train_state.json` means it is not complete.

## Log summary hints

Run:

```bash
python sub-skills/training/scripts/summarize_xtuner_log.py /runs/experiment --tail 30 --warnings
```

Interpretation:

- **Parsed steps = 0:** training did not reach the step loop or log format is not XTuner V1. Look for import/config/path/distributed errors above the first step.
- **Last step less than expected:** run stopped early. Check errors after the last step and checkpoint state.
- **Loss decreased but memory high:** training is probably progressing; reduce memory only if near device limit.
- **High warning counts:** review flash-attn, bitsandbytes, truncation, missing path, and OOM warnings before rerunning.
- **Rank count lower than world size:** some ranks did not emit parseable step lines; inspect per-node logs and distributed failures.
