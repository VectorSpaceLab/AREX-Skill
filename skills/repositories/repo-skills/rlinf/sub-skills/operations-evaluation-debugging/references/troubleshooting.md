# Troubleshooting RLinf operations

Start with the first root-cause log fragment, not the last wrapper exception. RLinf distributed jobs often produce secondary Ray, Gloo, or NCCL failures after an earlier model-load, SGLang, asset, CUDA-memory, or rendering error.

## Fast triage map

| Symptom or log fragment | Likely cause | First action |
| --- | --- | --- |
| `Cannot connect to GCS`, workers cannot reach head | Ray head IP chosen from the wrong network interface or blocked network path | Route Ray startup/IP details to `setup-and-cluster`; verify the head address is reachable from worker nodes before relaunching. |
| `NCCL cuda invalid argument` during task transfer | Stale Ray/NCCL state after previous failed jobs | Stop/restart Ray only after preserving logs; then relaunch with the same config if no deeper placement issue is present. |
| `NCCL cuda invalid argument` while SGLang loads parameters | Placement mismatch between trainer and generation GPUs | Re-check `cluster.component_placement`, actor/rollout/inference GPU sets, and collocated vs disaggregated assumptions. |
| `CUresult error result=2 ... torch_memory_saver.cpp ... cu_mem_create` | SGLang restore or cached-buffer allocation lacks free GPU memory | Lower rollout static memory use, reduce `gpu_memory_utilization`, enable/offload where supported, or reduce env/rollout batch sizes. |
| Gloo timeout, `unbound_buffer.cc`, `Global rank ... is not part of group` | Often secondary after SGLang restore/generation failed | Search earlier logs for SGLang/CUDA/model-load errors before changing Gloo settings. |
| `CUDA out of memory`, `Killed`, abrupt worker death | GPU memory pressure, CPU memory pressure, or container OOM killer | Reduce env count, batch sizes, sequence length, rollout memory utilization; enable offload/checkpointing; inspect system memory if process was killed without Python traceback. |
| TensorBoard/W&B/SwanLab missing | Logger backend disabled, dependency/credential absent, or process exited before finish | Check `runner.logger.logger_backends`, backend directories, credentials, and earliest crash. Disable cloud loggers for offline smoke tests if credentials are not available. |
| `MUJOCO_EGL_DEVICE_ID ... must be an integer between 0 and 0`, EGL failures | EGL/CUDA device namespace mismatch or missing NVIDIA graphics driver files | Prefer RLinf's automatic EGL assignment; only override device ids deliberately. Verify graphics-capable driver and GLVND config; consider OSMesa only as a slower fallback. |
| Vulkan incompatible GPU driver | Graphics driver lacks Vulkan compatibility or uses an unsupported version for the GPU generation | Check GPU driver family. For some NVIDIA Ampere setups driver 535 is safer; for Hopper/L40S/RTX40, driver 570 is commonly expected. |
| Missing RoboTwin/ManiSkill/BEHAVIOR/PolaRiS assets | Asset path or required external dataset missing | Stop and ask for the correct asset root/license/key/model path; do not auto-download large assets unless user approves. |
| `model_path`, `lora_path`, tokenizer, norm stats, or `ckpt_path` missing | Config placeholder not replaced or wrong model-family checkpoint layout | Validate model-family requirements; confirm whether evaluation needs base weights, RL checkpoint, LoRA, tokenizer/config, and norm stats. |
| `save_interval=... must be divisible by val_check_interval=...` | Checkpoint/validation cadence mismatch | Change `save_interval`, `val_check_interval`, or disable checkpointing/validation intentionally. |
| Checkpoint load asserts `actor` path missing | `runner.resume_dir` points at the wrong directory level or partial checkpoint | Point `resume_dir` to `.../checkpoints/global_step_<N>`, not `actor/` or `mp_rank_*`; choose an older complete checkpoint if needed. |
| Resume restarts data order or warns missing `data.pt` | Dataloader/sampler state absent | Report reproducibility limitation; continue only if user accepts possible sample-order change. |
| `max_steps_per_rollout_epoch` divisibility failure | Eval step budget not divisible by `rollout.model.num_action_chunks` | Adjust rollout epoch step budget or action chunk setting to match training/eval protocol. |

