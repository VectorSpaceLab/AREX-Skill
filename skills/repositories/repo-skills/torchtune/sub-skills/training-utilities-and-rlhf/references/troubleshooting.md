# Training Utilities And RLHF Troubleshooting

Use this matrix when torchtune training configs validate syntactically but fail around checkpoints, resume state, precision, distributed setup, logging/profiling, RLHF utilities, or experimental async RL code.

## First Preflight

Run the bundled checker before deeper debugging:

```bash
python scripts/check_training_runtime.py
```

Interpretation:

- `ok` for `torch` means the Python runtime can import PyTorch; it does not prove GPU memory or model files are sufficient.
- `torchao` failure usually blocks many torchtune training imports and QLoRA/QAT-related code paths.
- `torchtune.training` failure means checkpointer, precision, memory, and scheduler imports may be unavailable until prerequisites are installed.
- `torchtune.rlhf` success with `torchtune.rlhf.loss` failure can indicate the current DPO loss import bug; public RLHF helpers may still be usable.
- `async_rl_optional` failures are expected unless Ray/vLLM/async extras were installed intentionally.

## Checkpoint Format And Files

| Symptom | Likely cause | Safe fix |
| --- | --- | --- |
| Missing `model-00001-of-00002.safetensors` or similar | HF `checkpoint_files` does not match actual downloaded shards | Inspect the checkpoint directory and update `checkpoint_files`; for gated models, confirm download access first. |
| Missing `consolidated.00.pth` | Meta checkpointer selected for a directory containing HF safetensors, or Meta download ignored `.pth` files | Switch to `FullModelHFCheckpointer` for HF format or download Meta-format files intentionally. |
| State-dict keys mismatch such as `tok_embeddings` vs `model.embed_tokens` | Checkpointer format does not match source checkpoint | Use HF, Meta, or TorchTune checkpointer matching the source format; do not manually rename large tensors. |
| Shape mismatch on load | Model builder or `model_type` does not match checkpoint family/version | Align `model._component_`, `tokenizer`, `model_type`, and checkpoint source. |
| Output directory collision or recursive checkpoint copy | `output_dir` points inside `checkpoint_dir` or a conflicting previous run | Choose a separate durable `output_dir`; prune or archive old outputs deliberately. |
| Downstream inference cannot load output | User points at recipe state or intermediate DCP folder instead of final epoch folder | Use final synchronous epoch output for HF/Meta-compatible consumers; route inference/eval/quantization to the sibling skill. |

## Resume And Async Checkpointing

| Symptom | Likely cause | Safe fix |
| --- | --- | --- |
| Resume starts from epoch 0 | `resume_from_checkpoint` false or recipe state not loaded | Set `resume_from_checkpoint: True` and ensure the output contains compatible recipe state. |
| Resume fails with missing optimizer/RNG/dataloader keys | Trying to resume from a final-only weights folder | Resume from a torchtune intermediate output with `recipe_state.pt` when recipe state is required. |
| Async checkpoint resume cannot locate checkpoint | `enable_async_checkpointing` was true during save but false during resume, or output DCP folders are missing | Keep both `resume_from_checkpoint: True` and `enable_async_checkpointing: True` for async intermediate resume. |
| Final checkpoint missing after preemption | Async intermediate save succeeded but job stopped before final synchronous save | Resume from the latest async DCP checkpoint, then allow a final synchronous save to complete. |
| Save waits unexpectedly | Previous async checkpoint future is still running | Wait for async save completion before sync save; reduce checkpoint frequency or use faster storage. |
| Adapter resume fails | Adapter checkpoint/config or recipe checkpoint path missing | Confirm adapter files and `recipe_checkpoint` are in the expected output folders. |

## Precision, Dtype, And Device

| Symptom | Likely cause | Safe fix |
| --- | --- | --- |
| `bf16 precision was requested but not available` | Hardware/backend does not support bf16 | Switch to supported hardware or use `dtype=fp32` if the recipe/memory budget allows. |
| `Dtype ... must be one of fp16, bf16, fp32, fp64` | Unsupported dtype string in config | Use a supported torchtune precision string. |
| Full `fp16` training instability or rejection | Recipe path does not support full fp16 assumptions | Prefer `bf16` on supported accelerators or `fp32` for CPU/small debugging. |
| Parameters have unexpected dtype | Checkpoint loaded in a different dtype or custom module skipped dtype conversion | Use `validate_expected_param_dtype` to identify offending parameter names; fix model/checkpoint setup rather than masking the error. |
| QLoRA/QAT import errors | `torchao` missing or incompatible | Install the required torchao version for the selected torch stack before using quantized training paths. |

## Distributed Backend, Rank, And Environment

