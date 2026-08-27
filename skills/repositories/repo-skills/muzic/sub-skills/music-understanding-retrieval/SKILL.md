---
name: music-understanding-retrieval
description: "MusicBERT symbolic understanding, PDAugment lyrics-transcription
  augmentation, and CLaMP cross-modal symbolic MIR."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Music Understanding and Retrieval

Use this sub-skill when the task is about Muzic workflows for symbolic music understanding, lyrics-transcription augmentation, or cross-modal symbolic music retrieval.

## Route by requested capability

| Request | Load next | Notes |
|---|---|---|
| Preprocess MIDI into OctupleMIDI, binarize data, pretrain MusicBERT, fine-tune/evaluate melody completion, accompaniment suggestion, genre, or style classifiers | [references/musicbert-workflows.md](references/musicbert-workflows.md) | Data-prep can be CPU-bound; Fairseq train/eval normally needs the old MusicBERT stack, checkpoints, and CUDA. |
| Prepare speech/MIDI data for PDAugment, validate the final `pdaugment.py` positional arguments, or troubleshoot pitch/duration augmentation for lyrics transcription | [references/pdaugment-workflows.md](references/pdaugment-workflows.md) | Treat the original augmentation run as corpus-scale and externally dependent on audio tools, phonemization, MFA alignment, and MIDI preprocessing. |
| Run or prepare CLaMP text/music semantic search, zero-shot classification, similar-music retrieval, or input layout validation | [references/clamp-workflows.md](references/clamp-workflows.md) | The original CLaMP CLI downloads Hugging Face assets on first run and caches key features under the inference layout. |
| Diagnose failures across these workflows | [references/troubleshooting.md](references/troubleshooting.md) | Start with data/checkpoint/hardware checks before changing model code. |

## Explicit routes elsewhere

- Lyric-to-melody, melody-to-lyric, rap lyric, ReLyMe, ROC, SongMASS, and TeleMelody requests route to [../lyric-melody-songwriting/SKILL.md](../lyric-melody-songwriting/SKILL.md).
- GETMusic, MuseCoco, Museformer, MeloForm, and EmoGen symbolic generation or structure-control requests route to [../symbolic-generation-structure/SKILL.md](../symbolic-generation-structure/SKILL.md).
- MusicAgent orchestration, Gradio, plugin, credentials, or multi-tool agent workflows route to [../music-agent-workflows/SKILL.md](../music-agent-workflows/SKILL.md).

## Safe bundled helpers

These helpers validate user-provided layouts only. They do not import Muzic source modules, load models, contact Hugging Face, run Fairseq, invoke MFA, or mutate training data.

```bash
python scripts/validate_clamp_inputs.py --help
python scripts/validate_pdaugment_layout.py --help
```

Use them before expensive runs:

- `scripts/validate_clamp_inputs.py` checks CLaMP model name, query/key modalities, required `inference/` files or folders, text-key counts, `.mxl` readability, and `top_n` consistency.
- `scripts/validate_pdaugment_layout.py` checks the final PDAugment positional-argument layout, frequency JSON shape, metadata CSV columns, speech WAV/transcript layout, MIDI file presence, output directories, and thread count.

## Operating rules

1. Keep MusicBERT, PDAugment, and CLaMP commands separate; they use different dependency stacks and data layouts.
2. Before running source scripts, identify whether the requested step is input validation, CPU preprocessing, model inference, training, or evaluation.
3. Never assume external corpora, checkpoints, Hugging Face downloads, Fairseq user modules, CUDA, MFA, ffmpeg, or old Python packages are already available.
4. Prefer dry layout validation and command planning unless the user explicitly provides the needed data, checkpoints, and runtime budget.
5. When reporting a run plan, include: command, working directory requirement, expected input layout, expected output artifacts, first-run downloads, backend needs, and blockers.