## Ray and network failures

Checklist:

1. Preserve the main log and Ray worker logs before restart.
2. Identify whether Ray failed before workers launched or after a model/env worker error.
3. If workers cannot reach GCS, verify the selected head IP is reachable from every node and not the wrong NIC.
4. If prior jobs left stale processes, stop/restart Ray as part of a controlled relaunch.
5. Keep `RLINF_NODE_RANK` and multi-node Ray setup details in `setup-and-cluster`; this sub-skill only diagnoses symptoms.

## NCCL, Gloo, and placement failures

NCCL/Gloo messages are frequently secondary. Check in this order:

1. Did SGLang/vLLM/model loading fail earlier?
2. Are actor, rollout, inference, critic, and reward components placed on disjoint or collocated GPU sets consistent with the placement mode?
3. Are tensor/pipeline/expert parallel sizes compatible with world sizes?
4. Is Ray using stale resources from a previous run?
5. Does the job mix engines or environments that require separate virtual environments?

Only tune communication variables after the config/placement and first root cause are understood.

## CUDA memory and offload

Common levers:

- Reduce `env.eval.total_num_envs`, rollout batch size, sequence length, or `max_steps_per_rollout_epoch`.
- Lower rollout backend `gpu_memory_utilization`.
- Enable `enable_offload` for env, rollout, or actor when the config/model family supports it.
- Enable gradient checkpointing for actor/model training when appropriate.
- For SGLang restore issues, ensure inference weights are released before reloading and reduce static memory reservation.
- Avoid profiling every worker for the full run; profiler traces can add memory and storage pressure.

If the process is `Killed` without a Python traceback, inspect CPU RAM/container limits as well as GPU memory.

## Rendering and simulator graphics

RLinf automatically maps worker GPUs to EGL device ids where supported. Do not set `MUJOCO_EGL_DEVICE_ID` to a CUDA ordinal unless you know the EGL and CUDA device namespaces match.

Rendering triage:

1. Confirm whether the env uses MuJoCo/EGL, Vulkan, Isaac/OmniGibson, or another renderer.
2. For headless MuJoCo/robosuite errors, check driver graphics capability and GLVND/NVIDIA EGL availability.
3. Use OSMesa only as a slower CPU fallback and only when the benchmark can tolerate it.
4. For Vulkan-based simulators, verify a compatible GPU driver version.
5. For Isaac/OmniGibson/BEHAVIOR, check dataset/key/license paths and headless settings before blaming RLinf workers.

## Asset, model, and credential failures

Before launching or retrying:

- Replace placeholder paths for model, LoRA, tokenizer, config, norm stats, datasets, simulator assets, and robot IPs.
- Confirm checkpoint format matches the consumer: `runner.ckpt_path` often expects a consolidated `.pt`; full training resume expects `global_step_<N>` directories; backend conversion may be needed.
- Cloud logger credentials are separate from training correctness. If W&B/SwanLab credentials are absent, disable those backends or authenticate explicitly rather than treating it as model failure.
- For Hugging Face downloads/caches, distinguish network/auth/rate-limit problems from local path typos.

## CI and test failures

When a CI-equivalent job fails:

1. Identify the selected family: lint, unit, scheduler, embodied e2e, reasoning/agent e2e, SFT, offline RL, Docker/install, or package build/import.
2. Check whether the failure is environment creation, dependency resolution, asset/model path, runner timeout, test assertion, or cleanup.
3. Re-run the smallest matching test category locally only if environment/hardware is available.
4. Do not escalate to full e2e if a static import/unit failure already explains the change.
5. For parity failures, compare configs, seeds, env counts, action chunks, checkpoints, and baseline provenance before declaring a regression.

## Report template

When handing a failure back to a user or another agent, include:

- Run/config identity and overrides.
- Existing artifacts found by the checker.
- Last complete metric table and highest global step.
- Earliest root-cause log fragment with file/rank if known.
- A classified cause: config, missing asset/model, credentials, Ray/network, placement/communication, CUDA memory, rendering, checkpoint/resume, data utility, or unknown.
- Minimal next action and whether it is read-only, writes new artifacts, mutates existing data, requires GPU, requires robot hardware, or requires external credentials.
