---
name: tensorboard-x
description: "Router for tensorboardX logging, summaries, graph/projector
  workflows, and integration-safe writer usage."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# tensorboard-x

Use this repo skill when a task mentions `tensorboardX`, `SummaryWriter`, TensorBoard event files, or Python code that logs training progress for later inspection in TensorBoard.

This root skill is a router. It points to focused sub-skills for the common tensorboardX workflow families and keeps the public runtime guidance self-contained.

## Quick start

1. Install the package:
   ```bash
   python -m pip install tensorboardX
   ```
2. Verify the import:
   ```bash
   python -c "from tensorboardX import SummaryWriter; print(SummaryWriter)"
   ```
3. If you want to inspect a run directory, open TensorBoard with:
   ```bash
   tensorboard --logdir <logdir>
   ```
4. If you want a fast install check, run the bundled helper:
   ```bash
   python scripts/tbx_inspect_install.py --help
   python scripts/tbx_inspect_install.py
   ```

If you need graph/projector, media summaries, or remote writer integrations, install the optional packages described in [references/install-and-routing.md](references/install-and-routing.md). Do not assume every optional dependency is needed for every workflow.

## Choose the right sub-skill

### `logging-core`
Use this route for ordinary event logging and writer lifecycle tasks:
- `SummaryWriter` setup and logdir policy
- scalar logging, grouped scalars, hparams, custom scalars
- `use_metadata`, `purge_step`, `flush`, `close`, `reopen`
- `write_to_disk=False`
- event-file sanity checks and `tensorboard --logdir`

Open [sub-skills/logging-core/SKILL.md](sub-skills/logging-core/SKILL.md) when the user asks about scalar series, run directories, hparams, or writer behavior.

### `rich-media-summaries`
Use this route for image, audio, video, histogram, PR curve, text, or mesh summaries.

Open [sub-skills/rich-media-summaries/SKILL.md](sub-skills/rich-media-summaries/SKILL.md) when the user asks about payload shapes, media dependencies, or summary builders such as `tensorboardX.summary.image()` and `SummaryWriter.add_video()`.

### `graph-and-embedding-plugins`
Use this route for model graphs and projector output:
- `SummaryWriter.add_graph()` for PyTorch modules
- `SummaryWriter.add_onnx_graph()`
- `SummaryWriter.add_openvino_graph()`
- `SummaryWriter.add_embedding()` and projector metadata/label-image layout

Open [sub-skills/graph-and-embedding-plugins/SKILL.md](sub-skills/graph-and-embedding-plugins/SKILL.md) when the user asks about tracing models, loading ONNX/OpenVINO files, or writing embedding projector data.

### `remote-and-parallel-integrations`
Use this route for integration boundaries:
- `GlobalSummaryWriter`
- multiprocessing or multi-module logging
- `s3://` and `gs://` record-writer paths
- Comet forwarding and GPU telemetry as optional input sources

Open [sub-skills/remote-and-parallel-integrations/SKILL.md](sub-skills/remote-and-parallel-integrations/SKILL.md) when the task crosses process, credential, or service boundaries.

## What this skill does not do

- It does not expose a tensorboardX CLI; use Python APIs plus TensorBoard as the viewer.
- It does not rely on the original repository checkout at runtime.
- It does not ask future agents to run the source repo's examples or tests.
- It does not treat remote/cloud integrations as enabled by default.

## Shared references

- [references/install-and-routing.md](references/install-and-routing.md): package install options, optional dependency map, and route selection guidance.
- [references/troubleshooting.md](references/troubleshooting.md): cross-cutting import, event-file, and optional dependency issues.
- [references/repo-provenance.md](references/repo-provenance.md): source commit and refresh baseline.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json): router metadata used by the managed repo-skills router.

## Common escape hatch

If you only need to confirm the installation before choosing a workflow, start with `scripts/tbx_inspect_install.py`. It is safe, self-contained, and does not depend on the original repository checkout.
