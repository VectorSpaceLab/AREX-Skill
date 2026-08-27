---
name: deployment-conversion
description: "Export PocketFlow checkpoints to GraphDef or TensorFlow Lite,
  validate conversion artifacts, and troubleshoot mobile deployment or benchmark
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PocketFlow Deployment and Conversion

Use this sub-skill when the user has trained/evaluated PocketFlow checkpoints and asks about exporting GraphDef/PB/TFLite artifacts, channel-pruned graph transformation, quantized export, graph collections, mobile deployment, or inference timing.

## Route first

- For training a model or selecting `uniform-tf`, DCP, or channel-pruning learners before export, read [compression-learners](../compression-learners/SKILL.md).
- For `path.conf`, TensorFlow 1.x setup, launch modes, or GPU probes, read [execution-config](../execution-config/SKILL.md).
- For custom model helper output names, input shapes, data formats, or detection-vs-classification contracts, read [custom-models-data](../custom-models-data/SKILL.md).

## Operating checklist

1. Confirm export prerequisites: TensorFlow 1.x with `tf.contrib.lite`, a checkpoint-like model directory, `.meta` graph file, input/output collections, and the right model helper graph.
2. Read [conversion-tools](references/conversion-tools.md) to choose the export path: plain PB/TFLite, channel-pruned PB/TFLite, quantized PB/TFLite, data-format conversion, graph collection editing, or inference timing.
3. Run [check_conversion_artifacts.py](scripts/check_conversion_artifacts.py) against the model directory before attempting TensorFlow graph conversion.
4. For `uniform-tf` deployment, confirm quantization flags and route back to [compression-learners](../compression-learners/SKILL.md) if checkpoints were not produced by the expected learner.
5. For Android/mobile notes, read [mobile-deployment](references/mobile-deployment.md). Mobile app edits are outside this skill's runnable helpers.
6. If conversion fails, read [troubleshooting](references/troubleshooting.md) before changing flags; many failures are missing collections, unsupported ops, wrong `.meta` layout, or TF1/TFLite incompatibilities.

## Bundled helper

- [check_conversion_artifacts.py](scripts/check_conversion_artifacts.py) - validates model directory artifacts and optionally attempts a TensorFlow `.meta` collection inspection when run in a compatible TF1 environment.

## Verification status

The generated skill verified conversion script flag surfaces and `tensorflow.contrib.lite` importability in a TF1.10 inspection environment. It did not run real checkpoint conversion because no small checkpoint fixture was available and conversion depends on trained model artifacts.
