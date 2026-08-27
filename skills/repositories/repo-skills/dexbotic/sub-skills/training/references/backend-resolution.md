# Backend resolution

The live resolver exposes `detect_package_versions()`, `apply_backend_defaults(...)`, `normalize_fsdp_config(...)`, `resolve_fsdp2_mode(...)`, and `resolve_backend_mode(...)`. It returns a `BackendResolution` with `requested_backend`, `resolved_mode`, `framework`, package versions, normalized config, plugin arguments, and warnings.

## Supported choices

| Requested | Resolution | Requirements/notes |
|---|---|---|
| `ddp` | `ddp_trainer` | Distributed CUDA launch is still required for real training; suitable for the documented LoRA recipes. |
| `deepspeed` | `deepspeed_trainer` | On the modern torch/Transformers stack, DeepSpeed must be installed at the resolver's minimum version. `fsdp` must be unset. |
| `fsdp` | `trainer_fsdp1` | `trainer_config.fsdp` must be configured. The resolver maps normalized keys to Trainer FSDP arguments. |
| `fsdp2` | native Trainer or explicit Accelerate plugin | Requires an enabled `FSDPProfile`, configured `fsdp`, and a sufficiently new torch/accelerate/Transformers stack. No wrap selector disables FSDP2 activation checkpointing with a warning. |

`TrainerConfig` rejects unknown backend names. Its default is DeepSpeed and its default DeepSpeed path is a source-tree-relative example; replace it with a path that exists in the user's environment rather than copying that default verbatim.

## Defaults and validation

`apply_backend_defaults` disables gradient checkpointing for FSDP modes, supplies a sharded state-dict default, selects a sharding strategy, and sets FSDP2 `reshard_after_forward`/version defaults. FSDP1 uses `FULL_SHARD` spelling for resharding. `normalize_fsdp_config` maps compatibility aliases and warns when explicit versions disagree.

The resolver's useful failure messages are actionable:

- DeepSpeed is missing or older than required for the current torch/Transformers pair.
- FSDP is selected without `trainer_config.fsdp`.
- DeepSpeed is selected while FSDP configuration is present.
- FSDP2 is not enabled, lacks a configured strategy/profile, or the package versions are too old.

Never solve these by silently changing backend. Report the requested and resolved modes in experiment logs.
