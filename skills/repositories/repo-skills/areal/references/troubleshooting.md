# AReaL cross-cutting troubleshooting

Use this root troubleshooting guide when the failure spans install, config, backend variants, services, or multiple sub-skills. For workflow-specific details, follow the nearest sub-skill troubleshooting reference.

## Install/import failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `python` is 3.13 or older than 3.11 | AReaL metadata supports `>=3.11,<3.13` | Create a Python 3.11/3.12 environment before installing. |
| `import areal` fails after editable install | Missing base dependency or current directory masking an install | Run the root env doctor; verify `python -m pip show areal`; reinstall in the intended env; avoid using Conda `base` for production. |
| `pip check` reports Torch/Transformers/PEFT/TorchAO conflicts | Mixed SGLang/vLLM/runtime variants or partial install | Choose one variant and rebuild/sync that environment. Do not combine SGLang and vLLM pins unless the repo variant explicitly supports it. |
| SGLang or vLLM import is missing | Wrong optional/runtime variant | For default SGLang use the default CUDA sync/runtime image. For vLLM use the vLLM pyproject/lock or vLLM runtime image. |
| FlashAttention/Apex/TransformerEngine compilation fails | Missing CUDA toolkit/compiler, ABI mismatch, or insufficient build resources | Prefer runtime images/prebuilt wheels. If compiling, match Python, Torch, CUDA, GPU architecture, and use conservative parallel build settings. |

## Config and command failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `--config` file not found | Driver working directory or relative path is wrong | Use an absolute config path or run from the intended project directory. |
| Override is ignored or rejected | Missing `+` for new Hydra/OmegaConf key, typo, or wrong config class | Use `+new.key=value` for new keys and validate with the bundled config script. |
| Removed `behave_imp_weight_*` key error | Legacy rejection-sampling fields | Migrate to the `rejection_sampling` mapping in `configuration-cheatsheet.md`. |
| Total requested GPUs do not match cluster | Per-engine backend worlds were not summed/planned | Run `check_backend_plan.py` with `cluster.n_nodes` and `cluster.n_gpus_per_node`. |
| `allocation_mode` confusion | Legacy SPMD field mixed with modern backend fields | Prefer per-engine `rollout.backend`, `actor.backend`, etc.; use legacy launcher docs only when the user asks for SPMD. |

## CUDA/backend failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| CPU import works but training/inference backend fails | Import-only env lacks backend extra, model runtime, or CUDA-compatible packages | Recreate exact backend environment; do not treat CPU import as backend proof. |
| NCCL hang or collective timeout | Rank mismatch, inconsistent collectives, bad network/NCCL env, or placement mismatch | Enable `TORCH_DISTRIBUTED_DEBUG=DETAIL` and `NCCL_DEBUG=INFO`; verify every rank enters the same collective; check backend worlds and Ray/Slurm placement. |
| CUDA OOM during rollout or training | Model too large, TP/PP/DP mismatch, sequence length/batch too high, offload disabled, cache too large | Reduce batch/sequence/concurrency; increase TP/PP; enable supported offload; lower SGLang/vLLM memory fraction; verify no unintended colocation. |
| Weight update stalls | `disk`, `xccl`, or `awex` mode incompatible with role placement or backend | Check `WeightUpdateMeta` fields and backend support; use disk fallback when XCCL group setup is not viable. |
| LoRA update fails | Backend does not support selected LoRA path or LoRA config mismatch | Confirm `use_lora`, rank/target modules, backend support, and weight update mode; SGLang LoRA commonly needs disk-mode updates. |

## Dataset/reward/workflow failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Dataset unsupported | `dataset_config.path` and `type` do not match built-in loaders and path is not loadable from disk | Add a custom loader or save a Hugging Face dataset to disk; validate sample records with the workflow checker. |
| `messages` missing in RLVR workflow | Dataset row schema does not match `RLVRWorkflow` prompt extraction | Add `messages` with chat roles/content or provide a custom input-id extraction function. |
| Reward import fails on workers | Function is nested, not importable, has heavy top-level side effects, or needs credentials | Move reward to module scope, keep imports light, and pass credentials through approved runtime config only. |
| Workflow returns wrong type | Custom workflow returns list/string/non-tensor structure | Return tensor dict, `InteractionWithTokenLogpReward` dict, or `None` as documented. |

## Service and credential failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Gateway/router/worker health is mixed | One service component failed while CLI state remains | Use `areal <group> status`, `ps`, and `logs`; inspect component-level error before restarting. |
| Admin key rejected | Confusing inference-gateway admin key, agent-service admin key, and session key | Keep `$INF_ADMIN_KEY`, `$AGENT_ADMIN_KEY`, and `$SESSION_API_KEY` separate. Session keys usually start with `sk-sess-`. |
| Model registration fails | Backend args quoting, missing model path, stale workers, or wrong backend variant | Validate command statically, then use `areal inf status/logs`; stop stale workers before retrying. |
| Online RL episode has no reward/data | Session not started, traffic not routed through inference gateway, or reward set on wrong key | Start a session, forward the session key through the agent call, then set reward on the inference gateway session. |

## Verification language

When reporting results, distinguish:

- **Import/config verified**: package imported, configs parsed, CLI help worked.
- **Backend smoke verified**: framework saw GPU and a tiny op succeeded.
- **Native workflow verified**: an approved AReaL test/example/training/service case actually ran in the target runtime.
- **Skipped**: not run because it needed GPU cluster, model/data download, service side effects, credentials, or long runtime.
