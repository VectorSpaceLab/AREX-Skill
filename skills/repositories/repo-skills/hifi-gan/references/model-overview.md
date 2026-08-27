# Model overview

## Purpose

Read this when you need the high-level HiFi-GAN architecture summary, the
bundled generator family differences, or the shared model facts that both the
training and inference routes rely on.

## Core model facts

- Bundled `scripts/hifigan_runtime/models.py` provides `Generator(h)`, the generator used by both training and inference.
- The generator expects 80-channel mel inputs and produces a single waveform
  channel.
- `ResBlock1` and `ResBlock2` are the two residual block families used by the
  bundled configs.
- Training also uses `MultiPeriodDiscriminator` and
  `MultiScaleDiscriminator` plus the helper losses in `models.py`.

## Bundled generator families

| Config | Residual block | Width | Upsample schedule | Notes |
| --- | --- | --- | --- | --- |
| `config_v1.json` | `ResBlock1` | `upsample_initial_channel = 512` | `[8, 8, 2, 2]` | Full-size family from the README. |
| `config_v2.json` | `ResBlock1` | `upsample_initial_channel = 128` | `[8, 8, 2, 2]` | Smaller V1-style family with the same upsample pattern. |
| `config_v3.json` | `ResBlock2` | `upsample_initial_channel = 256` | `[8, 8, 4]` | Compact small-footprint family. |

## Shared architecture constraints

- The bundled configs all use `num_mels = 80`.
- The bundled configs all use `sampling_rate = 22050`.
- The bundled configs all use `hop_size = 256`, which matches the product of
  the V1/V2/V3 upsample rates.
- Changing the mel channel count requires changing the generator's first
  convolution in `models.py`.
- The bundled inference entrypoint expects checkpoint files that contain a
  `generator` state dict.

## Useful cross-checks

- If a checkpoint looks structurally wrong, compare it against the same config
  family in `scripts/hifigan_runtime/configs/config_v1.json`,
  `scripts/hifigan_runtime/configs/config_v2.json`, or
  `scripts/hifigan_runtime/configs/config_v3.json`.
- If a waveform length or mel mismatch shows up during training, verify that
  the config's `hop_size`, `n_fft`, and `win_size` are still aligned.
- If a route needs a deeper explanation of file layouts or troubleshooting,
  open `references/configuration.md` or `references/troubleshooting.md`.
