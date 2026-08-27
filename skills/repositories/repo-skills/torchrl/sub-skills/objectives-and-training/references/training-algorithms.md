# Training algorithms and wiring patterns

This reference distills algorithm wiring from TorchRL objectives, trainer code, tutorials, tests, and reference-only SOTA recipes. It intentionally avoids long-running launch commands.

## Universal training loop contract

A TorchRL training loop usually has these pieces:

1. Environment and transforms produce a TensorDict transition layout with `"next"` fields. Route environment setup to `envs-and-transforms`.
2. Actor/critic modules expose the keys consumed by the loss. Route module construction to `modules-and-policies`.
3. A collector or offline dataset provides batches; replay buffers and priorities are owned by `collectors-and-replay`.
4. This sub-skill wires the objective, key remapping, value estimator, target updater, optimizer, and trainer hooks.

Manual-loop skeleton:

```python
loss = LossClass(...)
loss.set_keys(...)
loss.make_value_estimator(ValueEstimators.TD0, gamma=0.99)  # when applicable
updater = SoftUpdate(loss, tau=0.005)                       # when target params exist
optimizer = torch.optim.Adam(loss.parameters(), lr=lr)

for batch in data_source:
    if hasattr(loss, "value_estimator") and loss.value_estimator is not None:
        with torch.no_grad():
            loss.value_estimator(batch)
    loss_td = loss(batch)
    objective = sum(value for key, value in loss_td.items() if key.startswith("loss_"))
    objective.backward()
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)
    updater.step()
```

Adjust this skeleton for on-policy minibatches, replay priority updates, target update cadence, and logger/trainer hooks.

## On-policy PPO / A2C / REINFORCE

Use when data is collected by the current policy and reused for a bounded number of epochs.

- Losses: `ClipPPOLoss`, `KLPENPPOLoss`, `PPOLoss`, `A2CLoss`, `ReinforceLoss`.
- Estimator: `ValueEstimators.GAE` is default for PPO/A2C/REINFORCE families.
- Dependencies: probabilistic actor emits an action and log-prob key; critic emits a value key; collector batch carries `("next", "reward")`, `("next", "done")`, and `("next", "terminated")`.
- Recipe:
  1. Build policy and critic in `modules-and-policies`.
  2. Instantiate loss with actor and critic.
  3. `loss.set_keys(...)` for non-default action/value/reward/done keys.
  4. Build/apply GAE before each minibatch update.
  5. Use a no-replacement sampler or minibatch iterator for multiple epochs over one rollout batch.
- Multi-agent PPO can use `MAPPOLoss`/`IPPOLoss` directly, or `ClipPPOLoss` with explicit group keys as shown by the multi-agent tutorial. Keep `normalize_advantage=False` or exclude the agent dimension when the data shape would otherwise normalize across agents.

Minimal PPO key pattern:

```python
loss = ClipPPOLoss(actor_network=policy, critic_network=critic, clip_epsilon=0.2)
loss.set_keys(
    action="action",
    sample_log_prob="action_log_prob",
    value="state_value",
    reward="reward",
    done="done",
    terminated="terminated",
)
loss.make_value_estimator(ValueEstimators.GAE, gamma=0.99, lmbda=0.95)
with torch.no_grad():
    loss.value_estimator(batch)  # writes advantage and value_target
```

## DQN and distributional DQN

Use for discrete-action value learning with replay.

- Losses: `DQNLoss`, `DistributionalDQNLoss`.
- Module dependency: `QValueActor` or a module that writes `action_value`, chosen `action`, and chosen value fields consistent with the loss key map.
- Replay dependency: replay sample must carry root current fields and `"next"` fields; prioritized replay additionally needs `priority_weight` and a post-loss priority update.
- Target update: `delay_value=True` by default. Use `SoftUpdate(loss, eps=...)`/`tau=...` or `HardUpdate(loss, value_network_update_interval=...)`.
- Exploration schedules such as epsilon-greedy belong to module/collector setup, but the update step may be registered as a trainer `post_steps` hook.

DQN pattern:

```python
loss = DQNLoss(q_actor, delay_value=True, double_dqn=True, action_space="one-hot")
loss.set_keys(action="action", action_value="action_value", value="chosen_action_value")
loss.make_value_estimator(ValueEstimators.TD0, gamma=0.99)
target_updater = SoftUpdate(loss, tau=0.005)
```

## Continuous off-policy actor-critic

Use for continuous-control replay-based algorithms.

