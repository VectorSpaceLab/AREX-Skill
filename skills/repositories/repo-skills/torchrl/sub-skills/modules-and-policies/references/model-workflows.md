# Model-based, planner, wrapper, and value-normalization workflows

This reference routes TorchRL module families that are not simple feed-forward actors but still live in the module/policy layer. Treat these APIs as TensorDict module components unless a task explicitly asks for loss/training-loop wiring.

## Workflow map

| Task phrase | Start with | Route notes |
| --- | --- | --- |
| "Dreamer actor", "RSSM", "world model", "latent dynamics" | `DreamerActor`, `WorldModel`, `WorldModelWrapper`, `RSSMPrior`, `RSSMPosterior`, encoders/decoders | Module assembly belongs here; Dreamer losses and training loops belong to objectives/training. |
| "Decision Transformer policy" | `DecisionTransformer`, `DTActor`, `OnlineDTActor`, `DecisionTransformerInferenceWrapper` | Base model/wrapper routing belongs here; offline RL losses and datasets belong elsewhere. |
| "planner", "MPC", "CEM", "MPPI" | `CEMPlanner`, `MPPIPlanner` | Requires an environment/model with specs and reward keys; environment construction routes to env workflows. |
| "MCTS" or tree-search score | `torchrl.modules.mcts` score classes | Score module selection belongs here; search-loop ownership depends on caller. |
| "normalize returns/values" | `ValueNorm`, `RunningValueNorm`, `PopArtValueNorm`, value transforms | Module state/update semantics live here; objective loss wiring belongs to training workflows. |
| "pretrained model policy wrapper" | policy wrapper classes and TensorDict keys | Check required external model dependencies before using LLM/VLA wrappers. |

## World-model components

TorchRL separates model-based building blocks into TensorDict-aware modules and lower-level neural networks.

Typical world-model assembly:

```text
encoder:       observation keys -> latent or embedding keys
dynamics:      latent/action keys -> next latent keys
reward_head:   latent/action keys -> ('next', 'reward') or custom reward key
done_head:     optional -> done/terminated keys
decoder:       optional latent -> reconstructed observation keys
WorldModel:    composes encoder, dynamics, reward, done, decoder
```

Guidelines:

- Keep transition outputs under `('next', ...)` keys when they represent predicted next-step quantities.
- Keep reward and done key names aligned with the environment/loss code that will consume them.
- Use `WorldModelWrapper` when the model is a transition model plus reward model and you need a compact TensorDict sequence.
- Do not mix imagined rollout TensorDicts with real collector TensorDicts unless the key layout is deliberately identical.

## Dreamer-style modules

Dreamer components include actor networks, observation encoders/decoders, RSSM prior/posterior modules, rollout modules, and DreamerV3 MLP utilities.

A safe routing plan:

1. Build and smoke-test the RSSM/prior/posterior modules on small TensorDicts.
2. Build `DreamerActor` or the chosen policy head and confirm action distribution parameters and action spec alignment.
3. Compose world-model rollout modules only after the one-step key contract works.
4. Route loss, lambda returns, actor/value objectives, replay sequence sampling, and SOTA configuration to objectives/training.

Dreamer components often use latent keys rather than direct environment observations. Name those keys explicitly (`'belief'`, `'state'`, `'latent'`, or project-specific nested keys) and document which module writes each one.

## Decision Transformer modules

Decision Transformer APIs operate on state/action/return/time-token style sequences rather than ordinary single-step observations. The module layer handles:

- Constructing `DecisionTransformer` with `state_dim`, `action_dim`, and transformer config.
- Wrapping the model with actor/inference wrappers that read/write TensorDict keys.
- Selecting the output distribution class, for example a bounded continuous distribution for actions.

Practical checks:

- Sequence length, return-to-go, timestep, state, and action tensors must share compatible batch/time dimensions.
- Inference wrappers maintain context windows; verify reset behaviour at episode boundaries before using them in collectors.
- Optional transformer dependencies may be required. If unavailable, keep the workflow at API-routing level instead of attempting model execution.

## Planner APIs

TorchRL planners are policy-like modules that search over actions using an environment or model.

| Planner | Typical constructor inputs | Use case |
| --- | --- | --- |
| `CEMPlanner` | environment/model, planning horizon, optimization steps, number of candidates, top-k, reward key, action key | Cross-entropy method planning over candidate action sequences. |
| `MPPIPlanner` | environment/model, advantage module, temperature, planning horizon, optimization steps, candidates/top-k, reward/action keys | Model-predictive path integral style planning with an advantage or scoring module. |

Planner checklist:

1. Confirm the environment/model accepts the same action key the planner writes.
2. Confirm the reward key is where the model/environment writes reward, often `('next', 'reward')`.
3. Keep planning horizon and candidate counts tiny in smoke tests; scale only after key contracts pass.
4. If the planner steps a real environment, route environment setup/spec validation to env workflows.
5. If the planner is part of a training objective, route losses and optimizer updates to objectives/training.

## MCTS score modules

The MCTS package provides score modules and enumerations for tree-search exploration/exploitation scores. Use this sub-skill to select and parameterize scoring modules, then hand off full search-loop integration to the task owner that owns the environment/model loop.

When debugging MCTS score usage, inspect:

- Which TensorDict keys contain visit counts, priors, values, and rewards.
- Whether score tensors preserve batch/tree dimensions.
- Whether the chosen score rule assumes normalized values or bounded rewards.

## Value normalization and transforms

TorchRL value-normalization modules maintain running statistics or output-layer corrections for value predictions.

| API | Role | Notes |
| --- | --- | --- |
| `ValueNorm` | Base normalization module with running location/scale state | Use for explicit normalize/denormalize operations. |
| `RunningValueNorm` | Running-statistics normalization | Useful when target scales drift during training. |
| `PopArtValueNorm` | PopArt normalization with output-preserving updates | Common for stabilizing value heads while preserving unnormalized predictions. |
| Value transforms | Invertible transforms such as symlog/symexp or signed hyperbolic mappings | Ensure inverse transform is applied before bootstrapping if required. |

Guidelines:

- Keep normalized prediction keys distinct from raw value/return keys when both exist.
- Save and restore normalization state with the module state dict.
- When a loss expects raw values, either configure the loss-aware value estimator or invert the transform before computing targets.
- For multi-agent values, decide whether statistics are shared across agents or per-agent; shape the normalization module accordingly.

## Policy wrappers and pretrained components

TorchRL includes wrappers for action post-processing, multi-step actor behaviour, pretrained model adapters, and specialized architecture families. Use the same TensorDict checklist for all of them:

1. What keys does the wrapper read?
2. What keys does it add or overwrite?
3. Does it require an action/value spec?
4. Does it alter interaction mode, random sampling, or log-prob computation?
5. Does it require optional model-serving, tokenizer, simulator, or dataset dependencies?

If optional serving/model dependencies are required, route to the LLM/VLA/service workflow rather than installing or launching services from this sub-skill.

## Minimal module-level validation

For any model-based or wrapper task, before adding training:

```text
small TensorDict input
  -> module forward
  -> assert expected keys
  -> assert batch/time/agent dimensions preserved
  -> assert action/value bounds or dtype
  -> assert no unintended key overwrite
```

Only after these assertions pass should a future agent wire collectors, replay buffers, losses, trainers, or long-running examples.
