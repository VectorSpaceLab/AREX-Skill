# SpeechScore API Reference

SpeechScore is a source-layout objective metric wrapper. In the inspected snapshot, the usable factory is the `SpeechScore` function in `speechscore.py`.

## Import contract

```python
from speechscore import SpeechScore

scorer = SpeechScore(["SNR", "SISDR"])
print(scorer)  # Scores: SNR SISDR
```

Important import rules:

- Put the SpeechScore component directory itself on `sys.path`, or run from that directory. Adding only the parent project directory can import the `speechscore` package `__init__` instead of `speechscore.py`, and that package does not expose the `SpeechScore` factory.
- The wrapper imports all metric modules at `speechscore.py` import time. A light metric subset such as `SNR,SISDR` can still fail to import if optional dependencies for other metrics are missing.
- Model-backed metrics use relative asset paths under `scores/`. When using the bundled helper from another working directory, pass `--speechscore-dir <speechscore_component_dir>` so imports and assets resolve consistently.
- Pass metric names as an explicit list. `SpeechScore("")` constructs successfully but produces an empty `ScoresList` in this snapshot.

## Factory and callable

```python
from speechscore import SpeechScore

scorer = SpeechScore(["PESQ", "STOI", "SISDR"])
results = scorer(
    test_path="enhanced.wav",
    reference_path="clean.wav",
    window=None,
    score_rate=16000,
    return_mean=False,
)
```

`SpeechScore(metric_names)` returns a `ScoresList` object. The callable signature is:

```python
ScoresList.__call__(test_path, reference_path, window=None, score_rate=None, return_mean=False)
```

| Parameter | Meaning | Practical rule |
|---|---|---|
| `test_path` | Test/degraded/enhanced audio file or directory. | Required for every run. Directory mode discovers `.wav` files first, then `.flac` files. |
| `reference_path` | Clean/reference audio file or directory. | Required if any selected metric is reference-based; omit for reference-free-only metric sets. |
| `window` | Window length in seconds, or `None` for whole-file scoring. | Direct source windowing can fail; use the bundled helper for windowed scoring. |
| `score_rate` | Requested scoring sample rate. | Fixed-rate metrics override it; the inspected direct source path does not reliably honor it for non-fixed metrics. Use the helper when explicit resampling matters. |
| `return_mean` | Add a recursive `Mean_Score` over directory results. | Best for matched directory scoring; the helper also handles the single-file corner case. |

## Reference requirement rules

Use the metric catalog as the source of truth. The source class attribute named `intrusive` is inconsistent: several reference-required metrics set it to `False`, while some reference-free metrics set it to `True`.

Reference-free metrics that can run with `reference_path=None` are:

- `SRMR`
- `DNSMOS`
- `NISQA`
- `DISTILL_MOS`

All other supported SpeechScore metrics require a clean reference audio path.

## File and directory behavior

Single-file scoring returns a dictionary keyed by metric name:

```python
{
    "SNR": 4.57,
    "SISDR": 4.78,
    "DNSMOS": {"BAK": 1.90, "OVRL": 1.86, "SIG": 2.68, "P808_MOS": 2.58},
}
```

Directory scoring returns a dictionary keyed by test basename. For reference-based metrics, the reference directory must contain the same basenames as the test directory:

```python
{
    "audio_1.wav": {"SNR": -0.95, "SISDR": -0.24},
    "audio_2.wav": {"SNR": 10.09, "SISDR": 9.79},
    "Mean_Score": {"SNR": 4.57, "SISDR": 4.78},
}
```

Only matching basenames are paired. Keep flat directories with exact filename parity for reproducible `return_mean=True` results.

## Result dictionary shapes

Most metrics return one scalar per file. These metrics return nested dictionaries:

- `BSSEval`: `{"SDR": value, "ISR": value, "SAR": value}`.
- `DNSMOS`: `{"BAK": value, "OVRL": value, "SIG": value, "P808_MOS": value}`.
- `NISQA`: `{"mos_pred": value, "noi_pred": value, "dis_pred": value, "col_pred": value, "loud_pred": value}`.

When `return_mean=True`, nested dictionaries are averaged key-by-key. Examples:

```python
results["Mean_Score"]["SNR"]
results["Mean_Score"]["DNSMOS"]["OVRL"]
results["audio_1.wav"]["NISQA"]["mos_pred"]
```

## `score_rate` and fixed-rate behavior

The inspected base scorer always starts from the loaded audio's rate, then applies a metric's internal fixed rate when one is set. The direct source `score_rate` argument is therefore not a reliable way to resample non-fixed metrics. The bundled helper pre-resamples audio when `--score-rate` is supplied, then lets fixed-rate metrics override as needed.

Observed fixed-rate settings:

- 16 kHz: `PESQ`, `NB_PESQ`, `CSIG`, `CBAK`, `COVL`, `SRMR`, `DNSMOS`, `DISTILL_MOS`.
- 48 kHz: `NISQA`.
- Input/common rate unless the helper pre-resamples: `BSSEval`, `STOI`, `SISDR`, `FWSEGSNR`, `LSD`, `SNR`, `SSNR`, `LLR`, `MCD`.

The loader keeps only the first audio channel and zero-pads test/reference arrays to the same length after rate alignment.

## Window behavior

The direct source `ScoreBasis.scoring(window=...)` branch references an undefined `maxlen` variable and can raise `NameError`. Use either:

- `window=None` when calling the source API directly; or
- `scripts/speechscore_metric_recipe.py --window SECONDS --run` when windowed scoring is needed.

The helper slices non-overlapping windows, pads the final short window, calls each metric on each window through the non-windowed source scorer, and nests results by window index.
