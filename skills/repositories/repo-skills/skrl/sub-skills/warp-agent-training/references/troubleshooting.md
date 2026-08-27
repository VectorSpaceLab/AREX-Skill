# Warp troubleshooting

Use the first matching row, reduce the workflow to an import/device/config
probe, and only then add a wrapped environment or trainer. Preserve the
original exception and the resolved device in bug reports.

| Symptom | Likely cause | Recovery | What the recovery proves |
| --- | --- | --- | --- |
| `ModuleNotFoundError: warp` or `warp_nn` | The Warp optional extra was not installed in the active environment, or the interpreter is different from the one running the program. | Run `python -m pip install "skrl[warp]==2.1.0"`; verify with `python -c "import warp, warp_nn"`; verify `skrl` metadata/version. | Importability only; not CUDA or simulator readiness. |
| `AttributeError`/missing Warp NN layer during model creation | `warp-nn` is missing or incompatible with the installed Warp release. | Check both package versions and reinstall the Warp extra together; avoid mixing a checkout's undocumented development APIs with the 2.1.0 surface. | The selected Python package set is coherent enough to import. |
| Warp initialization reports a driver/toolkit problem | CUDA driver, toolkit, GPU architecture, or Warp binary compatibility is unsuitable. | Retry the safe probe with explicit `device="cpu"`; for CUDA, align the NVIDIA driver/toolkit/Warp requirements and validate on the target machine. | CPU fallback can isolate package/config behavior; it does not repair CUDA. |
| `parse_device("cuda:N")` warns and resolves elsewhere | The requested ordinal is unavailable or malformed. | Enumerate `wp.get_devices()`, choose a valid explicit alias, or request `"cpu"` deliberately. Never use an invalid CUDA alias to request CPU. | Device resolution only. |
| The default device is CUDA when CPU was expected | Warp's default configuration starts from `cuda:0` when available. | Pass `device="cpu"` to models, memory, agents, preprocessors, and environment/wrapper configuration; optionally set `config.warp.device = "cpu"` for the process. | All selected components can be intentionally placed on CPU. |
| The default device is CPU on a CUDA host | CUDA may be unavailable to Warp, the driver is not visible, or the program explicitly selected CPU. | Inspect Warp's initialization/device list and driver visibility; request `cuda:0` explicitly only after the runtime is ready. | A visible device is not workload validation. |
| CPU probe passes but CUDA training fails | CPU and CUDA exercise different compilation, allocation, and kernel paths. | Run a bounded CUDA-specific device/allocation check, then a bounded workload on the target environment; inspect Warp and driver errors. | The CPU probe remains valid only for CPU/API scope. |
| Illegal memory access or unexplained CUDA failure | Kernel/runtime mismatch, stale asynchronous error, invalid tensor shapes, or simulator/device interaction. | Reproduce with one environment and explicit device; synchronize according to Warp guidance; check shapes/roles; test the package without the simulator; reduce memory and concurrency. | Isolation narrows the cause; it does not certify a fix. |
| Model has `compute` but `act` raises `NotImplementedError` | `Model` was inherited before the mixin, or the wrong mixin was selected. | Declare `class Policy(GaussianMixin, Model)` or `class Value(DeterministicMixin, Model)`; call the corresponding mixin initializer and implement `compute`. | Model lifecycle/dispatch is correct for the inspected path. |
| `GaussianMixin` complains about `log_std` or returns wrong outputs | `compute` did not return an output dict containing `log_std`, or the log-std shape/device is wrong. | Return `(mean_actions, {"log_std": log_std})`; use one log-std value per action and allocate it on the model device; check `reduction`. | Stochastic model interface, not training quality. |
| Actions are outside expected bounds | `clip_actions=False`, wrong action scaling, or an unbounded/incompatible action space. | Use `clip_actions=True` where appropriate and make the network output/action-space contract explicit; for Pendulum-like bounds, scale the mean intentionally. | Action transformation on the selected device. |
| `KeyError` or missing output during agent setup/act | Model dictionary role keys do not match the algorithm. | PPO: `policy`, `value`; DDPG: `policy`, `target_policy`, `critic`, `target_critic`; SAC: `policy`, `critic_1`, `critic_2`, `target_critic_1`, `target_critic_2`. | Role map correctness; not full training. |
| PPO value/actor shape or role error | Value model is not scalar, policy lacks a stochastic distribution output, or asymmetric state input is mismatched. | Ensure policy has `num_actions` outputs and `log_std`; value has one output; construct state-consuming value against `state_space`; call `init_state_dict(role=...)`. | Model construction and lazy parameter initialization. |
| DDPG warns about no exploration noise | `exploration_noise` was omitted. | Add `GaussianNoise` or `OrnsteinUhlenbeckNoise` and matching `exploration_noise_kwargs`; set warm-up timesteps. | Noise object construction only. |
| DDPG target update or SAC target critic fails | A required target model is missing, incompatible, or not initialized with the live model architecture. | Create target models with the same input/output structure; initialize all models; keep target roles exact. | Target model topology and initial copy path. |
| SAC entropy setup is unstable or unexpected | `target_entropy`, `initial_entropy_value`, or `learn_entropy` does not match the task/action space. | Inspect the action-space shape; accept the default only when appropriate or set `target_entropy` explicitly; verify positive initial entropy value. | Config expansion and entropy parameter setup, not convergence. |
| `RandomMemory` samples an undersized batch or NaNs | Replay/rollout capacity is not populated, `batch_size` is too large, or tensor data was read before agent initialization/storage. | Set PPO capacity to `rollouts`; make replay capacity exceed warm-up and batch size; set `learning_starts`; let the trainer/agent create tensors; inspect `len(memory)`. | Buffer contract, not data quality. |
| `init_state_dict` fails or model parameters are empty | Lazy model-instantiator network has not received inputs, or its role/input expression is invalid. | Call `model.init_state_dict(role=role)` before optimizer/agent construction; verify observation/state/action spaces and network expressions. | Parameter materialization only. |
| Optimizer/scheduler constructor rejects `optimizer` | Scheduler kwargs were copied from a different framework or manually included the optimizer. | Remove `optimizer` from `learning_rate_scheduler_kwargs`; the agent supplies it. Use Warp scheduler signatures. | Scheduler configuration parsing. |
| A trainer creates output directories during a smoke | `experiment` intervals are `"auto"` or positive, or checkpoint/logging was enabled. | Set `write_interval=0`, `checkpoint_interval=0`, and a bounded trainer config for the smoke; use an intentional output directory for real runs. | Construction without persistence. |
| Trainer fails because a second agent/scope was supplied | Warp `SequentialTrainer`'s simultaneous-agent path is not implemented. | Use one Warp agent here; route multi-agent setup to the multi-agent/Runner owner. | Single-agent trainer boundary only. |
| `wrap_env` reports an unknown wrapper or import error | Wrapper tag is invalid or the external environment dependency is absent. | Use `"gymnasium"` for Gymnasium, leave selection to the environment branch, and install/verify external simulator dependencies separately. | Adapter selection/import only; no simulator run. |
| Environment tensors and model tensors disagree | The wrapper, memory, model, and agent received different devices or flattened-space sizes. | Derive all spaces/device from the same wrapped environment; inspect `num_observations`, `num_states`, `num_actions`, and tensor shapes before training. | Shape/device consistency for the construction path. |

## A staged recovery ladder

1. Run `warp_cpu_probe.py` with the package interpreter.
2. Import the exact algorithm/config/model/memory/trainer symbols and inspect
   signatures.
3. Resolve `config.warp.parse_device("cpu")` and pass that object explicitly.
4. Build a no-output model/config/memory construction using synthetic spaces,
   initialize lazy parameters, and do not call a trainer.
5. Add the already verified environment wrapper and one bounded trainer only
   after the preceding stages pass.
6. Treat any CUDA or simulator failure as a new backend/integration case; do not
   convert a CPU pass into a CUDA claim.
