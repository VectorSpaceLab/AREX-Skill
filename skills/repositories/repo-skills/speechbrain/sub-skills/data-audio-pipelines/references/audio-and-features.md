# Audio I/O and feature extraction

## Audio I/O signatures

```python
from speechbrain.dataio import audio_io

audio_io.load(path, *, channels_first=True, dtype=None, always_2d=True, frame_offset=0, num_frames=-1)
audio_io.save(path, src, sample_rate, channels_first=True, subtype=None)
audio_io.info(path)
```

`audio_io.load` returns `(tensor, sample_rate)`. With default `channels_first=True` and `always_2d=True`, a mono WAV usually returns shape `(1, frames)`. Use `channels_first=False` for `(frames, channels)`.

## Shape conventions

SpeechBrain model inputs are batch-first:

- Mono waveform batch: `(batch, time)`.
- Multi-channel waveform batch: `(batch, time, channels)`.
- STFT-like features may be `(batch, time, frequency, complex)` or include extra channel dimensions.
- Relative length tensors are shape `(batch,)`, with the longest item `1.0`.

Convert single-file audio to a batch with `waveform.unsqueeze(0)` only after checking whether the file load already has a channel dimension.

## Feature signatures

```python
speechbrain.processing.features.STFT(sample_rate, win_length=25, hop_length=10, n_fft=400, ...)
speechbrain.processing.features.spectral_magnitude(stft, power=1, log=False, eps=1e-14)
speechbrain.processing.features.Filterbank(n_mels=40, log_mel=True, f_min=0, f_max=8000, n_fft=400, sample_rate=16000, ...)
speechbrain.processing.features.DCT(input_size, n_out=20, ortho_norm=True)
speechbrain.processing.features.InputNormalization(mean_norm=True, std_norm=True, norm_type="global", ...)
speechbrain.lobes.features.Fbank(deltas=False, context=False, sample_rate=16000, n_mels=40, ...)
speechbrain.lobes.features.MFCC(deltas=True, context=True, sample_rate=16000, n_mfcc=20, ...)
```

## Minimal audio roundtrip

```python
import torch
from speechbrain.dataio import audio_io

wave = torch.zeros(1, 16000)
audio_io.save("probe.wav", wave, 16000)
loaded, sr = audio_io.load("probe.wav")
info = audio_io.info("probe.wav")
assert sr == 16000
assert loaded.shape == (1, 16000)
print(info.duration, info.channels)
```

Run the bundled `scripts/audio_io_roundtrip.py` for a self-contained version.

## Feature extraction pattern

```python
import torch
from speechbrain.lobes.features import Fbank
from speechbrain.processing.features import InputNormalization

wavs = torch.zeros(2, 16000)       # batch, time
lengths = torch.ones(2)
fbank = Fbank(sample_rate=16000, n_mels=40)
norm = InputNormalization(norm_type="sentence")
features = fbank(wavs)
features = norm(features, lengths)
```

## Common mistakes

- Passing `(channels, time)` where a model expects `(batch, time)`.
- Forgetting to resample audio to the model's expected sample rate.
- Assuming every loader returns a 1D mono waveform; SpeechBrain audio I/O defaults to 2D.
- Normalizing padded frames because `lengths` are missing or wrong.
- Mixing raw `torchaudio.load` conventions with SpeechBrain's `audio_io` wrapper without checking shape.
