---
name: speechbrain
description: "Guides SpeechBrain package use, pretrained inference, recipes,
  audio pipelines, model components, metrics, and repo maintenance for speech
  and conversational-AI workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SpeechBrain repo skill

Use this skill when a task involves the SpeechBrain Python package, SpeechBrain recipes, pretrained SpeechBrain models, HyperPyYAML experiment files, audio/data pipelines, speech preprocessing, speech metrics, or maintaining the SpeechBrain repository.

SpeechBrain is a PyTorch-based speech and conversational-AI toolkit. It exposes both a library (`speechbrain`) and a large recipe collection. Start here to choose the right focused route, then read only the linked sub-skill/reference needed for the task.

## Quick install and import check

For ordinary package use:

```bash
pip install speechbrain
python - <<'PY'
import speechbrain as sb
print(sb.__version__)
print(sb.Brain)
PY
```

For local recipe development from a source checkout, install the repository and its dependencies in an isolated environment:

```bash
pip install -r requirements.txt
pip install --editable .
python -m pip check
```

Run the bundled environment smoke script when diagnosing setup or optional dependency issues:

```bash
python scripts/check_speechbrain_install.py --json
```

Read `references/installation-and-environment.md` for dependency, Python/Torch, audio backend, Hugging Face, and CPU/GPU notes. Read `references/troubleshooting.md` for cross-cutting install, import, audio, network/cache, and runtime failures.

## Route map

| User task | Read |
| --- | --- |
| Use pretrained models for ASR, speaker verification, classification, enhancement, separation, VAD, TTS, G2P, or local/Hugging Face model loading. | `sub-skills/pretrained-inference/SKILL.md` |
| Run or adapt a recipe, create a new recipe from templates, debug HyperPyYAML overrides, use `Brain`, or launch CPU/GPU/DDP training. | `sub-skills/recipe-training/SKILL.md` |
| Load/save audio, build `DynamicItemDataset`/`DataPipeline`, train tokenizers, create audio features, apply augmentation, beamforming, or vocal-feature preprocessing. | `sub-skills/data-audio-pipelines/SKILL.md` |
| Choose neural blocks, decoders, losses, metric stats, WER scoring, checkpoint recovery, `Pretrainer`, streaming helpers, or component-level tests. | `sub-skills/components-metrics/SKILL.md` |
| Maintain the repository: focused tests, recipe CSV consistency, docs generation, performance tables, lint/pre-commit, or contributor review checks. | `sub-skills/repo-maintenance/SKILL.md` |

## Working model

- SpeechBrain experiments are usually a Python script plus a HyperPyYAML file: `python train.py hparams.yaml --override value`.
- `speechbrain.Brain` owns train/valid/test loops; recipes subclass it and override forward/objective hooks.
- Pretrained inference classes inherit `speechbrain.inference.interfaces.Pretrained` and are commonly loaded with `Class.from_hparams(source=..., savedir=..., run_opts={...})`.
- Audio tensors generally follow batch-time-channel conventions. Mono waveforms are often `(batch, time)`; multi-channel waveforms use an extra channel dimension.
- CPU is enough for imports, small fixtures, and many debug examples. Full recipe training and profiling often need CUDA or another accelerator; do not treat a CPU smoke check as proof of GPU throughput.

## Evidence, provenance, and routing metadata

- Read `references/repo-provenance.md` before checking staleness or refreshing this skill.
- `references/repo-routing-metadata.json` contains structured router metadata for managed repo-skill import tooling.
- This runtime skill is self-contained. It does not require opening the original SpeechBrain checkout; source-relative evidence paths appear only in provenance and review artifacts.
