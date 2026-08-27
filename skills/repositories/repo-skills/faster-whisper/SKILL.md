---
name: faster-whisper
description: "Use the faster-whisper package for CTranslate2-backed Whisper
  transcription, model selection, CPU/CUDA setup, audio utilities, VAD,
  timestamps, and conversion guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# faster-whisper Repo Skill

Use this skill when a task involves `faster-whisper`, CTranslate2 Whisper ASR,
speech-to-text transcription, batched audio inference, word timestamps, VAD,
Whisper model aliases, local CTranslate2 model directories, or CPU/CUDA runtime
troubleshooting for this package.

`faster-whisper` is a Python reimplementation of OpenAI Whisper inference using
CTranslate2. It exposes a small Python API centered on `WhisperModel` and
`BatchedInferencePipeline` rather than a package-owned command-line interface.

## Start here

1. Install the package in the target runtime:

   ```bash
   pip install faster-whisper
   ```

   For a source checkout, use editable install only when developing that
   checkout:

   ```bash
   pip install -e .
   ```

2. Run the minimal import check:

   ```bash
   python - <<'PY'
   import faster_whisper
   from faster_whisper import WhisperModel, available_models
   print(faster_whisper.__version__)
   print(available_models()[:5])
   PY
   ```

3. For environment diagnostics, run the bundled helper:

   ```bash
   python scripts/check_install.py
   ```

4. Route detailed transcription work to
   [sub-skills/transcription/SKILL.md](sub-skills/transcription/SKILL.md).

## Route map

- Read [references/installation-and-backends.md](references/installation-and-backends.md)
  when setting up Python, understanding runtime dependencies, choosing CPU vs
  CUDA, or diagnosing CTranslate2/cuDNN/library issues.
- Read [references/model-management.md](references/model-management.md) when the
  task involves model aliases, Hugging Face downloads, offline caches, local
  converted CTranslate2 model directories, Distil-Whisper, or converting a
  Transformers/OpenAI Whisper checkpoint.
- Read [references/troubleshooting.md](references/troubleshooting.md) for
  cross-cutting install, import, model-download, backend, and deployment issues;
  transcription-specific failures are routed onward to the transcription
  sub-skill troubleshooting reference.
- Read [references/repo-provenance.md](references/repo-provenance.md) before
  deciding whether this skill is stale for a current checkout.
- `references/repo-routing-metadata.json` is structured metadata used by the
  managed repo-skills router importer; it is not a human workflow guide.
- Run [scripts/check_install.py](scripts/check_install.py) to inspect import,
  version, model aliases, CTranslate2 compute types, and VAD dependency health
  in the active environment.

## Sub-skills

| Sub-skill | Use when | Main outputs |
| --- | --- | --- |
| [transcription](sub-skills/transcription/SKILL.md) | The task asks for ASR/transcription, batched inference, language detection, translation, word timestamps, VAD, hotwords, clip timestamps, stereo decoding, or segment output handling. | API recipes, transcription workflows, troubleshooting, and a configurable transcription helper. |

## Common task routing

- "Transcribe this audio file with faster-whisper" → use the transcription
  sub-skill standard or bundled-helper workflow.
- "Make it faster on GPU" → read installation/backend guidance, then use the
  transcription sub-skill with `device="cuda"` and an appropriate `compute_type`.
- "Use a local or fine-tuned Whisper model" → read model-management first, then
  instantiate `WhisperModel` with the local CTranslate2 model directory.
- "Why is no transcription happening?" → read transcription troubleshooting;
  the segment iterable must be consumed.
- "I need word timestamps or VAD" → use the transcription sub-skill references.
- "Compare WER or benchmark memory" → this skill can explain package options,
  but heavy benchmark scripts are intentionally out of runtime scope because
  they require large models, datasets, GPU telemetry, and controlled hosts.

## Public API anchor

```python
from faster_whisper import WhisperModel, BatchedInferencePipeline

model = WhisperModel("tiny", device="cpu", compute_type="int8")
segments, info = model.transcribe("audio.mp3", language="en")
for segment in segments:  # transcription starts when iterated
    print(segment.start, segment.end, segment.text)
```

Use the transcription sub-skill for option details before writing production
code, especially around generator consumption, batched defaults, VAD, timestamps,
and CUDA/CPU compute types.

## Boundaries

This is a user-facing operating skill, not a maintainer checklist. It does not
cover release publishing, linting policy, or exhaustive benchmark reproduction.
It also does not replace CTranslate2, Hugging Face Hub, PyAV, or ONNX Runtime
documentation; it records how `faster-whisper` uses those dependencies for the
package workflows above.
