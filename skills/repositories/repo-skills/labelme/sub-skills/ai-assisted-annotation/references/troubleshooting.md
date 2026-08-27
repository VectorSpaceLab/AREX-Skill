# AI Troubleshooting

## Point prompt rejected for SAM3

This is expected: `sam3:latest` has `supports_point_prompts=False` in the
AI Assist model registry. Use a box prompt or choose SAM/SAM2/EfficientSAM for
point mode. Check before model creation with the bundled compatibility helper.

## Polygon or mask output creates no Shape

The shape builder drops detections without masks for polygon and mask outputs.
Choose rectangle output for bbox-only responses, or use a model/response path
that supplies masks.

## Model download or cache failure

OSAM may fetch model assets on first use. Check network access, model cache
permissions, and the exact model id. Keep real model tests separate from
headless unit tests; the repository's network test is explicitly marked
`network` and is not a safe default.

## Text prompt returns an unexpected label

The text-detection path rejects response annotations whose `text` is not in the
prompt list. Inspect the actual prompt strings and model response before
loosening validation.

## Detection mask shape mismatch

Suppression expects a mask whose height/width equals the inclusive bbox extent.
A mismatch is rejected rather than silently producing incorrect IoU. Verify the
OSAM response contract or normalize the mask before calling suppression.

## Duplicates remain on the canvas

Existing Shape Suppression is disabled by default. Enable
`ai.suppress_existing_shape_matches` or the corresponding control, then inspect
whether candidate overlap is high enough under IoU/containment thresholds.

## GUI AI controls are disabled

The AI widgets are enabled only in compatible canvas modes. Select AI-Points or
AI-Box for AI Assist, or a text-prompt-compatible drawing mode for AI Text Prompt.
A disabled control is not evidence that the model package is broken.
