# SpeechScore Workflows

These workflows use the bundled helper so paths are explicit and no sample audio locations are assumed. Replace placeholders such as `enhanced.wav`, `clean.wav`, and `<speechscore_component_dir>` with task-specific paths.

## 1. Choose the metric set

1. If clean reference audio is available, start with a small intrusive set such as `SNR,SISDR` for fast sanity checks.
2. Add `STOI` for intelligibility and `PESQ`/`NB_PESQ` for perceptual quality when their dependencies are installed.
3. Add `CSIG,CBAK,COVL,SSNR,LLR,FWSEGSNR` for speech-enhancement benchmark-style reports.
4. Add `LSD` or `MCD` when spectral/cepstral distance is relevant.
5. If no clean reference exists, use only `SRMR,DNSMOS,NISQA,DISTILL_MOS`. Expect the model-backed metrics to need more dependencies, model files, and runtime.

## 2. Dry-run validation before audio I/O

Dry-run mode is the default. It validates metric names and reference requirements without importing SpeechScore or reading audio.

```bash
python scripts/speechscore_metric_recipe.py \
  --metrics SNR,SISDR \
  --test-path enhanced.wav \
  --reference-path clean.wav
```

For reference-free metrics:

```bash
python scripts/speechscore_metric_recipe.py \
  --metrics SRMR,DNSMOS,NISQA,DISTILL_MOS \
  --test-path enhanced.wav
```

If dry-run sees existing test/reference directories, it also checks that every discovered test basename exists in the reference directory.

## 3. Score one file against one reference

```bash
python scripts/speechscore_metric_recipe.py \
  --run \
  --speechscore-dir <speechscore_component_dir> \
  --metrics SNR,SISDR,STOI,PESQ \
  --test-path enhanced.wav \
  --reference-path clean.wav \
  --score-rate 16000
```

Expected result shape:

```python
{
    "SNR": 4.57,
    "SISDR": 4.78,
    "STOI": 0.86,
    "PESQ": 1.14,
}
```

Use `--speechscore-dir` when running from outside the SpeechScore component directory. The helper inserts that directory into `sys.path` and uses it as the asset working directory for model-backed metrics.

## 4. Score matched directories and request means

Directory mode pairs files by basename. Keep the test and reference directories flat and name-matched:

```text
test_dir/
  audio_1.wav
  audio_2.wav
reference_dir/
  audio_1.wav
  audio_2.wav
```

Dry-run first:

```bash
python scripts/speechscore_metric_recipe.py \
  --metrics SNR,SISDR \
  --test-path test_dir \
  --reference-path reference_dir \
  --return-mean
```

Then run:

```bash
python scripts/speechscore_metric_recipe.py \
  --run \
  --speechscore-dir <speechscore_component_dir> \
  --metrics SNR,SISDR \
  --test-path test_dir \
  --reference-path reference_dir \
  --return-mean
```

Expected result shape:

```python
{
    "audio_1.wav": {"SNR": -0.95, "SISDR": -0.24},
    "audio_2.wav": {"SNR": 10.09, "SISDR": 9.79},
    "Mean_Score": {"SNR": 4.57, "SISDR": 4.78},
}
```

If a test basename is missing from the reference directory, stop and fix the pairing before trusting any mean.

## 5. Score without reference audio

Use only reference-free metrics:

```bash
python scripts/speechscore_metric_recipe.py \
  --run \
  --speechscore-dir <speechscore_component_dir> \
  --metrics DNSMOS,NISQA,DISTILL_MOS \
  --test-path enhanced.wav
```

Expected nested values:

```python
{
    "DNSMOS": {"BAK": 1.90, "OVRL": 1.86, "SIG": 2.68, "P808_MOS": 2.58},
    "NISQA": {"mos_pred": 2.04, "noi_pred": 1.63, "dis_pred": 4.02, "col_pred": 3.11, "loud_pred": 2.70},
    "DISTILL_MOS": 2.95,
}
```

If this fails before scoring, check model-backed metric dependencies and asset files. For a lighter reference-free probe, try `SRMR` first.

## 6. Windowed scoring

Direct source `window` support can fail in this snapshot. Use the helper for non-overlapping windows:

```bash
python scripts/speechscore_metric_recipe.py \
  --run \
  --speechscore-dir <speechscore_component_dir> \
  --metrics SNR,SISDR \
  --test-path enhanced.wav \
  --reference-path clean.wav \
  --window 2.0
```

Windowed output nests each metric by window index:

```python
{
    "SNR": {0: 3.2, 1: 4.1, 2: 5.0},
    "SISDR": {0: 2.9, 1: 4.3, 2: 5.2},
}
```

Use `--return-mean` with windowed directory scoring only when every file has compatible window counts and result shapes.

## 7. Interpret nested directory means

When `return_mean=True`, access nested scores explicitly:

```python
mean_snr = results["Mean_Score"]["SNR"]
mean_dnsmos_ovrl = results["Mean_Score"]["DNSMOS"]["OVRL"]
first_file_nisqa_mos = results["audio_1.wav"]["NISQA"]["mos_pred"]
```

Report the metric set, reference policy, sample-rate policy, and whether the score is per-file, per-window, or a directory mean.

## 8. Minimal direct API recipe

Use the source API directly only when imports already work and `window=None` is acceptable:

```python
import pprint
from speechscore import SpeechScore

scorer = SpeechScore(["SNR", "SISDR"])
scores = scorer(
    test_path="enhanced.wav",
    reference_path="clean.wav",
    window=None,
    score_rate=16000,
    return_mean=False,
)
pprint.pprint(scores)
```

For source-layout runs, ensure the component directory containing `speechscore.py` is importable before executing this snippet.
