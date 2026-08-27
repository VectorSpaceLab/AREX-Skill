---
name: data-preparation
description: "Prepare, validate, convert, and batch Motus robot, latent-action,
  RoboTwin, and LeRobot data, including frame sampling, normalization, language
  features, and three-camera inputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Motus data preparation

Use this route when a task involves Motus dataset layout, episode validation,
RoboTwin conversion, LeRobot preparation, image-view concatenation, action
normalization, or the batch contract consumed by training and inference.

- Read [data-formats.md](references/data-formats.md) before selecting a dataset
  type or diagnosing missing files.
- Read [api-reference.md](references/api-reference.md) for the dataset factory,
  collate output, sampling formulas, and image helpers.
- Read [workflows.md](references/workflows.md) for conversion, LeRobot cache,
  and three-view recipes. Networked or mutating source workflows are described
  but not silently run.
- Read [troubleshooting.md](references/troubleshooting.md) when an episode is
  rejected, language/image alignment fails, or an optional dependency is absent.
- For model inputs and inference output, continue to
  [model-inference](../model-inference/SKILL.md); for YAML training launch
  configuration, use [training](../training/SKILL.md).

## Operating procedure

1. Identify the dataset family (`robotwin`, `ac_one`, `aloha_agilex_2`,
   `latent_action`, or `lerobot`) and whether the task is training, validation,
   conversion, or inference preparation.
2. Validate the directory structure and one-to-one episode resources before
   starting a loader. Preserve the same episode id across video, qpos/action,
   language embedding, and instruction text where that family requires it.
3. Set `common.num_video_frames`, temporal downsampling, and
   `video_action_freq_ratio` together. The action chunk is derived, not an
   independent guess; verify its shape against `common.action_dim`.
4. Keep language resources aligned: a selected embedding variant must correspond
   to the matching instruction text when VLM inputs are built. Pre-encoded WAN
   T5 embeddings are distinct from Qwen VLM processor inputs.
5. Run the bundled [camera helper](scripts/concat_cameras.py) for three-view
   images when the downstream model expects a concatenated frame. Check the
   output dimensions before writing a dataset.
6. Treat download, conversion, video encoding, and T5-cache commands as
   explicit side-effect operations. Confirm paths, free space, and backups
   before running them; use the reference recipes rather than assuming they
   are harmless smoke tests.

The public runtime skill is self-contained: original repository scripts and
checkout paths are evidence only, not commands future agents should reopen.
