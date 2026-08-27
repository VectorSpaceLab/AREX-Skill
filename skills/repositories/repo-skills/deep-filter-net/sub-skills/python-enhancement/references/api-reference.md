# Python API reference

This reference is distilled from the package source plus live package inspection. It is self-contained for runtime use; do not rely on the original repository checkout being present.

## Import and version checks

Use `importlib.import_module("df.enhance")` when you need module constants. The package top-level `df.enhance` name is also exported as the `enhance` function, so `import df.enhance as x` can bind to the function instead of the module in some Python sessions.

```bash
python - <<'PY'
import importlib, inspect
import torch, torchaudio, libdf
import df
m = importlib.import_module("df.enhance")
print("df version:", getattr(df, "__version__", "unknown"))
print("torch:", torch.__version__, "cuda available:", torch.cuda.is_available())
print("torchaudio:", torchaudio.__version__)
print("pretrained:", m.PRETRAINED_MODELS)
print("default:", m.DEFAULT_MODEL)
print("init_df:", inspect.signature(m.init_df))
print("enhance:", inspect.signature(m.enhance))
PY
```

Expected key facts from the verified package environment:

- Python package distribution: `DeepFilterNet` 0.5.7 release-candidate style metadata.
- `DeepFilterLib`/`libdf` wheel: 0.5.6.
- Required imports for this sub-skill: `torch`, `torchaudio`, `df`, `libdf`.
- CLI entry points: `deepFilter`, `deep-filter-py`.
- Pretrained model names: `DeepFilterNet`, `DeepFilterNet2`, `DeepFilterNet3`.
- Source and installed constants set `DEFAULT_MODEL = "DeepFilterNet3"`. Some older help/doc text still says DeepFilterNet2; prefer the live constants.

## Model and configuration API

### `df.enhance.init_df`

Verified signature:

```python
init_df(
    model_base_dir: Optional[str] = None,
    post_filter: bool = False,
    log_level: str = "INFO",
    log_file: Optional[str] = "enhance.log",
    config_allow_defaults: bool = True,
    epoch: Union[str, int, None] = "best",
    default_model: str = "DeepFilterNet3",
    mask_only: bool = False,
) -> tuple[torch.nn.Module, libdf.DF, str, int]
```

Behavior and contracts:

- `model_base_dir=None` uses `default_model`, currently `DeepFilterNet3`.
- `model_base_dir` may be one of `DeepFilterNet`, `DeepFilterNet2`, `DeepFilterNet3`, or a local model directory.
- Passing `None` or a pretrained model name resolves through the DeepFilterNet user cache and may download a missing model archive. For offline execution, pass a local directory or verify the model is already cached before calling.
- A local model directory must contain `config.ini` and a `checkpoints/` directory with the requested checkpoint epoch. If missing, expect `NotADirectoryError`, `ValueError` for missing config, or an early exit/log message about not finding a checkpoint.
- `post_filter=True` sets the package `mask_pf` config and appends `_pf` to the returned suffix.
- `epoch` accepts `"best"`, `"latest"`, an integer epoch, or `None`/`"none"` to skip checkpoint loading.
- `log_file="enhance.log"` writes under the model directory; pass `log_file=None` in scripts that should avoid mutating model directories.
- The returned `model` is moved to the package-selected device. Device selection uses config option/environment variable `DEVICE`; when unset, it selects `cuda:0` if `torch.cuda.is_available()` else CPU.

Return values:

| Value | Meaning |
|---|---|
| `model` | Initialized DeepFilterNet PyTorch module in eval/inference-ready form after checkpoint load. |
| `df_state` | `libdf.DF` state configured from the model `config.ini` for STFT/ISTFT/ERB. |
| `suffix` | Basename of the model directory, with `_pf` appended when post-filtering is enabled. Use for output filenames if desired. |
| `epoch` | Loaded checkpoint epoch number. |

### `df.config.DfParams`

`DfParams()` reads the active package config and supplies defaults if allowed. Verified defaults when no model config overrides them:

