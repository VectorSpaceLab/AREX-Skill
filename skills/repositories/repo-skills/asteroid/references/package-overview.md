# Asteroid package overview

## Main public modules

- `asteroid.models`: ready-to-use source-separation model families, sharing helpers, and registry helpers
- `asteroid.data`: dataset loaders for speech, music, multichannel, VAD, and audio-visual corpora
- `asteroid.losses`: PIT, MixIT, SinkPIT, SDR/MSE/PMSQE/STOI, and clustering losses
- `asteroid.metrics`: metric computation and tracking helpers
- `asteroid.engine`: Lightning `System`, optimizers, and schedulers
- `asteroid.dsp`: overlap-add, beamforming, consistency, VAD, spatial helpers, and deltas
- `asteroid.masknn`: mask-network building blocks, activations, norms, recurrent layers, and attention
- `asteroid.complex_nn`: complex-tensor helpers and complex-valued blocks
- `asteroid.utils`: parser, tensor, tracing, generic, and hub utilities
- `asteroid.scripts`: installed CLI entry points for pretrained inference, model sharing, and version reporting
- bundled runtime helpers: `scripts/install_runtime.py`, `scripts/runtime_requirements.txt`, `scripts/smoke_training.py`, and `scripts/inspect_versions.py`

## Top-level entry points worth remembering

- `asteroid-infer`
- `asteroid-upload`
- `asteroid-register-sr`
- `asteroid-versions`

## Good first routes

- **Pretrained model usage**: `models`, `scripts`, `dsp`
- **Recipe training**: `data`, `losses`, `metrics`, `engine`
- **Custom architecture work**: `masknn`, `complex_nn`, `dsp`, `utils`, `models`
- **Model publishing**: `models.publisher`, `scripts`, and the sharing sub-skill
- **Runtime bootstrap / smoke checks**: `scripts/install_runtime.py`, `scripts/runtime_requirements.txt`, `scripts/smoke_training.py`, and `scripts/inspect_versions.py`
