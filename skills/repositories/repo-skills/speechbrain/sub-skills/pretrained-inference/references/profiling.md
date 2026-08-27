# Inference profiling guidance

SpeechBrain's source repository includes profiling material for pretrained inference. The profiling workflow is useful, but it can download large models, run many synthetic durations/batch sizes, and use GPU memory. Treat profiling as an explicit performance task, not a default smoke check.

## What to decide before profiling

- Model source and interface class, e.g. `EncoderASR` or `EncoderDecoderASR`.
- Device: CPU or CUDA. Validate the backend first.
- Input source: synthetic noise or a representative audio file.
- Duration grid and batch sizes.
- Whether trace logs should be exported.
- Acceptable runtime and memory budget.

## Lightweight dry-run pattern

Before full profiling, verify that the class and source can load and that a single forward method works on a tiny input:

```python
import torch
from speechbrain.inference.ASR import EncoderASR

model = EncoderASR.from_hparams(source="model-source", savedir="pretrained_models/model-source")
wavs = torch.zeros(1, 16000, device=model.device)
wav_lens = torch.ones(1, device=model.device)
model.transcribe_batch(wavs, wav_lens)
```

If the model uses a beam search or language model, synthetic silence/noise may not be representative for accuracy, but it is still useful for catching shape/device failures.

## Profiling result interpretation

- Real-time factor below `1.0` means faster than real time for that setting.
- Large batch sizes and long durations can be VRAM intensive even if one-file inference works.
- CPU time and CUDA time may both matter because audio loading, decoding, and post-processing can remain CPU-bound.
- The first few batches may include warmup and should not be treated as steady-state throughput.

## Skip reasons to record

Use explicit skip notes for:

- No network access for model download.
- No verified CUDA backend for a CUDA profile.
- Model source requires untrusted custom Python.
- Input audio is private or too large.
- Profiling grid exceeds time/memory budget.
