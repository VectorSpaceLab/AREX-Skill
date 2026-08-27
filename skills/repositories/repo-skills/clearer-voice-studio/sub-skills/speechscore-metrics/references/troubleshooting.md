# SpeechScore Troubleshooting

## Source-layout import fails

Symptoms:

- `ImportError: cannot import name 'SpeechScore' from 'speechscore'`
- `ModuleNotFoundError: No module named 'scores'`
- The wrong `speechscore` package is imported.

Cause:

- The usable factory lives in the `speechscore.py` module inside the SpeechScore component directory. If only the parent project directory is importable, Python can import the component package `__init__` instead, which does not expose `SpeechScore`. The source file also imports metric modules as `scores.*`, so the component directory itself must be importable.

Fixes:

- Run from the SpeechScore component directory; or
- pass `--speechscore-dir <speechscore_component_dir>` to the bundled helper; or
- in custom Python, insert the component directory at the front of `sys.path` before `from speechscore import SpeechScore`.

## Missing dependencies at import time

SpeechScore imports all metric modules when `speechscore.py` is imported. A missing dependency for an unselected metric can still break a light metric set.

Common missing packages:

- Core audio/scoring: `librosa`, `soundfile`, `resampy`, `numpy`, `scipy`, `museval`, `mir_eval`.
- PESQ/STOI family: `pesq`, `pystoi`.
- MCD: `pyworld`, `pysptk`, `fastdtw`.
- SRMR: `gammatone`.
- DNSMOS: `onnxruntime`.
- NISQA: `torch`, `pandas`, `tqdm`, NISQA support code and weights.
- DISTILL_MOS: `torch`, `torchaudio`, `xls_r_sqa`, model weights.

Use the helper without `--run` first when you only need metric-name/reference validation; dry-run mode avoids SpeechScore imports and audio reads.

## `pyworld` / `pkg_resources` issue

`pyworld` can import `pkg_resources`. Environments with very new setuptools releases may remove or change that compatibility surface.

Fix:

```bash
python -m pip install 'setuptools<81'
```

Then retry the SpeechScore import or the helper `--run` command.

## Reference audio is missing

Symptoms:

- Index errors inside metric code.
- Errors such as a metric needing reference and test signals.
- Nonsensical results from accidentally scoring a reference-based metric without a clean reference.

Rules:

- `SRMR`, `DNSMOS`, `NISQA`, and `DISTILL_MOS` can run without `reference_path`.
- Every other supported metric requires `reference_path`.
- For mixed metric sets, provide `reference_path` if any selected metric is reference-based.

Run a dry-run validation:

```bash
python scripts/speechscore_metric_recipe.py \
  --metrics SNR,SISDR,DNSMOS \
  --test-path enhanced.wav \
  --reference-path clean.wav
```

## Directory basenames do not match

Directory mode pairs files by basename. If the test directory contains `audio_1.wav`, the reference directory must contain `audio_1.wav` for reference-based metrics.

Fix checklist:

1. Keep scoring directories flat when possible.
2. Use the same extension and basename on both sides.
3. Dry-run before real scoring.
4. Treat extra reference files as ignored; treat missing reference basenames as blocking.

```bash
python scripts/speechscore_metric_recipe.py \
  --metrics SNR,SISDR \
  --test-path test_dir \
  --reference-path reference_dir \
  --return-mean
```

## Model-backed non-intrusive metrics fail

Metrics affected:

- `DNSMOS`
- `NISQA`
- `DISTILL_MOS`

Common causes:

- Missing Python packages such as `onnxruntime`, `torch`, `torchaudio`, or `xls_r_sqa`.
- Model weight files are not present under the expected `scores/` subdirectories.
- The process is run from a directory where relative asset paths do not resolve.
- CPU inference is available but slower than simple metrics.

Fixes:

- Pass `--speechscore-dir <speechscore_component_dir>` to the helper.
- Start with one model-backed metric at a time, for example `--metrics DNSMOS`.
- If no model assets are present, obtain them through the repository's supported setup process before scoring.
- For a lighter reference-free check, use `SRMR`.

## `window` scoring fails in direct API calls

Symptom:

- Direct `scorer(..., window=2.0)` raises a `NameError` related to `maxlen`.

Cause:

- The inspected base scoring branch for windowed scoring references an undefined variable.

Fix:

- Use `window=None` with the direct source API; or
- use the bundled helper with `--window SECONDS --run`, which slices non-overlapping windows and calls metrics through the non-windowed path.

## `score_rate` does not change non-fixed metrics in direct API calls

The direct source scorer accepts `score_rate`, but the inspected base scorer starts from the loaded audio rate and only reliably applies each metric's internal fixed rate. Use the helper's `--score-rate` when explicit pre-resampling is required for non-fixed metrics.

## `return_mean=True` fails on a single file or uneven nested shapes

The source implementation is designed for directory dictionaries. For one file, direct `return_mean=True` can fail because the values are metric scalars rather than per-file dictionaries.

Fixes:

- Use `return_mean=False` for single-file direct API calls.
- Use the helper if you want a safe single-file `Mean_Score` echo.
- For windowed directory scoring, use `--return-mean` only when all files produce compatible nested window keys.

## Results are hard to compare

Before reporting metrics, record:

- Metric names and whether each metric is reference-based.
- Test/reference pairing policy.
- File-level, directory-level, or window-level scoring.
- `score_rate` policy and fixed-rate metrics.
- Whether `Mean_Score` is present and how it was computed.
