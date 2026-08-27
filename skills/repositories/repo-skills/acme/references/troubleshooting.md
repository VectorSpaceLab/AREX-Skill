# Acme Troubleshooting

## Install And Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: dm_env` or `tree` | Core runtime requirements missing | Install `dm-acme` normally or add core dependencies from package metadata. |
| `ModuleNotFoundError: jax` during a seemingly core import | Acme logging utilities import JAX types, and top-level imports can touch logging | If running JAX agents, install the `jax` extra. If only inspecting source, import narrower modules or use source-backed signatures. |
| `ModuleNotFoundError: launchpad` | Environment-loop signal handling or distributed examples need Launchpad | Install the TF/JAX runtime extra that includes `dm-launchpad`, or avoid distributed launch paths. |
| `ModuleNotFoundError: reverb` | Replay datasets/adders or examples require Reverb | Install a compatible `dm-reverb` with the TensorFlow stack and verify table/server setup. |
| Backend pins cannot be resolved | Snapshot metadata pins older JAX/TF/Reverb versions | Choose between historical pinned environment, source-only inspection, or a modernized dependency set; do not silently mix versions for reproducibility claims. |

## Example Runtime Failures

- If an example starts a long training run, reduce flags such as `--num_steps`, `--eval_every`, or `--evaluation_episodes` before using it as a smoke test.
- If a Gym or Atari example fails before Acme code runs, check environment extras, Atari ROM installation, Gym version compatibility, and display/GL dependencies.
- If Control Suite examples fail, verify `dm-control` and MuJoCo/system library availability before debugging Acme networks.
- If Launchpad examples fail, first run a local single-process equivalent when available, then try `local_mt` before multi-process or cloud launch types.

## Shape And API Failures

- Always build `environment_spec = acme.specs.make_environment_spec(environment)` from the exact wrapped environment used at runtime.
- Check whether action specs are discrete or bounded continuous before selecting DQN/IMPALA/R2D2-style agents versus D4PG/TD3/SAC/MPO-style agents.
- For recurrent agents or sequence learners, route through `replay-and-data` to validate `sequence_length`, `period`, extras, and table signatures.
- For TensorFlow learner graph errors, route through `tf-agents` and consider eager-mode debugging before restoring `@tf.function`.
- For JAX PRNG or parameter-shape errors, route through `jax-agents` and inspect network factories, policy factories, and environment specs together.