| Field | Default | Meaning |
|---|---:|---|
| `sr` | `48000` | Training/model sampling rate in Hz. |
| `fft_size` | `960` | STFT FFT/window size in samples. |
| `hop_size` | `480` | STFT hop size/frame step. |
| `nb_erb` | `32` | Number of ERB bands. |
| `nb_df` | `96` | Number of low-frequency bins used by deep filtering. |
| `norm_tau` | `1` | Normalization time constant. |
| `lsnr_max` | `35` | Local SNR target upper clamp. |
| `lsnr_min` | `-15` | Local SNR target lower clamp. |
| `min_nb_freqs` | `2` | Minimum FFT bins per ERB band in the default DeepFilterNet setup. |
| `df_order` | `5` | Deep filtering order. |
| `df_lookahead` | `0` | Deep filtering lookahead. |
| `pad_mode` | `"input"` | Where lookahead padding is applied. |

Use the model's loaded config, not these defaults, for production enhancement decisions.

## Enhancement API

### `df.enhance.enhance`

Verified signature:

```python
enhance(
    model: torch.nn.Module,
    df_state: libdf.DF,
    audio: torch.Tensor,
    pad=True,
    atten_lim_db: Optional[float] = None,
) -> torch.Tensor
```

Input/output contracts:

- `audio` must be a time-domain tensor shaped `[channels, samples]`. Use `df.io.load_audio` because it returns this shape. If you have a 1-D tensor, add a channel dimension first.
- Audio sampling rate must match `df_state.sr()` and the loaded model config. For bundled pretrained models, plan for 48 kHz model audio.
- The function treats channels as a batch dimension and resets model recurrent state when the model exposes `reset_h0`.
- `pad=True` compensates the algorithmic STFT/model delay by padding the input and slicing the output back to the original length. The output shape matches `[channels, original_samples]`.
- `pad=False` disables delay compensation; output can be slightly shorter and delayed.
- `atten_lim_db=None` leaves the model output unchanged. A positive value such as `12` mixes enhanced and noisy spectra so suppression is limited to about 12 dB.
- Returns enhanced CPU tensor shaped `[channels, samples]` after ISTFT.

Minimal API recipe:

```python
import importlib
from df.io import load_audio, save_audio, resample

enhance_mod = importlib.import_module("df.enhance")
model, df_state, suffix, epoch = enhance_mod.init_df(
    model_base_dir="models/DeepFilterNet3-local",
    post_filter=False,
    log_file=None,
)
audio, meta = load_audio("noisy.wav", sr=df_state.sr())
enhanced = enhance_mod.enhance(model, df_state, audio, pad=True, atten_lim_db=None)
if meta.sample_rate != df_state.sr():
    enhanced = resample(enhanced, df_state.sr(), meta.sample_rate)
save_audio("enhanced.wav", enhanced, sr=meta.sample_rate)
```

### `df.enhance.df_features`

Verified signature:

```python
df_features(audio: torch.Tensor, df: libdf.DF, nb_df: int, device=None) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]
```

Contract:

- Input `audio`: tensor `[channels, samples]` on CPU; implementation calls `audio.numpy()`.
- `df`: `libdf.DF` state.
- `nb_df`: number of spectrum bins used for the DF feature branch; commonly model attribute `nb_df` or config default `96`.
- Returns `(spec, erb_feat, spec_feat)`:
  - `spec`: real-view complex STFT shaped approximately `[channels, 1, frames, fft_bins, 2]`.
  - `erb_feat`: normalized ERB features shaped approximately `[channels, 1, frames, nb_erb]`.
  - `spec_feat`: normalized low-bin complex features shaped approximately `[channels, 1, frames, nb_df, 2]`.
- If `device` is not `None`, outputs are moved to that device.

## Audio I/O API

### `df.io.load_audio`

Verified signature:

```python
load_audio(file: str, sr: Optional[int] = None, verbose=True, **kwargs) -> tuple[torch.Tensor, torchaudio.AudioMetaData]
```

