# JAX Agent Troubleshooting

## Import And Optional Dependency Failures

### `No module named jax` or `No module named jaxlib`

Acme core requirements do not include JAX. Install the JAX extra compatible with Acme 0.4.1, or pin the equivalent versions manually:

- `jax==0.4.3`
- `jaxlib==0.4.3`
- `chex`, `dm-haiku`, `flax`, `optax`, `rlax`

JAX/JAXLIB wheels are platform-, Python-, and accelerator-specific. If pip cannot find `jaxlib==0.4.3`, check Python version, OS, CPU/GPU/TPU wheel availability, and whether the environment is too new for that pin.

### TensorFlow, Reverb, or Launchpad imports fail in a JAX workflow

This is expected if only core Acme is installed. Acme JAX experiment runners import shared infrastructure:

- `reverb` for online replay-backed runners;
- TensorFlow savers and `jax2tf` snapshotting paths;
- `launchpad` for distributed programs;
- `tensorflow_datasets` for several offline examples.

The JAX extra includes the shared stack: `tensorflow==2.8.0`, `tensorflow_probability==0.15.0`, `tensorflow_datasets==4.6.0`, `dm-reverb==0.7.2`, and `dm-launchpad==0.5.2`. Do not switch to `acme.agents.tf.*` just because these imports appear; they are infrastructure dependencies used by JAX agents too.

### Environment packages fail

Install environment extras only when the chosen environment needs them:

- Atari workflows may need `atari-py` and `gym[atari]`.
- BSuite examples need `bsuite`.
- DeepMind Control tasks need `dm-control`.
- Gym examples in Acme 0.4.1 expect `gym==0.25.0`.
- MultiGrid examples need compatible `pygame==2.1.0` and environment wrappers.
- RLDS/TFDS offline datasets need `rlds` and `tensorflow_datasets`.

Keep environment troubleshooting separate from agent builder selection.

## Local vs Distributed Runner Mistakes

### Offline training accidentally uses an online runner

Symptoms:

- Code asks for `max_num_actor_steps` when the task should be learner-only.
- A replay server and actors are created for fixed offline data.
- The training loop interacts with the environment during learning.

Fix:

- Use `experiments.OfflineExperimentConfig` with `demonstration_dataset_factory` and `max_num_learner_steps`.
- Run `experiments.run_offline_experiment(...)` locally.
- Run `experiments.make_distributed_offline_experiment(...)` for Launchpad offline execution.
- Use `evaluator_factories=[]` or `num_eval_episodes=0` if no environment evaluation should happen.

### Online distributed run fails because Launchpad is missing

Use the local runner while prototyping:

```python
experiments.run_experiment(experiment=config, eval_every=..., num_eval_episodes=...)
```

Only switch to:

```python
program = experiments.make_distributed_experiment(experiment=config, num_actors=...)
lp.launch(program, xm_resources=...)
```

when `dm-launchpad`, Reverb, and the target launch mode are available.

### Inference server mode raises `TypeError` about policy type

`make_distributed_experiment(..., inference_server_config=...)` requires the experiment policy to be an `acme.agents.jax.actor_core.ActorCore`. Feed-forward policy functions must be wrapped by the builder or by `actor_core.batched_feed_forward_to_actor_core(...)` before inference-server mode can handle them.

## PRNG Key Problems

### Reusing the same key everywhere

Acme examples split keys for dataset sampling, learner initialization, evaluator actor initialization, and environment seeds. Follow the pattern:

```python
key = jax.random.PRNGKey(seed)
dataset_key, learner_key, eval_key = jax.random.split(key, 3)
```

Do not reuse the exact same key for dataset random sampling and learner initialization in a custom manual loop.

### Environment seed type mismatch

Distributed experiment code samples uint32 seeds with `acme.jax.utils.sample_uint32(environment_key)`. If a custom environment expects a Python `int`, convert or sample consistently in `environment_factory(seed)`.

## Spec, Dataset, And Network Mismatches

### Network factory built from the wrong spec

Symptoms:

- Shape mismatch during network initialization or policy application.
- Dataset observations/actions do not match `EnvironmentSpec`.
- Multiagent networks see normal arrays instead of dicts keyed by agent id.

Fix:

