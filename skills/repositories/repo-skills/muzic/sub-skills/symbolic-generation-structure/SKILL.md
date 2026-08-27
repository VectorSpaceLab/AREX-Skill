---
name: symbolic-generation-structure
description: "Route GETMusic, MuseCoco, Museformer, MeloForm, and EmoGen
  symbolic music generation workflows for any-track generation, text control,
  long-structure modeling, form refinement, and emotion control."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Symbolic Generation Structure

Use this sub-skill for Muzic projects that generate or refine symbolic music without lyric generation or retrieval:
GETMusic, MuseCoco, Museformer, MeloForm, and EmoGen.

## Start here

- Read [references/getmusic.md](references/getmusic.md) for GETMusic track generation, position infilling, preprocessing, and training layout.
- Read [references/musecoco.md](references/musecoco.md) for the two-stage text-to-attribute and attribute-to-music pipeline.
- Read [references/structure-emotion-generation.md](references/structure-emotion-generation.md) for Museformer, MeloForm, and EmoGen.
- Read [references/troubleshooting.md](references/troubleshooting.md) for checkpoint, Fairseq, Triton, Java, jSymbolic, and prompt-format failures.
- Use [scripts/validate_getmusic_request.py](scripts/validate_getmusic_request.py) to check GETMusic track letters and position grammar before a generation run.
- Use [scripts/plan_musecoco_pipeline.py](scripts/plan_musecoco_pipeline.py) to plan the MuseCoco stage-1 / stage-2 artifact handoff.

## Route boundaries

- Understanding / retrieval workflows belong in [music-understanding-retrieval](../music-understanding-retrieval/SKILL.md).
- Lyric and songwriting workflows belong in [lyric-melody-songwriting](../lyric-melody-songwriting/SKILL.md).
- MusicAgent orchestration belongs in [music-agent-workflows](../music-agent-workflows/SKILL.md).

## Operating notes

- Keep this skill focused on artifact order, prompt grammar, and workflow boundaries.
- Treat training and inference recipes as checkpoint- and dataset-dependent unless the bundled references say otherwise.
- Validate input structure first, then pick the smallest matching workflow.
- When a request crosses into another Muzic family, route there instead of stretching the current recipe.
