---
name: inference-and-deployment
description: "Use DLTK's TensorFlow 1.x prediction, full-volume sliding-window
  assembly, crop averaging, metrics, and metadata-preserving medical-image
  deployment workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DLTK inference and deployment

Use this route when the task is to run prediction with an exported DLTK model, assemble patch predictions into a full volume, average stochastic crops, calculate segmentation metrics, or write a NIfTI result. This is an operating guide for DLTK 0.2.1's TensorFlow 1.x graph-execution deployment path.

## Compatibility gate

- Expect Python 3.7 and TensorFlow 1.15-era graph execution. The documented deployment path is `tensorflow.contrib.predictor.from_saved_model`; do **not** claim that a modern TF2 installation provides this predictor or that these recipes are TF2-compatible.
- Confirm the model input and fetched output static shapes before running a volume. The sliding-window utility expects rank-compatible static shapes and a channels-last tensor. The input sample normally has `[batch, spatial..., channels]`; a full-volume application adds a dummy batch dimension.
- Keep model construction and output-key details in [model-building](../model-building/SKILL.md), input/file/reader assumptions in [data-pipelines](../data-pipelines/SKILL.md), and export/training setup in [training-and-estimators](../training-and-estimators/SKILL.md).

## Choose the workflow

1. From the directory containing this file (`inference-and-deployment/`), run `python scripts/sliding_window_plan.py --help`, then provide spatial `--input-shape`, `--window-shape`, and `--output-shape`. The helper performs validation without importing TensorFlow, reading data, or contacting a network.
2. From that same sub-skill directory, run `python scripts/sliding_window_smoke.py`. It exercises the native test shape plus output-smaller, overlapping, and batched assembly using constant synthetic predictions; it does not load a model or dataset.
3. For a real export, read [deployment-workflows.md](references/deployment-workflows.md) and [api-reference.md](references/api-reference.md) first. Discover a numeric export directory, load the TF1 predictor, inspect its tensors, assemble a volume, convert probabilities/logits to the required result, calculate metrics if labels exist, and write output only to an explicitly chosen directory.

## Inference checklist

- Validate all spatial dimensions, the predictor's input/output keys, channel count, `batch_size`, and explicit stride before session execution. A malformed output/window combination can fail in padding or produce empty slices and a zero division counter.
- Treat `sliding_window_segmentation_inference` as an averaging assembler: it runs each patch, adds each output to the corresponding output slice, increments a separate coverage counter, and returns `sum / counter` for each requested op. It returns a list in `ops_list` order, not class labels.
- For segmentation, convert a `[batch, spatial..., classes]` probability or logit result with `np.argmax(result, axis=-1)`. For probabilities, averaging overlapping patches before argmax is the DLTK MRBrainS pattern. For logits, a numerically stable softmax is useful when probabilities are needed, but argmax is unchanged.
- Exclude or report background explicitly when aggregating Dice. DLTK's `dice` returns `NaN` for a class with no predicted and no reference voxels; `np.nanmean(dice[1:])` is an application policy, not a universal score.
- For SimpleITK output, create the array image with the correct spatial order, call `CopyInformation` from the source image, and only then write the requested `.nii`/`.nii.gz`. A shape or direction/spacing mismatch must be diagnosed rather than silently discarded.
- Random-crop regression/classification deployment is stochastic. Record the crop count, shape, seed policy (if any), and aggregation axis; the original IXI examples average four random crops and explicitly warn that results vary between runs.

See [troubleshooting.md](references/troubleshooting.md) before changing geometry, predictor access, export discovery, or metric handling.
