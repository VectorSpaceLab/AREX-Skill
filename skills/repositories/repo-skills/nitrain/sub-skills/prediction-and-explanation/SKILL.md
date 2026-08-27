---
name: prediction-and-explanation
description: "Run Nitrain prediction workflows and inspect the current
  OcclusionExplainer surface."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Prediction and explanation

Use this sub-skill when a user wants to run dataset-level prediction with
`Predictor`, reconstruct slice-based outputs back into ANTs images, or inspect
what `OcclusionExplainer` does in the current release.

## What belongs here

- `Predictor` and its sampler-driven inference path.
- Output post-processing for regression, segmentation, and classification.
- The current `OcclusionExplainer` API surface and its limitations.

## What does not belong here

- Dataset creation and reader selection: use `sub-skills/datasets-readers/`.
- Transforms, samplers, and loader batching: use
  `sub-skills/preprocessing-and-loading/`.
- Architecture discovery and training: use `sub-skills/models-training/`.

## Typical user requests

- "Predict on a dataset"
- "Restore slice predictions into a 3D image"
- "Use a sampler for inference"
- "Check whether the occlusion explainer actually works"

## Working pattern

1. Make sure the model was built for the same geometry the predictor expects.
2. Use the same sampler family at inference time that the model was trained with
   when shape reconstruction matters.
3. Choose the task string carefully because prediction post-processing depends on
   whether the task is regression, segmentation, or classification.
4. Keep the input dataset tiny when you are only proving the prediction path.

## Read these references

- [references/api-reference.md](references/api-reference.md) for the verified
  predictor and explainer signatures.
- [references/workflows.md](references/workflows.md) for prediction snippets
  and output-shape rules.
- [references/troubleshooting.md](references/troubleshooting.md) for
  sampler-axis errors, shape mismatch, and the current explainer stub.

## Smoke check

After installing dependencies, run the bundled helper [scripts/check_install.py](../../scripts/check_install.py):

```bash
python scripts/check_install.py --mode predictor
```

Use this when you want to confirm the prediction path before you hand off to a
larger workflow.

## Key decisions

- `Predictor(model, task, sampler=None, expand_dims=-1)` stores the model, task,
  sampler, and expansion axis.
- `Predictor.predict(dataset)` loops over dataset records, applies the sampler,
  runs the model, and then normalizes the outputs by task.
- `expand_dims=None` disables extra dimension expansion.
- `SliceSampler` output is rolled back into the original axis position during
  prediction when the sampler type is recognized.

## Common outcomes

- Regression predictions may be returned as ANTs images when the output is
  multidimensional.
- Segmentation and classification outputs are rounded to `uint8` in the current
  implementation.
- Slice-based predictions should retain the original image orientation once the
  sampled axis is restored.

## Watch for these signals

- If the prediction shape is wrong, the sampler axis or `expand_dims` setting is
  usually the first thing to inspect.
- If the output type is not what you expect, check the task string and whether
  the model output is multidimensional.
- `OcclusionExplainer.fit()` is a placeholder in this snapshot and currently
  returns `1`.

## Before handing off

If the request grows into actual saliency, heatmap, or attribution logic, note
that the current explainer surface is incomplete and do not promise more than
what the source code provides.
