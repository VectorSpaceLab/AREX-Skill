# Distributed Backend Troubleshooting

Use this page when backend configuration parses but the requested runtime is unavailable, contradictory, or likely to fail.

## Optional Dependency Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: deepspeed` | DeepSpeed selected without package installed | Install DeepSpeed in the runtime environment or choose FSDP/DDP. |
| `torch_xla` import failure | TPU/XLA selected outside an XLA environment | Install/use a TPU runtime with `torch_xla`, or do not set TPU/XLA launch flags. |
| Transformer Engine import failure | `mixed_precision="fp8"` with `TERecipeKwargs` or `fp8_backend: te` | Install `transformer-engine` and use compatible NVIDIA hardware, or choose `ao`/`msamp`/bf16. |
| `torchao` import failure | `AORecipeKwargs` or torchao FP8/quantization path selected | Install `torchao`, and verify PyTorch/hardware support. |
| `bitsandbytes` import or CUDA setup failure | `BnbQuantizationConfig` selected without supported bitsandbytes backend | Install a compatible bitsandbytes build; check CUDA or multi-backend bitsandbytes support. |
| `msamp` import failure | MS-AMP FP8 selected | Install MS-AMP and avoid ZeRO-3 for MS-AMP DeepSpeed integration. |
| Habana/HPU import failure | Gaudi path selected without Habana stack | Use an HPU runtime with Habana packages or choose a CPU/GPU backend. |

The bundled validator can report import hints with `--check-imports`, but it does not prove hardware execution.

## Hardware Availability

- `fp16`, NCCL, DeepSpeed, and most FP8 paths generally require CUDA GPUs or equivalent backend support.
- `bf16` support depends on device and backend: common on TPU, HPU, Ampere+ NVIDIA GPUs, and some CPU/XPU paths.
- FP8 needs both a backend package and hardware with FP8-capable tensor cores or backend-specific support.
- TPU/XLA requires a TPU runtime; local CPU tests cannot emulate XLA multi-host behavior.
- Multi-node runs need correct `num_machines`, `machine_rank`, rendezvous backend, master address/port, firewall, and homogeneous dependency versions.

## DeepSpeed ZeRO and Offload Confusion

Checklist:

- ZeRO stage is one of `0`, `1`, `2`, `3`.
- `zero_optimization` exists in a full DeepSpeed JSON.
- Optimizer offload is meaningful for ZeRO-2 and ZeRO-3.
- Parameter offload is meaningful only for ZeRO-3.
- NVMe offload requires `device: nvme` and an NVMe path; a path with `device: cpu` is ignored or suspicious.
- `zero3_init_flag` and `zero3_save_16bit_model` only make sense for ZeRO-3.
- MS-AMP is not supported with ZeRO-3 in Accelerate's DeepSpeed plugin path.
- If both plugin kwargs and JSON values are provided, compare the final `plugin.deepspeed_config` rather than assuming the constructor won.

## FSDP Wrap Class Mistakes

Common signs:

- Runtime says a class name was not found.
- Tied weights or shared embeddings break after wrapping.
- FSDP2 reports parameter mapping failures or missing parameters after wrapping.
- Performance regresses because tiny modules were wrapped individually.

Fixes:

- Use exact Python class names, not module path strings, for `fsdp_transformer_layer_cls_to_wrap` / `transformer_cls_names_to_wrap`.
- Prefer model `_no_split_modules` when available for Transformers models.
- Keep shared embeddings and tied-weight modules in the same outer FSDP unit.
- For FSDP2, use `fsdp_reshard_after_forward: true` or `false`, not `FULL_SHARD`.
- Do not carry FSDP1-only fields such as `backward_prefetch` into FSDP2 without checking warnings.

## FP8 Support Mismatch

Checklist:

- `mixed_precision` is `fp8`.
- Exactly one intended FP8 backend is selected: `te`, `ao`, or `msamp`.
- Backend-specific package is installed.
- Hardware supports the chosen FP8 path.
- `TERecipeKwargs.fp8_format` is one of `HYBRID`, `E4M3`, or `E5M2`.
- `TERecipeKwargs.amax_compute_algo` is `max` or `most_recent`.
- `MSAMPRecipeKwargs.opt_level` is `O1` or `O2`.
- Torchao FSDP float8 all-gather is paired with FSDP2 when requested.
- Deprecated `FP8RecipeKwargs` is replaced with `TERecipeKwargs`, `AORecipeKwargs`, or `MSAMPRecipeKwargs` for new code.

## Config File vs Plugin Precedence

When a user supplies both CLI/config-file values and explicit Python plugins:

- Launch config determines distributed process startup: process count, machines, rendezvous, TPU/GPU mode, and many environment variables.
- Python plugins determine how `Accelerator` configures model wrapping after process startup.
- DeepSpeed JSON explicit values can override or conflict with `DeepSpeedPlugin` fields. Values set to `auto` are intended for Accelerate/runtime filling.
- FSDP plugin constructor values can override environment/config fallbacks; missing constructor values are filled from `FSDP_` environment variables.
- The safest debugging step is to print or inspect `accelerator.state`, `accelerator.state.deepspeed_plugin.deepspeed_config`, or `accelerator.state.fsdp_plugin` on rank 0 after initialization.

## Multi-Node Rank and Rendezvous Issues

Symptoms: hanging before training, timeout in `init_process_group`, all workers think they are rank 0, or only one node joins.

Check:

- `num_machines` equals the number of participating hosts.
- `machine_rank` is unique and zero-based.
- `main_process_ip`/master address and `main_process_port` are reachable from every node.
- `same_network` and rendezvous backend match cluster networking.
- Every node has the same training script path, dependency versions, and config file.
- Firewalls/security groups allow the rendezvous port.
- `InitProcessGroupKwargs(timeout=...)` can help with slow starts but does not fix wrong addresses.

## DDP Communication Hook Problems

- Hooks apply only to DDP-wrapped models, not DeepSpeed or FSDP wrappers.
- BF16 communication hooks require backend support; check NCCL/backend version.
- PowerSGD options belong in `comm_state_option`.
- HPU and other non-CUDA backends may not support the same hook set.

## Local SGD Problems

- Local SGD is for basic multi-GPU or multi-CPU distributed training.
- Do not combine it with DeepSpeed/FSDP unless the project explicitly proves compatibility.
- Call `local_sgd.step()` after optimizer updates so synchronization cadence matches actual parameter updates.
- It can combine with gradient accumulation, but accumulation and synchronization steps are different concepts.

## Static Validation Workflow

Run before attempting a distributed job:

```bash
python sub-skills/distributed-training-backends/scripts/validate_backend_config.py config.yaml
python sub-skills/distributed-training-backends/scripts/validate_backend_config.py --format deepspeed ds_config.json
```

Use results as a triage list, not as proof of runtime success.
