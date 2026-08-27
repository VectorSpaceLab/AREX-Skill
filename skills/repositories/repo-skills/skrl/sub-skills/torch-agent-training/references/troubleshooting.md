# Torch workflow troubleshooting

Use the root skill's framework and package troubleshooting first, then apply
this workflow-specific matrix. Error wording can vary across PyTorch and
Gymnasium versions; diagnose the first incompatible boundary rather than
loosening every setting.

| Symptom | Likely cause | Corrective action |
|---|---|---|
| `No module named torch` or a Torch submodule import fails | Base package installed without the `torch` extra, or Torch is unavailable for the interpreter running the command | Install `skrl[torch]` into the active runtime; verify `import torch, skrl` and `skrl.__version__`; do not install JAX/Warp extras for a Torch-only request |
| TensorBoard import fails during agent setup | Base `tensorboard` dependency is missing or the environment is partially installed | Repair the package environment, then set `experiment.write_interval=0` for a no-log component probe; do not enable logging until the import succeeds |
| `wandb` import fails only when building the agent | `ExperimentCfg.wandb=True` dynamically imports an optional dependency | Install/configure `wandb` or leave `wandb=False`; this is not a Torch model failure |
| Requested `cuda`, `cuda:N`, or another device logs an invalid-device warning and becomes CPU | Device string is malformed, CUDA is unavailable, or the index cannot allocate a tensor | Call `config.torch.parse_device(request, validate=True)`, inspect `torch.cuda.is_available()` and device count, then pass the resolved device consistently. CPU fallback does not prove CUDA works |
| Model, memory, and environment tensors are on different devices | Each component independently resolved `device=None`, or a model was moved after memory/agent creation | Resolve once from the environment/config and pass it to every model, memory, preprocessor, noise, and agent; avoid mixing CPU observations with GPU models |
| `RuntimeError` from `torch.distributed` during import | `WORLD_SIZE > 1` was inherited without an initialized distributed launcher or compatible backend | Unset distributed variables for a local run, or launch with a valid multi-process Torch setup; do not use a single-process CPU import to claim distributed support |
| `KeyError`, `NoneType` attribute failure, missing optimizer parameters, or an empty update | Model dictionary key is wrong or a training-only model role was omitted | Copy the exact role table for the selected algorithm. For PPO/A2C/RPO/TRPO use `policy` and `value`; for critics use every target/critic key; for AMP add `discriminator` |
| `GaussianMixin` raises on output use or log probabilities are invalid | `compute` did not return `outputs["log_std"]`, returned a wrong shape, or used an invalid reduction/probability convention | Return mean actions plus a log-standard-deviation tensor broadcastable to the action shape; use a supported reduction; use logits for categorical models unless explicitly opting into probabilities |
| Actions have wrong dtype/shape or a categorical distribution fails | Distribution does not match the Gymnasium action space (`Discrete`, `MultiDiscrete`, or `Box`) | Select Categorical, MultiCategorical, Gaussian/MultivariateGaussian, or Deterministic according to the action space; verify the final `compute` shape and integer action convention |
| `Model.act` reports it is not implemented | The mixin is after `Model`, its initializer was not called, or `act` dispatch for a shared model is missing | Define `class Policy(GaussianMixin, Model)`, call `Model.__init__` before `GaussianMixin.__init__`, and override shared-model `act` by role |
| Critic receives an action or state shape it cannot consume | Critic architecture was built for the wrong inputs, or `state_space`/`observation_space` was flattened inconsistently | Follow the role table: values consume observation/state as implemented; off-policy critics consume observation/state plus action; use `num_observations`, `num_states`, and `num_actions` from `Model` rather than hand-counting nested spaces |
| PPO/A2C update does not occur, or memory is sampled before it is full | `cfg.rollouts` is not aligned with `memory_size`, `learning_starts` is too large, or trainer timesteps end before the update boundary | Set `memory_size == cfg.rollouts` for a standard rollout, remember the total batch is multiplied by `num_envs`, and run at least through a rollout boundary after `learning_starts` |
| PPO mini-batches are empty, uneven, or produce a sampling error | `mini_batches` is incompatible with the valid sample count or sequence setup | Choose a divisor/useful split of `len(memory)`; test with a small `rollouts` and `num_envs=1` first; for RNNs also set the model sequence specification and use sequence-aware sampling |
| Off-policy agents fail at the first update with too few samples | Replay memory is underfilled relative to `batch_size`, or learning starts too early | Increase `learning_starts`, collect enough transitions, or use `replacement=True` only when repeated samples are intentional; do not confuse capacity with valid sample count |
| Memory tensor size/dtype error while initializing | A caller pre-created an agent-owned tensor with an incompatible shape or dtype | Start from an empty `RandomMemory` and let the agent create tensors; if extending memory, match the agent's names, flattened space size, and dtype exactly |
| AMP initialization fails with missing motion fields or batches | AMP's extra observation space, motion dataset, reply buffer, or reference-motion callback is missing or inconsistent | Provide all AMP-specific constructor arguments, populate the dataset's expected tensors, and ensure `amp_batch_size` is realistic for the motion dataset; route the task elsewhere if no motion-prior data exists |
| KL scheduler has no visible effect | It was attached to an unsupported agent, threshold/units are inappropriate, or the agent did not produce a KL value | Use `KLAdaptiveLR` for A2C, AMP, PPO, or RPO as documented, pass class and kwargs through the config, and inspect the optimizer learning rate after a real update |
| Preprocessor changes appear not to persist | A new scaler was created per call, or its state was not included in the agent checkpoint | Instantiate `RunningStandardScaler` through the agent config, retain the agent instance, and resume through `agent.load` so its registered state can be restored |
| Direct `agent.init(trainer_cfg={...})` raises a dataclass `asdict` error | In 2.1.0 the base implementation serializes `trainer_cfg` with `dataclasses.asdict`; the trainer passes its config dataclass, not a plain dict | Prefer constructing a trainer (which calls `agent.init` correctly), call `agent.init()` for a no-loop component probe, or pass the appropriate `TrainerCfg` dataclass rather than a raw dictionary |
| `SequentialTrainer` refuses a single environment in a simultaneous-agent path | The trainer's sequential multi-agent branch requires vectorized environments for its scope loop | Use the ordinary single-agent `SequentialTrainer` path, or route multi-agent scope/wrapper selection to the sibling; do not hand-edit scopes to bypass the environment contract |
| `StepTrainer` advances unexpectedly or never resets | `train()`/`eval()` were called with inconsistent timestep ownership, or the single environment termination/reset contract was not respected | Let the trainer's internal timestep advance, or pass both `timestep` and `timesteps` deliberately; call the returned transition outputs and keep the environment wrapper contract intact |
| `ParallelTrainer` hangs, cannot pickle an agent, or exhausts memory | Spawned workers cannot import the model definition, processes lack shared-memory setup, or the per-process overhead is too high | Put custom model classes at importable module scope, use `if __name__ == "__main__":`, test a tiny configuration, and prefer `SequentialTrainer` until process behavior is proven. CUDA multi-process memory overhead can be substantial |
| Evaluation creates logs/checkpoints unexpectedly | Evaluation reused production experiment intervals or `"auto"` resolved to a positive interval | Set both intervals to `0` in the evaluation config and set `stochastic_evaluation=False` if mean actions are required |
| `agent.load` reports missing modules or state-dict size/key errors | Evaluation agent intentionally omitted modules, or the current architecture/roles differ from the saved agent | Loading through an agent is recommended; warnings about absent training-only modules may be acceptable for policy-only evaluation, but shape/key mismatches require reconstructing the original architecture before loading |
| Resume succeeds but behavior is wrong | Same tensor shapes exist but action scaling, distribution mixin, role mapping, preprocessor state, or device semantics changed | Treat architecture, action space, model roles, preprocessing, and configuration as part of the checkpoint contract; compare them before accepting a resumed result |
| A script accidentally creates artifacts during a probe | Agent intervals, memory export, or a trainer loop were enabled | Use the bundled component smoke, explicit non-positive logging/checkpoint intervals, no memory export, a temporary environment only if needed, and no call to `train()`/`eval()` in the smoke |

## Fast isolation sequence

1. Run `python scripts/torch_ppo_components.py --help` and then the CPU
   component smoke.
2. Import the chosen algorithm, config, memory, model mixins, and trainer in
   one process; print signatures if an API assumption is uncertain.
3. Instantiate models with the real spaces and call `act` on one correctly
   shaped batch. Verify action/value shapes and device before creating a
   trainer.
4. Instantiate the agent with a tiny memory and both experiment intervals at
   zero. Call `agent.init` only; confirm agent-owned memory tensors and model
   roles.
5. Add a short real environment loop through the environment-integration
   route. Only after that succeeds, enable checkpointing/logging and scale
   memory or parallelism.

Never classify a missing CUDA/MPS/vendor backend as fixed merely because a CPU
smoke passes. Carry the backend limitation to the final experiment record.
