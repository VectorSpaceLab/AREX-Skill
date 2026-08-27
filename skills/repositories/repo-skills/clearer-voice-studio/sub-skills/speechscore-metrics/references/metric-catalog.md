# SpeechScore Metric Catalog

Use this catalog to choose metric names and decide whether `reference_path` is required. Metric names are case-insensitive in the bundled helper, but the canonical spellings below match SpeechScore source names.

## Quick selection guide

- Fast reference-based checks for enhancement quality: `SNR,SISDR`, optionally `STOI` and `PESQ` when those dependencies are installed.
- Intelligibility-oriented intrusive scoring: `STOI` plus `PESQ` or `NB_PESQ`.
- Distortion/noise MOS-style intrusive proxies: `CSIG,CBAK,COVL,SSNR,LLR,FWSEGSNR`.
- Separation-style global quality: `BSSEval` and `SISDR`.
- Spectral/cepstral distance: `LSD` and `MCD`.
- Reference-free quality estimates: `SRMR,DNSMOS,NISQA,DISTILL_MOS`.
- Lowest dependency dry-run validation: use the helper without `--run`; dry-run validation does not import metric modules or read audio.

## Reference-free vs reference-based

Reference-free metrics that can run with no clean reference:

| Metric | Output | Notes |
|---|---|---|
| `SRMR` | Scalar SRMR score. | Reverberation/modulation-energy metric; uses 16 kHz scoring and `gammatone`. |
| `DNSMOS` | Nested `BAK`, `OVRL`, `SIG`, `P808_MOS`. | ONNX model-backed MOS predictor; uses 16 kHz scoring and ONNX model files. |
| `NISQA` | Nested `mos_pred`, `noi_pred`, `dis_pred`, `col_pred`, `loud_pred`. | Torch model-backed predictor; uses 48 kHz scoring and bundled NISQA weights. |
| `DISTILL_MOS` | Scalar MOS-like score. | Torch/torchaudio model-backed predictor using `xls_r_sqa` and bundled weights; uses 16 kHz scoring. |

All other SpeechScore metrics require both `test_path` and `reference_path`.

## Full metric table

| Metric | Reference required? | Output shape | Rate behavior | Dependency/runtime notes |
|---|---:|---|---|---|
| `SRMR` | No | Scalar | Fixed 16 kHz | Requires `gammatone` and SRMR helper code. |
| `PESQ` | Yes | Scalar wideband PESQ | Fixed 16 kHz | Requires the `pesq` package; expects reference and test speech. |
| `NB_PESQ` | Yes | Scalar narrowband PESQ | Fixed 16 kHz | Uses `pesq` in narrowband mode. |
| `STOI` | Yes | Scalar 0-1 intelligibility score | Input/common rate unless helper pre-resamples | Requires `pystoi`; reference and test are ordered as clean/reference then degraded/test internally. |
| `SISDR` | Yes | Scalar dB | Input/common rate unless helper pre-resamples | NumPy-based scale-invariant SDR. |
| `FWSEGSNR` | Yes | Scalar dB-like score | Input/common rate unless helper pre-resamples | Uses spectral weighting; requires `librosa`/NumPy stack. |
| `LSD` | Yes | Scalar spectral distance | Input/common rate unless helper pre-resamples | Uses `librosa`; lower is generally closer to the reference. |
| `BSSEval` | Yes | Nested `SDR`, `ISR`, `SAR` | Input/common rate unless helper pre-resamples | Requires `museval`; separation-style metrics. |
| `DNSMOS` | No | Nested `BAK`, `OVRL`, `SIG`, `P808_MOS` | Fixed 16 kHz | Requires `onnxruntime` and model files; can be slower than simple metrics. |
| `SNR` | Yes | Scalar dB | Input/common rate unless helper pre-resamples | Lightweight NumPy metric. |
| `SSNR` | Yes | Scalar segmental dB | Input/common rate unless helper pre-resamples | Lightweight relative metric. |
| `LLR` | Yes | Scalar spectral-model distance | Input/common rate unless helper pre-resamples | Requires SciPy linear-algebra helpers. |
| `CSIG` | Yes | Scalar MOS-like signal distortion score | Fixed 16 kHz | Uses PESQ/WSS/LLR helper formulas; reference required. |
| `CBAK` | Yes | Scalar MOS-like background intrusiveness score | Fixed 16 kHz | Uses PESQ/WSS/SSNR helper formulas; reference required. |
| `COVL` | Yes | Scalar MOS-like overall quality score | Fixed 16 kHz | Uses PESQ/WSS/LLR helper formulas; reference required. |
| `MCD` | Yes | Scalar mel-cepstral distortion | Input/common rate unless helper pre-resamples | Requires `pyworld`, `pysptk`, `fastdtw`, SciPy; lower is closer to reference. |
| `NISQA` | No | Nested `mos_pred`, `noi_pred`, `dis_pred`, `col_pred`, `loud_pred` | Fixed 48 kHz | Requires torch, pandas, NISQA code, and weights. |
| `DISTILL_MOS` | No | Scalar MOS-like score | Fixed 16 kHz | Requires torch, torchaudio, `xls_r_sqa`, and weights. |

## Interpreting directionality

Higher is usually better for `PESQ`, `NB_PESQ`, `STOI`, `SISDR`, `BSSEval` ratios, `SNR`, `SSNR`, `CSIG`, `CBAK`, `COVL`, `SRMR`, `DNSMOS`, `NISQA`, and `DISTILL_MOS`. Lower is usually better for distance/error metrics such as `LSD`, `LLR`, and `MCD`.

Always compare metrics on the same dataset, path pairing, sample-rate policy, and metric set. Do not mix single-file scores with directory means without labeling them clearly.

## Import side effects to remember

Although only four metrics are reference-free, importing the SpeechScore factory loads all metric modules in the inspected source layout. If any dependency such as `resampy`, `pesq`, `pystoi`, `pyworld`, `pysptk`, `onnxruntime`, `gammatone`, or `xls_r_sqa` is missing, even a simple metric subset may fail at import time. Use the helper's default dry-run to validate names/reference behavior without triggering those imports.
