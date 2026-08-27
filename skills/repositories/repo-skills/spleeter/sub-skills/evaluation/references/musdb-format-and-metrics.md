# MUSDB format and metrics

Spleeter evaluation expects a MUSDB-style dataset root with a `test` subset. The command separates each test `mixture.wav`, then `museval` compares the separated estimates against source files in the same song directory.

## Required `mus_dir` layout

Minimum 4-stem evaluation layout:

```text
MUSDB_ROOT/
  test/
    song0/
      mixture.wav
      vocals.wav
      drums.wav
      bass.wav
      other.wav
    song1/
      mixture.wav
      vocals.wav
      drums.wav
      bass.wav
      other.wav
```

Rules to keep straight:

- `mixture.wav` is the input audio Spleeter separates.
- `vocals.wav`, `drums.wav`, `bass.wav`, and `other.wav` are ground-truth files used by `museval`.
- Ground-truth files are not created by `spleeter evaluate`; they must already exist in `mus_dir`.
- Spleeter writes estimates separately under `OUTPUT/audio/test/<song>/`.
- Metrics are written under `OUTPUT/metrics/test/`.

The evaluation command locates songs with the pattern `MUSDB_ROOT/test/*/` and builds mixture inputs by appending `mixture.wav` to each song directory. A wrong root, missing `test` directory, empty test split, or missing mixtures can produce confusing downstream failures because no estimates or no comparable targets are available.

## Instruments and model match

The Spleeter evaluation helper compiles metrics for these instruments:

| Instrument | Expected ground-truth file |
| --- | --- |
| `vocals` | `vocals.wav` |
| `drums` | `drums.wav` |
| `bass` | `bass.wav` |
| `other` | `other.wav` |

Use a 4-stem model or local config for this standard MUSDB evaluation path. A 2-stem model does not produce `drums`, `bass`, and `other` estimates, and a 5-stem model produces an extra `piano` estimate that is not part of the compiled metric table in `spleeter.__main__._compile_metrics`.

## Metric files and compilation

`museval` writes one JSON file per evaluated song under:

```text
OUTPUT/metrics/test/<song>.json
```

Spleeter then compiles the JSON files by reading `OUTPUT/metrics/test/*.json` and collecting these metrics for each instrument:

| Metric | Meaning in source-separation evaluation |
| --- | --- |
| `SDR` | Signal-to-distortion ratio; broad estimate quality indicator. |
| `SAR` | Signal-to-artifacts ratio; penalizes artifacts introduced by separation. |
| `SIR` | Signal-to-interference ratio; measures leakage from other sources. |
| `ISR` | Image-to-spatial-distortion ratio; spatial/image consistency metric used by `museval`. |

Compilation behavior in Spleeter 2.4.2:

1. For each song JSON, iterate over `targets`.
2. For each target instrument and each metric (`SDR`, `SAR`, `SIR`, `ISR`), read frame-level values.
3. Ignore frame values that are `NaN`.
4. Store the median of the remaining frame values for that song.
5. When logging the final summary, print the median across the collected per-song medians.

This means the returned metrics object is a dictionary of lists, not a single scalar table:

```python
{
    "vocals": {"SDR": [...], "SAR": [...], "SIR": [...], "ISR": [...]},
    "drums": {"SDR": [...], "SAR": [...], "SIR": [...], "ISR": [...]},
    "bass": {"SDR": [...], "SAR": [...], "SIR": [...], "ISR": [...]},
    "other": {"SDR": [...], "SAR": [...], "SIR": [...], "ISR": [...]},
}
```

If a song has only `NaN` frames for a metric, the median can be `NaN` and should be treated as an invalid or unsupported evaluation result for that source/metric.

## Tiny fake fixture

Use the bundled helper to create a deterministic MUSDB-like layout for smoke tests and documentation examples:

```bash
python scripts/create_eval_fixture.py ./tiny_musdb_eval
```

From this sub-skill directory, the script path is:

```bash
python scripts/create_eval_fixture.py OUTPUT_ROOT
```

From another working directory, call the script by its actual path in the generated skill tree. The helper creates:

```text
OUTPUT_ROOT/
  test/
    song0/
      mixture.wav
      vocals.wav
      drums.wav
      bass.wav
      other.wav
    song1/
      mixture.wav
      vocals.wav
      drums.wav
      bass.wav
      other.wav
```

The fake fixture is useful for layout checks, missing-file troubleshooting, and tiny command rehearsals. Its synthetic tones are not a meaningful benchmark; do not report the resulting SDR/SAR/SIR/ISR values as model quality.

## Source evidence notes

This layout and metric behavior are supported by `spleeter/__main__.py` evaluation constants and `_compile_metrics`, and the deterministic fake-fixture shape is adapted from `tests/test_eval.py` without requiring the original source checkout at runtime.
