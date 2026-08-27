---
name: samgeo3-workflows
description: "Guides SamGeo3 and SamGeo3Video workflows for SAM3/SAM3.1 text,
  point, box, tiled, batch, and video segmentation with CUDA/backend
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SAM3 and SAM3.1 workflows

Use this sub-skill when the task names `SamGeo3`, SAM3, SAM3.1,
`facebook/sam3`, `facebook/sam3.1`, text-prompt SAM3 masks, tiled GeoTIFF
segmentation, batch image segmentation, or SAM3 video/object tracking.

## Read this when

- The user needs SAM3 text prompts: `sam.generate_masks("building")`.
- The user has point or box prompts and wants SAM3 instance interactivity.
- A large GeoTIFF needs tiled segmentation with overlap.
- The input is a video or frame sequence and the user wants prompt propagation.
- The failure involves `backend="meta"`, `backend="transformers"`, SAM3.1,
  checkpoint download, bfloat16 conversion, or CUDA availability.

## Route elsewhere

- Original SAM or SAM2 image/prompt workflows: [core-segmentation](../core-segmentation/SKILL.md).
- Raster CRS, band selection, vector conversion, split/merge, or device helpers:
  [geospatial-utilities](../geospatial-utilities/SKILL.md).
- LangSAM/GroundingDINO text prompts with SAM1/SAM2: [specialized-models](../specialized-models/SKILL.md).
- HTTP API calls to `/segment/text`, `/segment/predict`, or `/segment/automatic`:
  [api-server](../api-server/SKILL.md).

## Backend rules

- Treat real SAM3/SAM3.1 inference as CUDA-backed. CPU import or mock tests do
  not prove runtime readiness.
- `backend="meta"` is the default and supports `facebook/sam3.1`.
- `backend="transformers"` is only for supported SAM3 model ids; SAM3.1 is a
  Meta checkpoint path and should use `backend="meta"`.
- Use `enable_inst_interactivity=True` when point/box prompt methods such as
  `predict_inst()` are needed.
- For gated Hugging Face assets, confirm access and authentication before model
  construction.

## Workflow sequence

1. Run [scripts/samgeo3_backend_check.py](scripts/samgeo3_backend_check.py) with
   `--require-cuda` before a real SAM3 run.
2. Choose image/text vs instance vs tiled vs video workflow using
   [workflows.md](references/workflows.md).
3. Validate input image CRS/bands with the utilities sub-skill.
4. Construct `SamGeo3` or `SamGeo3Video` only after model access and GPU memory
   are acceptable.
5. Save outputs and convert to vectors only after inspecting mask counts and
   bounding boxes on a small example.

## References and scripts

- [workflows.md](references/workflows.md) gives copyable SAM3 image, prompt,
  tiled, batch, and video patterns without depending on source notebooks.
- [api-reference.md](references/api-reference.md) records verified signatures,
  model ids, backend constraints, and test-backed SAM3.1 behavior.
- [troubleshooting.md](references/troubleshooting.md) covers CUDA, checkpoint,
  backend, dtype, cache, and video-memory failures.
- [scripts/samgeo3_backend_check.py](scripts/samgeo3_backend_check.py) safely
  checks imports, registry ids, CUDA, and `SamGeo3` signatures without loading
  model weights.

## Native validation candidates

- `tests/test_samgeo3.py` is the safe native candidate for backend selection,
  SAM3.1 checkpoint routing, and user-error reporting.
- SAM3 example notebooks are GPU/network/model-download candidates. Run them
  only when final verification explicitly authorizes Hugging Face/model assets.