1. Build or pass a single `environment_spec` from the same environment wrapper that evaluation uses.
2. Use that spec in both `network_factory(spec)` and offline dataset conversion.
3. For offline data, validate that observations, actions, rewards, discounts, and extras have the structure expected by the chosen builder.
4. For multiagent data, use dict observations/rewards/actions keyed by string agent IDs and a shared scalar discount.

### SAC target entropy errors

`sac.target_entropy_from_env_spec(spec)` expects bounded continuous action specs with minimum `-1` and maximum `1` unless an explicit `target_entropy_per_dimension` is provided. If actions are not normalized to `[-1, 1]`, normalize/wrap the environment or specify entropy behavior deliberately.

### D4PG value support too narrow or too broad

D4PG uses a distributional critic. Tune `vmin` and `vmax` in `d4pg.make_networks(...)` to the reward scale. A practical rule is to set `vmax` near the discounted sum of maximum instantaneous rewards over an episode and `vmin=-vmax` for symmetric tasks.

### MBOP dataset or planner shape fails

MBOP assumes continuous, flattened observation and action spaces and normalized timestep-batched transition triples. Use the MBOP dataset helpers when adapting datasets:

- convert episodes to timestep-batched transitions;
- compute `NestedMeanStd` normalization statistics;
- normalize samples before learner updates;
- ensure `MPPIConfig.n_trajectories` is divisible by `MBOPConfig.num_networks` or the explicit ensemble size.

## Replay And Iterator Issues

### Local online run hangs before learning

`run_experiment` disables blocking inserts for local sequential actor/learner execution, but a builder-specific iterator can still wait for enough replay samples. Check:

- `min_replay_size` is not too high for the test run;
- `samples_per_insert` and tolerance are feasible;
- `batch_size * num_sgd_steps_per_step` is not larger than available samples;
- sequence agents such as IMPALA/R2D2 have compatible `sequence_length`, `burn_in_length`, `trace_length`, and `sequence_period`.

### Reverb memory pressure or checkpoint stalls

Replay buffers can be very large. For distributed runs, avoid aggressive `replay_checkpointing_time_delta_minutes`; replay checkpointing is asynchronous but can retain items temporarily and cause memory pressure.

### PWIL replay deadlock concerns

PWIL pre-fills replay in a concurrent learner thread to avoid potential Reverb deadlocks. When adapting PWIL, keep the demonstrations and replay prefill assumptions intact rather than replacing them with a synchronous one-shot insert path without testing.

## Evaluation And Checkpointing Surprises

### Default evaluator requires environment factory

If `evaluator_factories` is `None`, `ExperimentConfig` and `OfflineExperimentConfig` build a default evaluator. Offline configs raise a `ValueError` if no `environment_factory` is available and evaluators are not disabled. Set `evaluator_factories=[]` to disable evaluator creation.

### Deprecated policy factories override builder policy

`ExperimentConfig.policy_network_factory` and `eval_policy_network_factory` are deprecated but still take precedence in `experiments.make_policy(...)` when set. If behavior/eval policies seem inconsistent with a builder's `make_policy`, inspect those config fields.

### Snapshotting imports TensorFlow in JAX code

`acme.jax.snapshotter.JAXSnapshotter` uses `jax2tf` and `tf.saved_model.save`. TensorFlow import errors in snapshotting do not imply the agent itself is a TensorFlow agent. Disable snapshotting by omitting `make_snapshot_models` or setting `checkpointing=None` if snapshots are not needed.

## Expensive Examples And Safe Smoke Tests

Many baseline defaults run for hundreds of thousands or millions of environment steps and may download datasets or launch distributed programs. For safe adaptation:

- lower `num_steps`, `max_num_actor_steps`, or `max_num_learner_steps` sharply;
- set `run_distributed=False` while checking construction;
- set `num_eval_episodes=0` for a construction-only learner test;
- shrink replay sizes and batch sizes for local smoke tests only;
- avoid TFDS/D4RL dataset downloads unless the user explicitly wants data acquisition.

## Common Routing Corrections

- If the task is about `EnvironmentLoop`, wrappers, observers, or generic logging, use the core workflows skill.
- If the task is about Reverb tables, adders, TFDS/RLDS iterators, or data conversion internals, use the replay/data skill.
- If the task imports `acme.agents.tf.*`, use the TF agents skill.
- If the task imports TensorFlow only through JAX experiment infrastructure, stay in this JAX agents skill.
