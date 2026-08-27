# TensorFlow Agent Troubleshooting

Use this guide for Acme TensorFlow/Sonnet installation, graph/eager debugging, network shape errors, Launchpad distributed runs, OpenSpiel legal actions, and Gym/Atari environment setup.

## Install And Version Pins

Symptoms:

- `ModuleNotFoundError: No module named 'tensorflow'`, `sonnet`, `trfl`, `reverb`, or `launchpad`.
- ABI/import errors after installing a newer TensorFlow, TensorFlow Probability, Reverb, or Launchpad version.
- A TF agent import works in source-only inspection but real learner execution fails.

Likely cause:

- The core `dm-acme` requirements do not include the TF runtime stack.
- Acme 0.4.1 pins the TF extra stack: `tensorflow==2.8.0`, `tensorflow_probability==0.15.0`, `tensorflow_datasets==4.6.0`, `dm-reverb==0.7.2`, `dm-launchpad==0.5.2`, plus `dm-sonnet` and `trfl`.

Recovery:

- Install a TF-capable Acme environment with the TF extra or equivalent pinned packages.
- Avoid mixing arbitrary newer TF/TFP/Reverb/Launchpad wheels unless the user explicitly accepts compatibility work.
- If the user only needs algorithm selection or code review, use `scripts/select_tf_agent.py`; it intentionally avoids importing TensorFlow.

## Debugging Learners: Eager vs `@tf.function`

Symptoms:

- The learner fails inside a graph trace with unclear TensorFlow stack frames.
- Python-side prints or breakpoints do not show expected values.
- Code works in a small eager snippet but fails after the learner `_step()` is traced.

Evidence-backed workflow:

1. Locate the learner `_step()` method; Acme TF learners decorate these methods with `@tf.function` for speed.
2. Temporarily comment out or bypass the decorator in the working copy while debugging.
3. Run one learner step or the smallest failing network/loss call in eager mode.
4. Inspect tensor shapes, dtypes, nested structure, and distribution objects.
5. Restore `@tf.function` once eager mode is correct; leaving it eager makes learners slow.

Rare graph-only issues can still occur with exotic ops or unsupported dtypes. In that case, reduce the failure to a small `tf.function` wrapper around the suspect network or loss.

## Sonnet Shape And Dtype Errors

Symptoms:

- `ValueError` from `snt.Linear` or `snt.nets.MLP` about unknown input size.
- Critic receives only observations, or `CriticMultiplexer` receives incorrectly structured `(observation, action)` inputs.
- Policy output shape does not match a bounded action spec.
- Distributional critic loss fails due to mismatched atom/support dimensions.
- Snapshot export fails because variables or input signatures were not created.

Recovery checklist:

- Create variables with representative input specs before saving or launching: use `acme.tf.utils.create_variables(network, input_spec)` when possible.
- For actor-critic critics, validate with a batched observation and a batched action.
- For bounded continuous policies, end with `networks.TanhToSpec(action_spec)` or another action-bound transform when the agent expects spec-shaped actions.
- For stochastic policies, distinguish distribution outputs from sampled/mode actions; add `networks.StochasticModeHead()` only for greedy/evaluation action selection.
- For distributional critics, use `networks.DiscreteValuedHead(vmin, vmax, num_atoms)` and keep loss support dimensions aligned.
- For recurrent agents, ensure `initial_state(batch_size)` exists and sequence axes match the replay sequence configuration.

## Launchpad Distributed Run Failures

Symptoms:

- `lp_launch_type` errors, workers never start, ports collide, or child processes fail imports.
- Actors see stale variables or evaluator performance does not change.
- Reverb server/table creation errors appear before learner starts.

Recovery:

