---
name: data-audio-pipelines
description: "Guides SpeechBrain audio I/O, DynamicItemDataset and DataPipeline
  construction, encoders/tokenizers, feature extraction, augmentation,
  beamforming, and preprocessing troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SpeechBrain data and audio pipelines

Use this sub-skill when the task involves audio loading/saving, dataset manifests, dynamic item pipelines, encoders/tokenizers, preprocessing, augmentation, feature extraction, beamforming, or vocal features.

## Route map

| Task | Read/run |
| --- | --- |
| Audio load/save/info, shape debugging, SoundFile backend behavior. | `references/audio-and-features.md`; run `scripts/audio_io_roundtrip.py`. |
| Build `DynamicItemDataset`, `DataPipeline`, `takes`, `provides`, output keys, or data manifests. | `references/data-pipelines.md`; run `scripts/dynamic_pipeline_smoke.py`. |
| Train/use SentencePiece or categorical/text/CTC encoders. | `references/data-pipelines.md`. |
| Use STFT, filterbanks, MFCCs, normalization, streaming features, or tensor shape conventions. | `references/audio-and-features.md`. |
| Use `AddNoise`, `AddReverb`, `SpeedPerturb`, `DropFreq`, `DropChunk`, clipping, beamforming, or vocal feature extraction. | `references/augmentation-and-preprocessing.md`. |
| Diagnose audio/data/preprocessing failures. | `references/troubleshooting.md`. |

## Key conventions

- Audio I/O is through `speechbrain.dataio.audio_io` and uses SoundFile.
- `audio_io.load` returns `(tensor, sample_rate)` and can use `channels_first` / `always_2d` to control shape.
- SpeechBrain model tensors generally use batch first and time second: `(batch, time)` or `(batch, time, channels)`.
- `DynamicItemDataset` plus `DataPipeline` lets recipes compute derived fields lazily from static manifest keys.
- Dynamic item functions declare dependencies with `@takes(...)` and outputs with `@provides(...)`.
- Output keys control which dynamic items are executed; omitted outputs may prevent a dynamic item from running at all.

## Safe smoke checks

```bash
python scripts/audio_io_roundtrip.py --json
python scripts/dynamic_pipeline_smoke.py --json
```

Both scripts use synthetic data only and do not require a SpeechBrain source checkout, dataset, network, or GPU.
