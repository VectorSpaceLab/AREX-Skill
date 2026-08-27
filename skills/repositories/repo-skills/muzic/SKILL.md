---
name: muzic
description: "Route Microsoft Muzic research workflows for music understanding,
  retrieval, symbolic generation, songwriting, and MusicAgent orchestration."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Muzic Repo Skill

Use this skill when a task names Muzic or asks for AI-music workflows that match the Muzic research projects: symbolic music understanding, cross-modal music retrieval, lyrics transcription augmentation, lyric-to-melody songwriting, symbolic music generation, structure/form/emotion control, or MusicAgent orchestration.

Muzic is a research monorepo, not a single pip-installable Python package. Most workflows are project-specific scripts with old dependency stacks, external datasets, checkpoints, or credentials. Start by routing to the right sub-skill, then validate inputs and runtime prerequisites before running heavyweight model code.

## Quick routing

| User intent | Read |
|---|---|
| MusicBERT OctupleMIDI, symbolic music understanding, pretraining/fine-tuning/evaluation, PDAugment speech/MIDI augmentation, or CLaMP semantic search/zero-shot classification | [sub-skills/music-understanding-retrieval/SKILL.md](sub-skills/music-understanding-retrieval/SKILL.md) |
| DeepRapper rap lyrics, SongMASS lyric-to-melody or melody-to-lyric, TeleMelody, ReLyMe, ROC, lyric/chord templates, songwriting metrics | [sub-skills/lyric-melody-songwriting/SKILL.md](sub-skills/lyric-melody-songwriting/SKILL.md) |
| GETMusic any-track generation/infilling, MuseCoco text-to-music, Museformer long structure, MeloForm form refinement, EmoGen emotion-controlled generation | [sub-skills/symbolic-generation-structure/SKILL.md](sub-skills/symbolic-generation-structure/SKILL.md) |
| MusicAgent installation, config, secrets, model/tool downloads, CLI or Gradio startup, plugin/tool selection | [sub-skills/music-agent-workflows/SKILL.md](sub-skills/music-agent-workflows/SKILL.md) |
| Repo-wide setup, dependency-family choices, old-stack caveats, and safe workspace checks | [references/setup-and-environments.md](references/setup-and-environments.md) and `scripts/check_muzic_workspace.py` |
| One-table map of Muzic subprojects, typical inputs, outputs, and owner sub-skill | [references/project-map.md](references/project-map.md) |
| Cross-cutting install, data, checkpoint, backend, and credential failures | [references/troubleshooting.md](references/troubleshooting.md) |

## First steps for any Muzic task

1. Identify the subproject and task family from [references/project-map.md](references/project-map.md).
2. Check whether the request is only planning/validation or an actual model run. Model runs often need checkpoints, datasets, old Torch/Fairseq/TensorFlow versions, CUDA, Java, system audio packages, or API credentials.
3. If the user has a Muzic checkout or prepared workspace, run the safe checker before expensive commands:

   ```bash
   python scripts/check_muzic_workspace.py --workspace /path/to/muzic --expect musicbert clamp getmusic musicagent
   ```

4. Load the nearest sub-skill and its references. Use bundled validators/planners there before invoking original research scripts.
5. When giving commands, state the required working directory, input files, expected outputs, dependency family, and what is intentionally not verified.

## Setup stance

- Do not install root `requirements.txt` blindly. It pins old and conflicting ML stacks; choose the smallest per-project environment described in [references/setup-and-environments.md](references/setup-and-environments.md).
- Treat full training and inference as data/checkpoint/backend dependent unless a sub-skill explicitly identifies a CPU-only validation path.
- Do not assume Hugging Face, Google Drive, or dataset downloads are acceptable. Ask or plan explicitly before network-heavy downloads.
- Do not hardcode credentials, local cache paths, or `.env` values in instructions or generated files.
- Do not mutate system package managers, Conda base, or user environments without approval.

## Safe bundled helpers

Root helper:

```bash
python scripts/check_muzic_workspace.py --help
```

Sub-skill helpers:

- `sub-skills/music-understanding-retrieval/scripts/validate_clamp_inputs.py`
- `sub-skills/music-understanding-retrieval/scripts/validate_pdaugment_layout.py`
- `sub-skills/lyric-melody-songwriting/scripts/plan_deeprapper_command.py`
- `sub-skills/lyric-melody-songwriting/scripts/check_songmass_telemelody_assets.py`
- `sub-skills/lyric-melody-songwriting/scripts/make_roc_input_template.py`
- `sub-skills/symbolic-generation-structure/scripts/validate_getmusic_request.py`
- `sub-skills/symbolic-generation-structure/scripts/plan_musecoco_pipeline.py`
- `sub-skills/music-agent-workflows/scripts/validate_musicagent_config.py`

These helpers are self-contained planning or layout checks. They do not load Muzic model weights, contact remote services, run training, or import source checkout modules.

## Provenance and routing metadata

- Source snapshot and evidence baseline: [references/repo-provenance.md](references/repo-provenance.md).
- Managed router metadata for repo-skill import tooling: [references/repo-routing-metadata.json](references/repo-routing-metadata.json).

## Non-goals

- This skill does not replace the Muzic research code, checkpoints, datasets, or external model assets.
- This skill does not certify that optional CUDA/Triton/Java/system-audio/API-key workflows run in the current environment.
- This skill does not export or import itself; import is intentionally disabled for this production run.
