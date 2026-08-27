# Training troubleshooting

Start by preserving the exact command, Python/TensorFlow/TFP versions, GPU
listing, effective `config.yaml`, and the last terminal exception. Diagnose in
the order below; do not repeatedly restart a long run against the same
unresolved gate.

## No GPU found or GPU is invisible

Native `python -m dreamerv2.train` intentionally asserts that TensorFlow sees
at least one GPU and prints:

```text
No GPU found. To actually train on CPU remove this assert.
```

Check the process that will run training, not a different shell:

```sh
python - <<'PY'
import tensorflow as tf
print(tf.__version__)
print(tf.config.experimental.list_physical_devices('GPU'))
PY
```

An empty list means native training is blocked; `--precision 32`, `--jit False`,
or `debug` do not make it CPU-safe. Check driver/container GPU exposure,
CUDA/cuDNN compatibility, and that `CUDA_VISIBLE_DEVICES` did not hide all
cards. A public API import or tiny CPU API experiment can validate wrappers and
serialization, but is not a substitute for the native GPU gate. If the GPU is
visible but allocation fails, continue with the OOM section rather than
removing the assertion.

## Modern TensorFlow or mixed-precision incompatibility

This release is from the TensorFlow 2.6 era. The native precision-16 branch
imports `tensorflow.keras.mixed_precision.experimental`, an API removed or
changed in newer TensorFlow. `setup.py` is unpinned, so a fresh installation
can silently select an incompatible modern stack. Use one coherent verified
variant, for example TensorFlow 2.6.0 with TensorFlow Probability 0.14.1 and a
legacy Gym 0.23-style environment, or use the matching Docker image and its
own package pins. Do not combine the Dockerfile's TensorFlow 2.4.2 base with
the 2.6-era host packages.

For a first diagnostic, override the native policy selection:

```sh
python -m dreamerv2.train --help
python -m dreamerv2.train \
  --logdir "$RUN_DIR" --configs atari debug \
  --task atari_pong --steps 300 --precision 32 \
  --envs_parallel none
```

Precision 32 avoids the legacy mixed-precision policy branch, but it does not
make every modern TensorFlow/TFP combination supported: agent imports,
optimizer behavior, distribution APIs, and CUDA kernels still need the same
era-compatible stack. If the API is used, note that `config.precision` does
not itself set a TensorFlow policy; configure such a policy before import/use
only if the chosen API is verified.

## Installed `dreamerv2` launcher cannot find `configs.yaml`

The distribution exposes `dreamerv2=dreamerv2.train:main`, but this source
runner resolves the YAML as `Path(sys.argv[0]).parent / 'configs.yaml'`.
An installed console script therefore looks beside its launcher, not beside
package data. A typical failure mentions a missing `configs.yaml` near a bin
folder. Use:

```sh
python -m dreamerv2.train --help
```

and use the same module form for real training. Do not copy a second YAML next
to the launcher or rely on the current working directory; that masks the
packaging defect and is not portable.

## Empty replay, short episodes, or dataset sampling failure

A replay directory being present does not mean it contains usable episodes.
`Replay.add_episode` skips any episode with effective length below
`replay.minlen`, where effective length is the number of actions minus one.
The dataset additionally needs `dataset.length`; its iterator samples from
completed episodes and batches with `drop_remainder=True`.

Inspect without training:

```sh
python - <<'PY' "$RUN_DIR/train_episodes"
import pathlib, sys
for p in sorted(pathlib.Path(sys.argv[1]).glob('*.npz')):
  import numpy as np
  with np.load(p) as ep:
    print(p.name, 'effective_length=', len(ep['action']) - 1)
PY
```

If the list is empty or every length is too short, increase the custom
environment's episode duration or lower `replay.minlen`, `replay.maxlen`, and
`dataset.length` together in a compatible debug config. Then collect enough
complete episodes with `prefill`; merely increasing `steps` does not repair a
run that never reaches `is_last=True`. A never-ending environment can leave
prefill in an ongoing in-memory episode because the default `ongoing` is false.
For native evaluation, also ensure an eval episode reaches the configured
`dataset.length`, or the evaluation replay will be unusable.

## Logdir permission or output collision

The runner/API creates the configured directory and writes `config.yaml`
immediately. Later it appends `metrics.jsonl`, creates TensorBoard events, and
pickles `variables.pkl`. Test the exact parent and choose a new run directory:

```sh
mkdir -p "$RUN_DIR"
test -w "$RUN_DIR"
touch "$RUN_DIR/.probe" && rm "$RUN_DIR/.probe"
```

Do not use a file such as `/dev/null` as a directory, a read-only mount, or a
shared directory with another active process. A config file without metrics
usually means the run failed after startup; a checkpoint without new metrics
may mean the process stopped between saves and logger flushes. Keep partial
artifacts for diagnosis and resume from a copied directory.

