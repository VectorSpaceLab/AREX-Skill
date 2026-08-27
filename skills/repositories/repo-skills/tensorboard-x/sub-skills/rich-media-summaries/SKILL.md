---
name: rich-media-summaries
description: "Image, audio, video, histogram, PR-curve, text, and mesh summary
  workflows for tensorboardX."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# rich-media-summaries

Use this sub-skill when the tensorboardX task is about non-scalar summary payloads.

## Covers

- `SummaryWriter.add_image()` and `add_images()`
- `SummaryWriter.add_image_with_boxes()`
- `SummaryWriter.add_figure()`
- `SummaryWriter.add_audio()`
- `SummaryWriter.add_video()`
- `SummaryWriter.add_text()`
- `SummaryWriter.add_histogram()` and `add_histogram_raw()`
- `SummaryWriter.add_pr_curve()` and `add_pr_curve_raw()`
- `SummaryWriter.add_mesh()`
- direct `tensorboardX.summary.*` helpers for the same payload families
- `tensorboardX.utils` shape and video helpers used by these summaries

## Route out

- scalar logging, writer lifecycle, hparams, `purge_step`, or event-file checks: [../logging-core/SKILL.md](../logging-core/SKILL.md)
- model graphs, ONNX/OpenVINO, and projector embeddings: [../graph-and-embedding-plugins/SKILL.md](../graph-and-embedding-plugins/SKILL.md)
- global writer, multiprocessing, S3/GCS, and Comet integrations: [../remote-and-parallel-integrations/SKILL.md](../remote-and-parallel-integrations/SKILL.md)

## Read these references first

- [references/api-reference.md](references/api-reference.md): method signatures and summary builders.
- [references/data-formats.md](references/data-formats.md): tensor shapes, channel conventions, label handling, and optional dependency requirements.
- [references/workflows.md](references/workflows.md): end-to-end payload recipes and the safest sequence for each summary family.
- [references/troubleshooting.md](references/troubleshooting.md): shape, dtype, and optional dependency failures.

## Bundled smoke script

- [scripts/tbx_media_summary_smoke.py](scripts/tbx_media_summary_smoke.py): creates a tiny temporary run with images, boxes, histogram, PR curve, text, mesh, and optional figure/audio/video checks when the dependencies are installed.

## Working rules

- Prefer a CPU-only tiny fixture unless the user explicitly wants a different backend; this sub-skill does not require GPU support.
- Use `tensorboardX.summary` helpers only when the caller needs direct protobuf construction or when `SummaryWriter` is too high-level.
- Treat `moviepy`, `imageio`, `matplotlib`, `soundfile`, and `pillow` as optional dependencies that are activated only for the payloads that need them.
- Keep payloads small and deterministic so the helper script remains safe to run in a fresh environment.
- If the user only needs scalar logging, route them back to `logging-core` instead of expanding this route.

## Common user requests

- "How do I log a batch of images?"
- "Why is my audio summary empty or clipped?"
- "How do I log a matplotlib figure?"
- "What shape should my video tensor have?"
- "How do I encode a PR curve or mesh summary?"

## What to avoid

- Do not depend on the original repository checkout.
- Do not point future agents to the source repo examples as runtime instructions.
- Do not treat a missing optional dependency as a failure for the whole skill when the user did not ask for that payload.
