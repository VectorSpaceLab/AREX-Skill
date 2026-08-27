# DreamerV2 cross-cutting troubleshooting

Read this reference when installation, import, backend detection, or a failure
crosses more than one sub-skill. Keep the focused route open for workflow
specific recovery.

## Import or dependency failures

**Symptom:** `ImportError` from `tensorflow.keras.mixed_precision.experimental`,
TensorFlow Probability incompatibility, protobuf descriptor errors, or NumPy
ABI errors.

**Cause:** this 2.2.0 release uses TensorFlow 2.6-era APIs and legacy Gym. A
fresh environment with unpinned dependencies can resolve modern Keras,
TensorFlow Probability, NumPy, or Gym versions that no longer expose those
APIs. Use a coherent pinned stack rather than patching one import at a time:
TensorFlow 2.6.0, TensorFlow Probability 0.14.1, Gym 0.23.1, NumPy 1.19.5,
and `ruamel.yaml<0.18`. If TensorFlow 2.6 reports protobuf descriptor errors,
verify a protobuf version compatible with the old wheel (the verified stack
uses protobuf 3.20.x).

Run `python -m pip check`, then import `tensorflow`, `tensorflow_probability`,
`dreamerv2.api`, and `dreamerv2.common` from the same Python. Do not use a
successful import from a different shell or checkout as proof.

## No GPU found

**Symptom:** native training stops at `No GPU found. To actually train on CPU
remove this assert.`

**Cause:** `dreamerv2.train` intentionally requires a TensorFlow GPU. Check
`tf.config.list_physical_devices('GPU')`, the driver/container passthrough, and
that the TensorFlow wheel/runtime matches the host. `nvidia-smi` alone is not
sufficient. A CPU import can validate configuration, wrappers, or plotting but
cannot validate this native capability. Either repair the CUDA runtime, use the
custom API only for a deliberately bounded compatibility experiment, or record
native training as blocked.

## Installed `dreamerv2` command fails

**Symptom:** the console command raises `FileNotFoundError` for `configs.yaml`
under the environment's `bin/` directory.

**Cause:** the source runner uses `pathlib.Path(sys.argv[0]).parent` rather than
its installed module location. Use `python -m dreamerv2.train ...`, which
resolves the package module path, and record this as a release defect rather
than copying `configs.yaml` beside an arbitrary launcher. Do not claim the
console entry point passed a smoke check.

## Optional environment failures

- Atari construction needs the old Gym Atari integration, `atari_py`, and
  separately imported ROMs. A missing ROM is not fixed by changing `--task`.
- DMC construction needs a compatible `dm_control`, MuJoCo, rendering backend
  (`MUJOCO_GL=egl` is used by the adapter), and sometimes legacy asset/key setup.
  Test one environment reset and one render before training.
- Crafter needs the `crafter` package and its runtime data.
- Custom Gym registrations and system libraries remain the caller's
  responsibility. Keep the legacy four-return `reset`/`step` semantics or add a
  tested compatibility shim for modern environments.

The package imports these suites lazily, so core API inspection can succeed
while a suite-specific run still fails. Keep the two gates separate.

## Logdir and replay failures

**Symptom:** permission errors, `IndexError`/empty dataset at the first train
step, or repeated `Skipping short episode` messages.

Use a fresh writable logdir and verify that episodes are at least
`replay.minlen` actions plus the initial transition. `prefill` counts target
steps but does not guarantee a valid sequence of `dataset.length`. Inspect
`train_episodes/*.npz`, `replay.minlen`, `replay.maxlen`, and
`dataset.length` before reducing thresholds. Never let two processes write one
logdir.

**Symptom:** a checkpoint exists but resume fails. `variables.pkl` stores model
variables only; the runner reconstructs the step from replay filenames and
needs a dataset batch before loading. Restore matching replay/config/model
schema or copy the run to a new logdir and collect compatible complete episodes.
Do not force incompatible observation keys, action dimensions, precision, or
model widths into an old checkpoint.

## Numerical and memory failures

If loss or gradient checks report NaN/Inf, stop and preserve the effective
config. Try `--precision 32`, `--jit False`, smaller batch/model settings, and a
short debug run only after confirming the data contract. Mixed precision is a
performance option, not a requirement for reproducibility. TensorFlow GPU OOM
may come from multiple visible GPUs or `envs`; start with serial environments,
smaller debug settings, and explicit memory-growth behavior.

## Cross-route escalation

- Wrong flag, preset, or schedule: [configuration](../sub-skills/configuration/SKILL.md).
- Missing key, dtype, bound, or task name: [environments](../sub-skills/environments/SKILL.md).
- Replay, checkpoint, GPU, or API lifecycle: [training](../sub-skills/training/SKILL.md).
- Missing metric, plot layout, baseline, or TensorBoard artifact:
  [evaluation](../sub-skills/evaluation/SKILL.md).
