---
name: media-and-exchange
description: "Guide fastdup workflows for video inputs, tar or zip archives,
  cloud paths, and export or exchange helpers."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# media-and-exchange

Use this sub-skill when the data is not just a plain image folder: mp4/avi videos, archives, cloud paths, or exchange plumbing belong here.

## Use when

The request mentions any of the following:

- mp4 or avi video files
- tar, tgz, tar.gz, zip, or webdataset-style archives
- `s3://` or `minio://` input paths
- syncing remote storage locally before a run
- `run_mode=1`, `run_mode=2`, `run_mode=3`, or `run_mode=4` around archives or stored features
- `fastdup.webdataset` helpers
- CVAT or LabelImg exchange/export helpers tied to a completed run

## Typical workflow

1. Confirm whether the input source is video, an archive, or a remote object store.
2. Decide whether the workflow should extract frames first or resume from stored features.
3. Check the local tooling needed for the source type, especially ffmpeg and cloud-sync utilities.
4. Keep the input source and the output work directory separate.
5. Export only after the fastdup run has produced stable outputs.

## What to read

- `../../references/workflows.md` for the archive, cloud, and video workflow family
- `../../references/data-formats.md` for the input-file and output-file conventions
- `../../references/exports.md` for CVAT and LabelImg handoff details
- `../../references/troubleshooting.md` for ffmpeg, cloud-sync, and archive issues
- `references/troubleshooting.md` in this sub-skill for media-specific failures

## Bundled scripts

Use the root export smoke scripts when you need exchange coverage:
- `../../scripts/export_cvat_smoke.py`
- `../../scripts/export_labelimg_smoke.py`

This sub-skill intentionally stays reference-first for video and cloud workflows because they depend on local media or external services.

## Common decisions

- Use the archive path only when the dataset really arrives as tar/zip/webdataset input.
- Use cloud paths only when the source cannot be copied locally first.
- Use the stored-feature path when the run needs to resume from `features.dat` / `nnf.index`.
- Keep video workflows small and codec-aware.
- Treat export helpers as a final-stage exchange step, not as a replacement for the main analysis run.
- TensorBoard projector belongs to `model-enrichment`, not this sub-skill.

## Known limitation

These workflows are the most environment-sensitive part of fastdup. If video codecs, cloud tools, or archive inputs are unavailable, route back to the documented reference path rather than pretending the media workflow is fully validated.
