---
name: image-data-utilities
description: "Prepare, validate, convert, and display chest X-ray image inputs
  while preserving DICOM originals and reporting utility metadata."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Image-data utilities

Use this skill when a chest X-ray input must be checked, made viewable, or
handed between the upload/UI layer and an image-capable tool. It covers the two
utility tools:

- `DicomProcessorTool` converts a DICOM pixel array to a temporary PNG and
  returns conversion metadata.
- `ImageVisualizerTool` validates a JPG/PNG path and returns the path plus
  display metadata. Its normal `_run` path reports a display result; it does
  not call the matplotlib rendering method in the current implementation.

This skill does **not** perform model inference. Route interpretation,
classification, segmentation, grounding, or report generation to
[chest-xray-analysis](../chest-xray-analysis/SKILL.md). Route LangGraph
construction to [agent-orchestration](../agent-orchestration/SKILL.md), upload
widgets, chat history, and Gradio state to
[web-interface](../web-interface/SKILL.md), and benchmark data preparation to
[benchmark-evaluation](../benchmark-evaluation/SKILL.md).

## Operating contract

1. Keep the input path and its role explicit: `original_path` is the preserved
   source used for archival or a tool that explicitly supports that format;
   `display_path` is a viewable PNG/JPG path for the UI or an image-only tool.
2. Validate a path before invoking a utility. Use the bundled
   `scripts/validate_image_input.py` for existence, supported suffix, lightweight
   file-signature, and optional output-directory checks.
3. For DICOM, preserve the original file first. Convert a working/display copy
   with `DicomProcessorTool`; never replace the original with the generated PNG.
4. Treat DICOM-derived fields such as `PatientID` and `StudyDate` as sensitive.
   Pass only the metadata needed by the next step, avoid logging it, and do not
   claim that conversion anonymizes the source.
5. Inspect the returned tuple for an `error` key before using `image_path`.
   Utility failures are data-preparation failures, not evidence about the
   patient's image.

See [api-reference.md](references/api-reference.md) for exact inputs and
outputs, [data-formats.md](references/data-formats.md) for format and privacy
rules, [workflows.md](references/workflows.md) for path handoffs, and
[troubleshooting.md](references/troubleshooting.md) for recovery actions.

## Choose the path

### Existing PNG/JPG/JPEG

- Validate the file and optional destination directory.
- Pass the existing image path to `ImageVisualizerTool._run` when a display
  record is required.
- Pass that same path to a downstream model tool only when its contract accepts
  the format. Keep this utility step separate from model-specific preprocessing.

`ImageVisualizerInput` documents JPG and PNG. JPEG is commonly represented by
`.jpg` or `.jpeg`; do not silently accept an arbitrary suffix merely because a
reader might open it.

### DICOM

- Validate the original file as DICOM-like input without dumping tags.
- Call `DicomProcessorTool._run(dicom_path, window_center, window_width)`.
- If both window parameters are absent, the tool first uses the first value of
  DICOM `WindowCenter`/`WindowWidth` when present. If either is still absent,
  it uses a min/max scale. If both are present, it clips and scales to uint8.
- If `RescaleSlope` and `RescaleIntercept` are both present, apply them before
  windowing or min/max scaling (as the tool does).
- Use returned `image_path` as the display path and retain the original DICOM
  path as the source path. The metadata also records `original_path` and
  `output_path` on success.
- Use the PNG for a model tool that only reads JPG/PNG/PIL/skimage inputs. A
  DICOM conversion is not a promise that every model tool can read DICOM.

A caller may supply a positive window width and a clinically appropriate center
when the source values are known. Do not invent window settings to compensate
for a malformed file; fix or reroute the input instead.

## Display parameters

`ImageVisualizerTool._run` accepts `image_path`, optional `title`, optional
`description`, `figsize=(width, height)`, and `cmap="rgb"`. For a grayscale CXR,
use a grayscale colormap such as `"gray"` when actual rendering is requested.
The implementation treats `"rgb"` specially and passes other colormap names to
matplotlib. If a non-`rgb` colormap is selected for a multi-channel array, its
renderer keeps only the first channel.

The success result is a two-item tuple: `output={"image_path": image_path}` and
metadata containing whether title/description were supplied, the requested
`figsize` and `cmap`, and `analysis_status="completed"`. A missing file returns
an error tuple; do not treat that as a successful visualization.

## UI path distinction

The interface stores uploaded data in managed temporary storage. It keeps an
`original_file_path` for the uploaded file and a separate `display_file_path`.
For a `.dcm` upload it converts only for display; for a regular image the two
paths can be the same. UI rendering should use `display_file_path`, while a
message/tool handoff must choose the path according to the receiving tool's
format contract. In particular, do not encode raw DICOM bytes as if they were a
JPEG data URL. If an image API needs base64, encode the PNG display derivative
and use its actual image MIME type, while retaining the original for archival
or explicitly DICOM-aware processing.

The utility result from `image_visualizer` contains the path to show in the UI;
it is not a model answer. See [web-interface](../web-interface/SKILL.md) for
state and event handling.

## Safety and cleanup

- Do not print full DICOM metadata or embed sensitive tags in titles,
  descriptions, chat messages, or benchmark records.
- Use a caller-owned temporary/output directory with appropriate permissions.
  The DICOM tool creates a unique `processed_dicom_<token>.png`; it does not
  anonymize or automatically delete that file.
- Clean generated derivatives only through an explicit, narrowly scoped cleanup
  policy owned by the caller. Never delete the original input as part of this
  skill.
- Stop on a missing path, unsupported suffix, invalid pixel data, or unwritable
  destination and report the actionable error. Do not fall back to a random
  file or silently reinterpret a DICOM as an ordinary image.
