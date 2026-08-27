# Bundled runtime material map

This sub-skill uses skill-bundled HiFi-GAN runtime files so inference does not
require the original repository checkout.

## Self-contained inference entrypoint

- `scripts/infer_hifigan.py` — public wrapper for wav and mel inference modes.
  It runs copied HiFi-GAN runtime source under `../../scripts/hifigan_runtime/`.
- `scripts/make_dummy_checkpoint.py` — creates a synthetic generator checkpoint
  from bundled source/configs.
- `scripts/run_inference_smoke.py` — exercises both inference modes end to end
  with synthetic inputs.

## Bundled core source/config files

Root runtime directory: `../../scripts/hifigan_runtime/`

- `inference.py` — copied wav-to-wav runtime path.
- `inference_e2e.py` — copied mel-to-wav runtime path.
- `models.py` — `Generator(h)` expects 80 mel channels and emits one waveform
  channel.
- `meldataset.py` — `load_wav`, `MAX_WAV_VALUE`, and `mel_spectrogram` define
  wav normalization and mel math.
- `env.py`, `utils.py` — checkpoint/config helpers shared with training.
- `configs/config_v1.json`, `configs/config_v2.json`, `configs/config_v3.json`
  — bundled V1/V2/V3 generator configs.
- `compat.py` — process-local modern PyTorch/librosa compatibility shims used
  by the wrappers.

## Layout contract

- Checkpoint directories must contain the exact `config.json` that matches the
  generator weights.
- The inference entrypoint reads the paired config from the checkpoint
  directory via the bundled runtime source.
- Output WAVs use the config sample rate and are written as PCM16.

## Verified inspection stack

- `torch 2.3.1+cu121` on an NVIDIA A100-SXM4-40GB host.
- CUDA is available and usable from Python.
- `torch.utils.tensorboard` is importable.
- `librosa.util.normalize` is available from `librosa 0.10.2.post1`.
