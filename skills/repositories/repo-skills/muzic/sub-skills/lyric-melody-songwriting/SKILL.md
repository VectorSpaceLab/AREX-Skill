---
name: lyric-melody-songwriting
description: "Route DeepRapper, SongMASS, TeleMelody, ReLyMe, and ROC
  lyric/songwriting workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Lyric-Melody Songwriting

Use this sub-skill when the task is centered on lyrics, lyric-conditioned melody generation, melody-conditioned lyric generation, or retrieval-based songwriting.

## Route here for
- DeepRapper rap lyric generation with rhyme and rhythm controls.
- SongMASS lyric-to-melody and melody-to-lyric translation, training, or evaluation.
- TeleMelody lyric-to-rhythm and template-to-melody workflows, including inference and metrics.
- ReLyMe constraint-based reranking, scoring, or TeleMelody/SongMASS integration.
- ROC lyric/chord input generation, melody-language-model training, or database-driven generation.

## Route away
- Understanding, retrieval, or PDAugment workflows -> [music-understanding-retrieval](../music-understanding-retrieval/SKILL.md)
- Non-lyric symbolic music generation -> [symbolic-generation-structure](../symbolic-generation-structure/SKILL.md)
- MusicAgent orchestration -> [music-agent-workflows](../music-agent-workflows/SKILL.md)

## Read next
- [DeepRapper reference](references/deeprapper.md)
- [SongMASS / TeleMelody / ReLyMe reference](references/songmass-telemelody-relyme.md)
- [ROC reference](references/roc.md)
- [Troubleshooting](references/troubleshooting.md)

## Bundled helpers
- `scripts/plan_deeprapper_command.py` — print a safe DeepRapper command plan without running it.
- `scripts/check_songmass_telemelody_assets.py` — verify SongMASS and TeleMelody asset layout before inference or training.
- `scripts/make_roc_input_template.py` — create starter `lyrics.txt` and `chord.txt` files for ROC.

## Operating notes
- Treat checkpoints, dictionaries, databases, and generated MIDI files as external assets.
- Keep runtime instructions in this subtree; do not depend on the original source checkout remaining present.
- ReLyMe's SongMASS branch exists in code, but the repository README marks it as under-documented; prefer the score module and bundled notes when routing that path.
- This file is a router only. Detailed command tables, layouts, and failure modes live in the bundled references.
