---
name: pretrained-inference
description: "Guides SpeechBrain pretrained inference interfaces, Hugging Face
  or local model loading, audio normalization, G2P/text inference, profiling,
  and model-cache troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SpeechBrain pretrained inference

Use this sub-skill when the user wants to run or debug SpeechBrain pretrained models, local model folders, Hugging Face sources, direct inference APIs, or model-cache/download behavior.

## First questions to resolve

1. Which task family: ASR, classifier, speaker verification, enhancement, separation, VAD, TTS/vocoder, G2P/text, or custom interface?
2. Is the model source a Hugging Face repo id, local directory, URL, or trusted custom `foreign_class` package?
3. Is network access allowed, and should the model revision/cache be pinned?
4. Is the target backend CPU or CUDA, and is throughput/profiling part of the task?
5. Is the input a file path, already-loaded waveform tensor, batch of waveforms, or text string?

## Common route

1. Read `references/inference-interfaces.md` to choose the class and method.
2. Read `references/workflows.md` for standard loading, audio, batch, local/offline, and custom-model flows.
3. For G2P or text generation workflows, read `references/text-and-g2p.md`.
4. For throughput profiling, read `references/profiling.md` before running any benchmark.
5. For errors, read `references/troubleshooting.md`.
6. Run `scripts/pretrained_interface_smoke.py` when you only need to verify class availability and signatures without downloading models.

## Safe minimal pattern

```python
from speechbrain.inference.ASR import EncoderDecoderASR

asr = EncoderDecoderASR.from_hparams(
    source="speechbrain/asr-conformer-transformerlm-librispeech",
    savedir="pretrained_models/asr-conformer-transformerlm-librispeech",
    run_opts={"device": "cpu"},
)
text = asr.transcribe_file("audio.wav")
```

For a CUDA run, install a CUDA-capable Torch/Torchaudio pair first and set `run_opts={"device": "cuda"}` or an explicit device such as `cuda:0`. Validate CUDA separately; a CPU import check is not a CUDA verification.

## Trust and self-containment notes

- `from_hparams` loads HyperPyYAML and checkpoint files. Treat untrusted hparams as executable configuration.
- `foreign_class` fetches and executes external Python code. Use it only for highly trusted sources.
- Future agents should not depend on original repository examples or tools. Use the bundled references and scripts in this sub-skill.
