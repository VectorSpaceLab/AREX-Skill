# Streaming and chunked processing

SpeechBrain includes streaming helpers for models/features that process fixed chunks or dynamic chunks. Use this reference when adapting streaming ASR, streaming features, or chunked inference.

## Relevant APIs

- `speechbrain.inference.ASR.StreamingASR`
- `speechbrain.utils.dynamic_chunk_training.DynChunkTrainConfig`
- `speechbrain.utils.streaming.split_fixed_chunks`
- `speechbrain.utils.streaming.split_wav_lens`
- `speechbrain.utils.streaming.infer_dependency_matrix`
- `speechbrain.lobes.features.StreamingFeatureWrapper`
- `speechbrain.utils.filter_analysis.FilterProperties`

Verified signature:

```python
speechbrain.lobes.features.StreamingFeatureWrapper(module, properties)
```

## Streaming feature wrapper pattern

A streaming wrapper needs filter properties so it can preserve context and truncate frames correctly:

```python
import torch
from speechbrain.lobes.features import StreamingFeatureWrapper
from speechbrain.utils.filter_analysis import FilterProperties
from speechbrain.utils.streaming import split_fixed_chunks

module = torch.nn.Identity()
props = FilterProperties(window_size=5, stride=2)
wrapper = StreamingFeatureWrapper(module, props)
chunks = split_fixed_chunks(torch.arange(16.0).unsqueeze(0), chunk_size=4)
ctx = wrapper.make_streaming_context()
outs = [wrapper(chunk, ctx) for chunk in chunks]
```

## Streaming ASR notes

`StreamingASR.transcribe_file(path, dynchunktrain_config, use_torchaudio_streaming=True)` expects a dynamic chunk configuration aligned with the model's training assumptions. Do not reuse arbitrary chunk sizes without checking model hparams and latency requirements.

## Validation checklist

- The model was trained or configured for streaming/chunked inference.
- Chunk size, left/right context, and downsampling preserve expected frame alignment.
- Output frames from chunked processing match non-streaming output within acceptable tolerance for a tiny signal.
- VAD or boundary post-processing is evaluated separately from acoustic forward pass.
- Long-form audio tests include memory and latency budgets.

## Troubleshooting

- Shape mismatches often come from confusion between waveform samples and feature frames.
- Boundary artifacts usually mean missing context or wrong filter properties.
- If chunked output has too many/few frames, inspect window size, stride, and truncation behavior.
- If `use_torchaudio_streaming=True` fails, test file loading separately through `audio_io` and try the non-streaming file load path if supported.
