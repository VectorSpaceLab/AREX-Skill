---
name: latent-sync
description: "Route LatentSync video generation, raw-video preprocessing,
  training, and evaluation workflows to the right sub-skill."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LatentSync

Use this skill when the request is about the LatentSync repository: talking-head video synthesis, raw `.mp4` preprocessing, U-Net or SyncNet training, or SyncNet/FVD evaluation.

## Quick start

1. Run `python scripts/check_env.py --check-imports --check-cuda --check-ffmpeg` before a long workflow.
2. Add `--check-scenedetect` when preprocessing raw clips.
3. Add `--check-assets` when you want the bundled demo inputs or Gradio smoke path.
4. Read the narrow sub-skill before choosing configs or launch commands.

## Route by task

- Generate one video, a small batch, or launch the local UI: [`sub-skills/inference/SKILL.md`](sub-skills/inference/SKILL.md).
- Convert raw videos into aligned, AV-synced, quality-filtered clips: [`sub-skills/data-preparation/SKILL.md`](sub-skills/data-preparation/SKILL.md).
- Choose U-Net or SyncNet configs, build fileslists, or render training launches: [`sub-skills/training/SKILL.md`](sub-skills/training/SKILL.md).
- Score generated clips, validate SyncNet checkpoints, or compare real and fake sets: [`sub-skills/evaluation/SKILL.md`](sub-skills/evaluation/SKILL.md).

## Shared references and helpers

- [`references/configuration.md`](references/configuration.md) — repo-wide config, checkpoint, and resolution map.
- [`references/api-reference.md`](references/api-reference.md) — verified shared runtime call surfaces.
- [`references/troubleshooting.md`](references/troubleshooting.md) — cross-cutting install, import, backend, path, and checkpoint failures.
- [`references/repo-provenance.md`](references/repo-provenance.md) — source snapshot and refresh baseline.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) — structured router metadata for managed discovery.
- [`scripts/check_env.py`](scripts/check_env.py) — safe repo-root, import, CUDA, ffmpeg, scenedetect, and asset checker.

## Working rules

- Always pass `--repo-root` to bundled helpers when the current directory is not the runtime tree.
- Keep temp directories isolated; the pipeline and metrics delete and recreate scratch paths.
- Treat CUDA as required for the core inference, preprocessing, and training workflows; CPU-only checks are useful only for limited import or FVD-style smoke paths.
- Do not route a training, preprocessing, or metric issue through inference just because the same checkpoints or demo assets appear in the stack.
- Use `references/repo-provenance.md` when deciding whether this skill still matches the current checkout or needs refresh.