| Algorithm | Loss | Target updater | Distinct knobs |
| --- | --- | --- | --- |
| DDPG | `DDPGLoss` | Usually yes (`delay_value=True`) | Deterministic actor, one Q/value network, simpler TD target. |
| TD3 | `TD3Loss` | Usually yes (`delay_actor=True`, `delay_qvalue=True`) | Twin/ensemble Q, delayed actor updates, target policy smoothing via `policy_noise` and `noise_clip`. |
| SAC | `SACLoss` | Usually yes for Q/value targets | Stochastic actor, entropy temperature `alpha`, `target_entropy`, `skip_done_states`, optional value network for older variants. |
| TQC / REDQ / CrossQ | `TQCLoss`, `REDQLoss`, `CrossQLoss` | Algorithm-dependent delayed Q targets | Ensembles and quantile/dropout variants; inspect signatures and keys before editing. |

Operating checks:

- Pass `action_spec` when the loss needs action bounds, especially SAC/TQC/TD3/CQL variants.
- If actor output keys are nested or named differently, fix with `loss.set_keys(action=...)` and module `out_keys` alignment.
- Use `deactivate_vmap=True` only to debug unsupported vectorization in ensemble-Q modules.
- For prioritized replay, keep `priority_weight` in samples and call the replay buffer's priority update after loss computation.

## Offline and imitation losses

Use these when training from a static dataset or behavior-cloned trajectories.

- `CQLLoss` / `DiscreteCQLLoss`: conservative Q-learning; needs behavior actions, rewards, done/terminated, next observation/value fields, and Q/actor modules. Continuous CQL uses sampled/random actions and optional lagrange threshold.
- `IQLLoss` / `DiscreteIQLLoss`: expectile value regression and advantage-weighted actor update; needs actor, Q, value modules, and offline transitions.
- `TD3BCLoss`: TD3 with behavior-cloning regularization; ensure action data is the behavior action, not a freshly sampled actor action.
- `BCLoss`: supervised action matching; default action key is `"action"`; optional `pad_mask` excludes invalid sequence positions.
- `DTLoss`, `OnlineDTLoss`, `DiffusionBCLoss`: sequence or diffusion-specific action-target losses. Inspect default keys before mixing with RL replay logic.

Do not use collector freshness or replay priority assumptions for pure offline batches unless the selected algorithm recipe explicitly does so.

## Multi-agent losses

- `MAPPOLoss`: centralized critic with decentralized actor. Critic commonly writes `("agents", "state_value")`; actor writes `("agents", "action")`. Default estimator is `MAGAE`.
- `IPPOLoss`: independent critic counterpart. Same loss surface, but critic uses local agent observations rather than global state.
- `QMixerLoss`: local per-agent Q values plus a mixer network that writes a global team Q value. Default local keys are under `("agents", ...)`.

Multi-agent PPO rules:

```python
loss = MAPPOLoss(policy, critic, normalize_advantage_exclude_dims=(-2,))
loss.set_keys(
    action=("agents", "action"),
    value=("agents", "state_value"),
    reward="reward",
    done="done",
    terminated="terminated",
)
loss.make_value_estimator(ValueEstimators.MAGAE, gamma=0.99, lmbda=0.95)
```

If `reward`, `done`, or `terminated` are team-shared at root, the estimator may need expanded per-agent fields to match `("agents", ...)` value shapes. Follow the batch-shape convention from the multi-agent tests before blaming the loss.

## Model-based and auxiliary objectives

- Dreamer / DreamerV3 losses require latent state, model/reward/reconstruction outputs, and value/actor components. Keep keys synchronized across world model, actor, and value losses.
- `WorldModelLoss` is for learned dynamics/model objectives, not a generic actor-critic loss.
- `GAILLoss` needs discriminator inputs for expert and collector observation/action keys.
- `RNDLoss` defaults to reading `("next", "observation")`; it is usually an exploration bonus module that must be wired into reward/collector code.
- `ExponentialQuadraticCost`/PILCO-related surfaces are specialized model-based control utilities.

## Target-update cadence

- In manual loops, call `target_updater.step()` after optimizer updates that changed the source parameters.
- In `Trainer`, register target updates as `post_optim` via `TargetNetUpdaterHook` or a direct updater step. `post_loss` exists but is marked for replacement by `OptimizationStepper` and should not be the first choice for new code.
- Match the algorithm cadence: hard DQN target copy may happen every many optimizer steps; SAC/TD3/DDPG often use soft Polyak updates every optimizer step.

## SOTA recipe usage

The repository contains many `sota-implementations` scripts and `sota-check` launchers. Treat them as reference-only algorithm recipes unless the task explicitly asks to run a benchmark with the right dependencies and time budget. Extract from them:

- algorithm-specific hyperparameter names and config layout;
- environment family and optional extras required;
- collector/replay/loss/trainer composition;
- tests or smoke commands to add when changing the algorithm implementation.

For GRPO/SFT/RLHF and VLA-specific SOTA recipes, route implementation details to `llm-vla-and-services` while keeping generic loss-key conventions from this reference.