Contracts:

- Uses `torchaudio.info()` and `torchaudio.load()`.
- Returns audio tensor `[channels, samples]`, contiguous, plus metadata for the original file.
- If `sr` is set and the input sample rate differs, resamples to `sr` and returns metadata with the original sample rate.
- Extra `torchaudio.load()` kwargs are accepted. `format` is passed to the info call; `method` is passed to `df.io.resample`.
- Supported resample methods are `sinc_fast`, `sinc_best`, `kaiser_fast`, and `kaiser_best`.

### `df.io.resample`

Verified signature:

```python
resample(audio: torch.Tensor, orig_sr: int, new_sr: int, method="sinc_fast") -> torch.Tensor
```

Use this to move enhanced audio from model sample rate back to the original input rate when mirroring the CLI behavior.

### `df.io.save_audio`

Verified signature:

```python
save_audio(
    file: str,
    audio: Union[torch.Tensor, numpy.ndarray],
    sr: int,
    output_dir: Optional[str] = None,
    suffix: Optional[str] = None,
    log: bool = False,
    dtype=torch.int16,
)
```

Contracts:

- If `suffix` is set, output filename becomes `<stem>_<suffix><ext>`.
- If `output_dir` is set, the output basename is written under that directory.
- 1-D audio is promoted to `[1, samples]`.
- Default `dtype=torch.int16` scales floating audio by `2**15` and writes int16 through `torchaudio.save`.
- Use `dtype=torch.float32` if you need a floating-point output file and the selected torchaudio backend supports it.

## `libdf` STFT/ISTFT/ERB API

### `libdf.DF`

Stubbed public constructor:

```python
DF(sr: int, fft_size: int, hop_size: int, nb_bands: int, min_nb_erb_freqs: Optional[int] = 1)
```

Important methods:

| Method | Contract |
|---|---|
| `analysis(input)` | Input real NumPy array `[channels, samples]`; output complex STFT array `[channels, frames, fft_bins]`. Verified wheel behavior uses one-sided FFT bins, `fft_bins = fft_size // 2 + 1`. |
| `synthesis(input)` | Input complex array `[channels, frames, fft_bins]`; output real array `[channels, samples]` for the available frames. |
| `erb_widths()` | ERB filterbank widths for `nb_bands`. |
| `fft_window()` | FFT analysis/synthesis window, length `fft_size`. |
| `sr()`, `fft_size()`, `hop_size()`, `nb_erb()` | Runtime parameters. |
| `reset()` | Reset streaming/STFT buffers. |

A verified smoke with `DF(sr=16000, fft_size=320, hop_size=160, nb_bands=32)` and a 0.1 s mono signal produced:

- STFT shape `(1, 10, 161)`.
- Synthesis shape `(1, 1600)`.
- ERB shape `(1, 10, 32)`.

### ERB and normalization functions

```python
erb(input: numpy.ndarray, erb_fb: Union[numpy.ndarray, list[int]], db: bool = True) -> numpy.ndarray
erb_inv(input: numpy.ndarray, erb_fb: Union[numpy.ndarray, list[int]]) -> numpy.ndarray
erb_norm(erb: numpy.ndarray, alpha: float, state: Optional[numpy.ndarray] = None) -> numpy.ndarray
unit_norm(spec: numpy.ndarray, alpha: float, state: Optional[numpy.ndarray] = None) -> numpy.ndarray
unit_norm_init(num_freq_bins: int) -> numpy.ndarray
```

Notes:

- `erb` accepts the `DF.analysis()` spectrum shape used by DeepFilterNet, `[channels, frames, fft_bins]`, and maps the frequency axis to `nb_erb` bands.
- `erb_norm` and `unit_norm` return arrays with the same shape as their data input and can accept an optional normalization state for streaming-style reuse.
- Use [../scripts/libdf_smoke.py](../scripts/libdf_smoke.py) to verify these calls in the active environment before building a larger enhancement script.