## Out-of-memory (OOM)

First stop the run and identify whether memory is GPU, host, or replay disk
pressure. For a bounded retry, reduce in this order:

```text
--envs 1 --envs_parallel none
--dataset.batch 2
--dataset.length 10
--replay.minlen 10 --replay.maxlen 10
--render_size 32,32       # only when the selected environment/config supports it
--precision 16            # only after the legacy policy path is verified
```

Use `debug` as a starting cadence, reduce model widths/layers through the
configuration route, and disable video keys in a programmatically constructed
API config if video memory is the issue. `memory_growth` is enabled by the
native runner but does not make an oversized model fit. Do not silently change
observation key filters or action shapes to save memory; revalidate the
environment/model contract. If precision 16 produces unstable loss scaling,
prefer precision 32 and a smaller model rather than accepting NaNs.

## Precision, NaN, or infinite gradient norms

The native assertion permits only `precision` 16 or 32; no other value is a
valid CLI setting. Defaults use 16. Mixed precision can print infinite raw
gradient norms as described by the release documentation because loss scaling
is active; that message alone is not proof of failure. Treat NaN losses,
failed `check_numerics`, or a run that stops making finite metrics as failure.

Retry a bounded segment with:

```sh
python -m dreamerv2.train \
  --logdir "$RETRY_DIR" --configs <preset> debug \
  --precision 32 --jit False --steps 300 \
  --envs_parallel none
```

Do not switch precision in place on a resume without checking checkpoint
compatibility and the TensorFlow policy. API runs do not select mixed
precision from `config.precision`; make the policy decision explicit and test
it before relying on the config value.

## Checkpoint mismatch or unsafe resume

`variables.pkl` is a pickle of model/module variables. It does not restore
replay files, `config.yaml`, the counter, or a partial episode. The runner
reconstructs its counter from replay filenames and calls one dataset batch
before `Agent.load`. Consequently these cases are distinct:

- **Shape assignment error:** model dimensions, heads, action distribution, or
  observation keys differ. Use the original saved config and environment, or
  start a new logdir.
- **Empty/short replay before load:** `variables.pkl` may be valid, but
  `next(dataset)` cannot sample. Restore replay or collect complete episodes;
  increasing `prefill` above the current replay step count is a safe planning
  tool only when the environment can finish episodes.
- **Replay/config disagreement:** filenames give a plausible step count while
  `config.yaml` changes `action_repeat`, sequence lengths, or schemas. Do not
  claim continuity; copy the run, align values, and verify a dataset batch.
- **Corrupt pickle:** preserve the file, check its size and traceback, and use
  a known-good checkpoint or restart. Never unpickle untrusted files.

A safe plan for the difficult case is: copy the run, compare `config.yaml`,
count valid `.npz` lengths, set a compatible larger prefill target, collect
new accepted episodes, verify a dataset batch, then resume. If architecture
cannot be matched, make a fresh run and record the checkpoint as diagnostic
only.

## External environment or asset dependency failure

Native task names select only these suites:

```text
dmc_<domain>_<task>       dm_control, MuJoCo/rendering and possible key
atari_<game>              legacy Gym Atari integration, atari_py, ROMs
crafter_reward/noreward    crafter package and runtime assets
```

Missing registrations, ROMs, MuJoCo libraries/keys, EGL/OpenGL, Crafter, or
MiniGrid packages are environment failures, not replay or model failures.
Use the environment route to validate the exact observation/action contract.
A custom Gym environment is not a fourth native CLI suite: instantiate it in
Python and call `dv2.train(raw_env, config)`.

The Dockerfile is an alternative GPU image based on TensorFlow 2.4.2. It
installs ffmpeg and external packages and downloads Atari ROMs and MuJoCo
files; its MuJoCo key argument is sensitive. Inspect or rebuild it only when
those downloads, licenses, network access, and mounted logdir are approved.
A safe GPU visibility check is:

```sh
docker run --rm --gpus all tensorflow/tensorflow:2.4.2-gpu nvidia-smi
```

Do not run the image's default long training command just to test dependency
availability. Use package imports, environment reset/step checks, and a
bounded run after assets are deliberately provisioned.

## Missing metrics, TensorBoard, or ffmpeg

`metrics.jsonl` is created only after a scalar logger flush; `variables.pkl`
does not imply metrics. JSONL contains scalar values only. TensorBoard files
are created lazily. Missing `ffmpeg` affects animated video encoding and the
logger falls back to an image summary; it should not block scalar JSONL unless
a malformed video shape triggers a separate error. Use a JSONL-only custom
output for a bounded API smoke and route all artifact interpretation to
[evaluation](../../evaluation/SKILL.md).