- Confirm `dm-launchpad` and `dm-reverb` are installed with versions compatible with the TF stack.
- Start with local multi-threaded launch (`local_mt`) for debugging import/shape errors; move to local multi-process (`local_mp`) only after the program builds cleanly.
- Keep `environment_factory` and `network_factory` top-level or otherwise pickle-safe for multi-process launches.
- Make every factory return fresh instances; do not share a global environment or Sonnet module across Launchpad nodes.
- Reduce `num_actors`, replay size, and prefetch size for local smoke tests.
- Inspect distributed constructor `variable_update_period` if actors are not receiving learner updates.
- Route Reverb table, limiter, adder, and dataset iterator failures to `replay-and-data` after confirming the TF agent family.

## OpenSpiel And Legal Actions

Symptoms:

- DQN chooses illegal actions.
- Action logits/Q-values have the wrong trailing dimension.
- Legal-action masks are missing or named differently than the network expects.
- `EpsilonGreedy` samples invalid actions or divides by zero.

Recovery:

- Use `acme.tf.networks.legal_actions.MaskedSequential` so illegal action values are replaced by a large negative penalty.
- Add `acme.tf.networks.legal_actions.EpsilonGreedy(epsilon=..., threshold=...)` when the output should be a sampled epsilon-greedy action.
- Confirm the final network dimension equals the OpenSpiel action count.
- Confirm each observation includes a legal-action mask and at least one legal action.
- Set the threshold so legal action values exceed it and masked illegal values do not.

## Gym, Atari, Bsuite, And Control Suite Environment Issues

Symptoms:

- Atari ROM errors, Gym version conflicts, `dm_control` import/rendering failures, pygame import errors, or Bsuite missing.
- Environment spec action type does not match the selected TF agent.

Recovery:

- Environment examples require the `envs` extra family: `atari-py`, `bsuite`, `dm-control`, `gym==0.25.0`, `gym[atari]`, `pygame==2.1.0`, and `rlds`.
- For Atari, install/provide ROMs according to the Atari package expectations before debugging Acme networks.
- For headless Control Suite, check MuJoCo/rendering system packages separately from Acme.
- Match algorithm to action spec: DQN/R2D2/IMPALA/MCTS/DQfD/R2D3 for discrete action specs; DDPG/D4PG/MPO/DMPO/MO-MPO/SVG0 for bounded continuous action specs.
- If the environment works but the agent fails, print `environment_spec.observations` and `environment_spec.actions` and validate network input/output shapes in eager mode.

## Saver And Snapshot Failures

Symptoms:

- Checkpoint restore silently misses variables or complains about object graph mismatch.
- Snapshotter fails to trace a module.
- SavedModel export works for feed-forward networks but fails for recurrent modules.

Recovery:

- Use `Checkpointer` for restartable training state and recreate the same object graph before `restore()`.
- Use `Snapshotter` for self-contained module export after a representative call has created variables.
- Verify object keys in `objects_to_save` are stable and unique.
- For recurrent modules, verify the module exposes a traceable `initial_state`; Acme recurrent wrappers include saver-specific input-signature support.
- Force a save (`save(force=True)`) only for explicit smoke checks; normal training relies on `time_delta_minutes` throttling.

## Offline And Demonstration Learner Issues

Symptoms:

- `BCLearner`, `DiscreteBCQLearner`, `DQfD`, or `R2D3` fails on dataset iteration.
- Demonstration ratio appears ignored or batches contain unexpected fields.

Recovery:

- Verify the dataset produces the learner's expected transition or sequence structure before blaming the network.
- Keep behavior-cloning policy output compatible with the action spec: logits for discrete policies, spec-shaped actions or distributions for continuous policies.
- Route dataset conversion, table schemas, n-step transitions, sequence replay, and demonstration mixing mechanics to `replay-and-data`.

## Fast Triage Questions

Ask these before changing code:

- Is this a TF-capable runtime or just core `dm-acme` installed?
- Is the action spec discrete or bounded continuous?
- Is the failure in a single-process class, a distributed Launchpad program, or a learner-only offline script?
- Does the same network call succeed in eager mode with a representative batched observation/action?
- Are Reverb/Launchpad errors occurring before any TensorFlow network or learner code runs?
