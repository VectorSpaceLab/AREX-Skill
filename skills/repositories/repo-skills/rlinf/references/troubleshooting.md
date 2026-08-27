# RLinf Cross-cutting Troubleshooting

## When to read

Read this when the user's issue spans installation, Ray, configs, optional backends, runtime failures, or ambiguous task routing. For workflow-specific triage, continue to the nearest sub-skill troubleshooting reference.

## Fast triage ladder

1. **Classify the workflow.** Setup/cluster, embodied, reasoning/agentic, extension work, or operations/debugging.
2. **Inspect, do not launch.** Use bundled read-only scripts first: root API snapshot, setup environment probe, config inspectors, run artifact checker.
3. **Separate prerequisites from bugs.** Missing model paths, simulator assets, Ray node ranks, rollout servers, real robot access, and API keys are not code bugs until prerequisites are satisfied.
4. **Check the earliest failure.** Later Gloo/NCCL/Ray timeouts often follow an earlier SGLang, CUDA OOM, env reset, or path error.
5. **Do not claim full validation from CPU-only checks.** Full training/eval may need GPUs/NPUs, model checkpoints, datasets, and simulators.

## Common symptom map

| Symptom | Likely owner | First checks | Recovery |
| --- | --- | --- | --- |
| `ModuleNotFoundError: rlinf`, `ray: command not found`, wrong package version | setup-and-cluster | root API snapshot; setup env probe; package install target | Install with the selected target/extras or activate the intended environment; verify `python -c 'import rlinf'` and `ray --version`. |
| Ray workers do not join or node count is wrong | setup-and-cluster | `RLINF_NODE_RANK` before `ray start`; head IP; port/firewall; `ray status` | Stop Ray on affected nodes, set env vars and network device, restart, then relaunch only from a joined node. |
| Config composes but component placement looks impossible | setup-and-cluster + task sub-skill | render cluster plan; compare `cluster.num_nodes`, GPU count, node groups, process ranks | Fix placement ranges, node-group labels, or hardware ranks before running. |
| YAML has placeholder paths such as `/path/to/...` | task sub-skill | static config inspector; model/data/env sections | Replace model checkpoints, datasets, simulator assets, logging paths, service URLs, and robot addresses. |
| CUDA/NCCL/Gloo timeout after rollout starts | operations-evaluation-debugging | earliest worker log; SGLang/vLLM memory; placement collisions; GPU visibility | Resolve the earlier backend failure; restart Ray if environment variables or visible devices changed. |
| EGL/MuJoCo/Vulkan/rendering failure | embodied-workflows + operations | `MUJOCO_GL`, `PYOPENGL_PLATFORM`, EGL device mapping, container driver capabilities | Use EGL/headless settings, correct driver/graphics capabilities, and per-worker render device assignment. |
| Reward worker or data preprocessing mismatch | embodied-workflows or reasoning-agent-workflows | reward config, dataset schema, collected episode fields, service credentials | Validate the data format and reward model type before launching the trainer. |
| SGLang/vLLM OOM or restore errors | reasoning-agent-workflows + operations | rollout backend config, memory utilization, offload, sequence lengths, placement | Reduce batch/seq/model parallel load, enable offload, separate actor/rollout placement, or switch backend. |
| `model_type` or `env_type` unsupported after extension | extension-development | registry hook, `RLINF_EXT_MODULE`, config validation, worker process import path | Register the type in the correct process, add lazy import/factory branches, and add tests. |
| Checkpoint resume loads the wrong step or path | operations-evaluation-debugging | backend (FSDP vs Megatron), checkpoint directory, `runner.resume_dir` | Select the latest complete global-step checkpoint and relaunch with the same config plus resume key. |

## What not to do by default

- Do not run installer scripts, Docker builds, `ray start`/`ray stop`, training, evaluation, data conversion, checkpoint conversion, robot diagnostics, or cloud logger login without explicit user approval.
- Do not delete logs, checkpoints, replay buffers, generated data, or Ray state as a first response.
- Do not edit source registries for a one-off external model until checking whether external `register_model(...)` plus `RLINF_EXT_MODULE` is the safer route.
- Do not run real-world robot checks unless the operator confirms safety, calibration, e-stop, and workspace readiness.

## Useful read-only helpers

- [`../scripts/rlinf_public_api_snapshot.py`](../scripts/rlinf_public_api_snapshot.py) — root package/version/config constants snapshot.
- `setup-and-cluster/scripts/rlinf_env_probe.py` — environment/Ray/Torch/CUDA probe.
- `setup-and-cluster/scripts/render_cluster_plan.py` — static `cluster` YAML summary.
- `embodied-workflows/scripts/check_embodied_config.py` and `reasoning-agent-workflows/scripts/inspect_agentic_config.py` — static task config checks.
- `operations-evaluation-debugging/scripts/check_run_artifacts.py` — log/checkpoint/video artifact layout audit.