| Symptom | Likely cause | Safe fix |
| --- | --- | --- |
| Process group initialization hangs | Not launched with torchrun or missing rank/rendezvous env vars | Do not probe with `init_distributed`; build the correct `tune run`/torchrun command in the recipe sibling skill. |
| `torch.distributed already initialized` | Code called `init_distributed` after process group setup | Avoid duplicate initialization; rely on recipe setup or torchrun. |
| NCCL unavailable or backend mismatch | CUDA backend unavailable, wrong device type, or CPU-only runtime | Use `get_distributed_backend(device_type)` logic: CUDA usually `nccl`, CPU `gloo`, offload composite with `cpu:gloo`. |
| CPU offload or async DCP errors | Backend lacks CPU component for offloaded operations | Use `get_distributed_backend(device_type, offload_ops_to_cpu=True)` behavior in the approved run path. |
| Rank-specific logs missing | Non-zero ranks suppress rank-zero logging | Check all rank logs or use `get_world_size_and_rank`-aware logging patterns. |
| Multi-node cannot rendezvous | Bad `MASTER_ADDR`, port, firewall, or `--rdzv_endpoint` | Fix launch/rendezvous fields before changing torchtune configs. |

## Memory And Performance

| Symptom | Likely cause | Safe fix |
| --- | --- | --- |
| CUDA OOM during model init | Model/checkpoint too large for device memory | Choose smaller model, LoRA/QLoRA, distributed FSDP, activation checkpointing, or lower batch size. |
| OOM during backward | Activation memory or optimizer state too large | Enable activation checkpointing, reduce sequence length/batch size, increase accumulation, or use optimizer-in-backward where supported. |
| `get_memory_stats` raises on CPU | CPU devices are not supported for memory stats | Skip memory stats on CPU; use accelerator-only probes. |
| Activation offloading is slow | CPU transfer overhead dominates | Use offloading only when memory savings justify slowdown; validate baseline first. |
| Compile changes stack traces or slows startup | `torch.compile` has warmup/compatibility costs | Enable compile only after a functional baseline and keep a non-compiled reproduction path. |

## Metric Logging And Profiling

| Symptom | Likely cause | Safe fix |
| --- | --- | --- |
| `wandb` import/login error | W&B optional dependency or credentials missing | Use `DiskLogger`/`StdoutLogger` by default or install/login only after user approval. |
| `comet_ml` import/API error | Comet optional dependency or credentials missing | Use local logging unless user requests Comet and provides credentials through normal environment mechanisms. |
| TensorBoard/MLflow logger import error | Optional package missing | Install only the requested logger dependency or switch logger component. |
| Large trace files or slow training | Profiler enabled with memory/stack/shapes/flops | Disable profiler or reduce active schedule; keep trace output on durable storage. |
| No profiler output | `enabled=False`, no active cycle reached, or output dir unwritable | Check profiler config and schedule; verify `output_dir` is writable. |
| Logs written to unexpected directory | `metric_logger.log_dir` uses config interpolation or default output dir | Inspect resolved config with CLI/config sibling skill; keep logs under chosen `output_dir`. |

## RLHF Utilities And Losses

| Symptom | Likely cause | Safe fix |
| --- | --- | --- |
| `torchtune.rlhf.loss` import fails with missing `TypeVar`, `dataclass`, `Optional`, or `Tuple` | Current `dpo.py` source references those names without imports | Record as current-code gap; continue with public `torchtune.rlhf` utilities and recipe evidence until repo is refreshed or patched. |
| `torchtune.rlhf` top-level import fails | Base torchtune prerequisite such as `torchao` missing | Run the checker and install prerequisites rather than debugging RLHF logic first. |
| `get_batch_log_probs` shape error | `logits.shape[:-1]` does not match labels shape | Align model output and label tensors before shifting; keep labels as `[batch, seq]`. |
| Reward added to wrong token | Padded response lacked `valid_score_idxs` | Compute last valid response index and pass `valid_score_idxs` to `get_rewards_ppo`. |
| NaNs in whitened advantages | Mask has too few valid values or rewards/values are pathological | Inspect mask counts, reward scale, and KL coefficient; avoid normalizing all-padding rows. |
| DPO uses SFT data | Dataset lacks paired chosen/rejected outputs | Route to `data-and-datasets` and use preference dataset schemas. |

## Experimental GRPO And Async RL

| Symptom | Likely cause | Safe fix |
| --- | --- | --- |
| `ray`, `vllm`, `torchrl`, or `tensordict` import error | Async RL extras not installed | Treat as optional; install only in a dedicated environment after user approval. |
| Async GRPO recipe starts network/GPU services | Ray/vLLM workers launch as part of recipe | Do not run without explicit approval; use `tune cat`/`tune ls` and the checker first. |
| Single GPU cannot run documented async GRPO setup | Architecture splits trainer/generator resources and may need multiple GPUs | Explain hardware constraints; consider non-async GRPO or smaller configs only after user approval. |
| vLLM weight sync issues | Parameter server/generator constraints or version mismatch | Verify vLLM/Ray versions and current dev source comments; treat as experimental instability. |
| Dev API changed | `torchtune.dev` has no backward-compatibility guarantee | Refresh the skill from current repo source before relying on dev API names. |

## Synthetic Hard Cases For Review

- Debug a DPO validation failure where top-level `torchtune.rlhf` imports but `torchtune.rlhf.loss` fails from the current DPO import bug; the agent should identify the precise source gap and not rewrite the dataset config.
- Preflight a distributed QLoRA plan on a CPU-only machine missing `torchao`; the agent should report runtime gaps and command-shape risks without initializing distributed process groups or launching training.
