# Evaluation troubleshooting

Use this page for `spleeter evaluate` problems. For generic separation failures, route to [separation troubleshooting](../../separation/references/troubleshooting.md). For cross-cutting install, TensorFlow, ffmpeg, model-cache, and platform issues, see the root [troubleshooting reference](../../../references/troubleshooting.md).

## Missing evaluation extra or exit code 10

Symptom:

- `spleeter evaluate ...` logs `Extra dependencies musdb and museval not found` and `Please install musdb and museval first, abort`.
- Process exits with status `10`.

Cause:

- The base Spleeter package can run the CLI, but evaluation imports optional `musdb` and `museval` packages inside the `evaluate` command.

Fix:

```bash
python -c "import musdb, museval"
pip install 'spleeter[evaluation]'
# or install compatible musdb and museval packages into the same environment
```

Do not continue to evaluation until both imports work in the same environment that runs `python -m spleeter`.

## Wrong `--mus_dir`

Symptoms:

- No song estimates appear under `OUTPUT/audio/test/`.
- Metrics directory is missing or empty.
- `musdb` reports that the dataset cannot be found or has no tracks.

Checks:

```bash
find MUSDB_ROOT/test -maxdepth 2 -type f -name 'mixture.wav'
```

Expected structure:

```text
MUSDB_ROOT/test/<song>/mixture.wav
```

Pass the dataset root as `--mus_dir`, not the `test` directory itself and not a single song directory.

## Missing mixture files

Symptom:

- A song directory exists but separation cannot load input audio, or no estimate is produced for that song.

Cause:

- Spleeter discovers song directories with `MUSDB_ROOT/test/*/`, then appends `mixture.wav` to each one. The mixture path must exist and be readable.

Fix:

```bash
find MUSDB_ROOT/test -mindepth 2 -maxdepth 2 -name mixture.wav -type f
```

Add or regenerate missing `mixture.wav` files before evaluation.

## Missing ground-truth source files

Symptoms:

- Separation estimates are created, but metric computation fails.
- A song has `mixture.wav` but is missing `vocals.wav`, `drums.wav`, `bass.wav`, or `other.wav`.

Cause:

- `mixture.wav` is enough for Spleeter separation, but `museval` needs ground-truth sources to score the estimates. Do not mistake `OUTPUT/audio/test/<song>/<instrument>.wav` estimates for ground truth.

Fix:

```bash
for stem in vocals drums bass other; do
  find MUSDB_ROOT/test -mindepth 2 -maxdepth 2 -name "$stem.wav" -type f | wc -l
done
```

Every evaluated song should contain all four source files for the standard 4-stem metric path.

## Model, cache, or network failures

Symptoms:

- Evaluation fails before metrics start.
- Logs mention model download, checksum, descriptor, cache, or provider errors.
- First run hangs or fails while using `spleeter:4stems` or another pretrained descriptor.

Cause:

- Evaluation calls Spleeter separation before `museval`. Pretrained descriptors may need model assets from a cache or network download.

Fixes:

- Prewarm the model by running a tiny separation smoke with the same `--params_filename`.
- Ensure the model cache location is writable and allowed by policy.
- Use a local config/checkpoint when network access is forbidden.
- Consult the root [models/configuration reference](../../../references/models-and-configuration.md) for descriptor and cache controls.

## Metrics JSON issues

Symptoms:

- `OUTPUT/audio/test/<song>/` contains estimates, but compiled metrics are empty, missing instruments, or contain `NaN`.
- Spleeter fails while reading JSON from `OUTPUT/metrics/test/*.json`.

Checks:

```bash
find OUTPUT/metrics/test -maxdepth 1 -type f -name '*.json'
python - <<'PY'
import json, glob
for path in glob.glob('OUTPUT/metrics/test/*.json'):
    with open(path) as f:
        data = json.load(f)
    print(path, [target.get('name') for target in data.get('targets', [])])
PY
```

Common causes:

- `museval` did not run or wrote to a different output directory.
- Estimate directory names do not match MUSDB song names.
- Source or estimate files are silent, too short, malformed, or missing.
- All frame values for a metric are `NaN`, leaving no meaningful median.

## Runtime cost or apparent slowness

Symptoms:

- Long startup before any evaluation output.
- High CPU usage or memory pressure.
- Full dataset evaluation takes much longer than a CLI smoke check.

Cause:

- TensorFlow/model loading happens first, every test mixture is separated, and `museval` computes frame-level metrics afterwards.

Fixes:

- Start with the bundled fake fixture or a one-song subset to verify layout and dependencies.
- Keep `--mwf` off unless needed, because MWF adds cost.
- Use an explicit `--output_path` and monitor `audio/test` before expecting `metrics/test`.
- Treat full MUSDB evaluation as a benchmark run requiring user-approved time and resources.

## Optional GPU caveat

Spleeter can benefit from GPU acceleration in suitable TensorFlow environments, but GPU is optional and unverified for this skill. If TensorFlow logs CUDA or device warnings while falling back to CPU, do not treat that as an evaluation failure unless the user explicitly required GPU execution.

Only promise GPU acceleration after the target environment independently verifies TensorFlow GPU devices and matching CUDA/cuDNN libraries.

## Fixture-specific checks

For synthetic layout debugging, create a deterministic tiny dataset:

```bash
python scripts/create_eval_fixture.py ./tiny_musdb_eval
```

Then deliberately check difficult cases:

- Remove `test/song0/bass.wav` and confirm the guide routes this as a ground-truth source problem, not a separation output problem.
- Try evaluation in a base install without `musdb`/`museval` and confirm exit code `10` plus the missing-extra log path.
