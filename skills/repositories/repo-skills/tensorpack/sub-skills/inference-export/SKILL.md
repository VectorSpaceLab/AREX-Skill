---
name: inference-export
description: "Use Tensorpack PredictConfig, OfflinePredictor, SmartInit,
  checkpoints, model export, and model-conversion workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# inference-export

Root skill id: `tensorpack`.

This sub-skill covers Tensorpack inference, checkpoint inspection, export, and optional model-conversion flows. Use it when a task is about turning trained weights into a predictor, a SavedModel, a compact graph, or a clean inference graph.

## Use this sub-skill for

- `PredictConfig`, `OfflinePredictor`, `OnlinePredictor`, and `FeedfreePredictor`.
- `SmartInit`, `SaverRestore`, `DictRestore`, and checkpoint / `.npz` loading.
- `ModelExporter.export_serving()` and `ModelExporter.export_compact()`.
- `tensorpack.utils.loadcaffe` and Caffe-to-`npz` conversion flows.
- Example inference routes from export, saliency, CAM, ResNet loading, and Faster R-CNN prediction scripts.

## Route elsewhere

- Training loops, callbacks, trainer selection, or resume semantics -> `../training/SKILL.md`.
- Input pipelines, augmentation, serializers, or dataset plumbing -> `../dataflow/SKILL.md`.
- Deployment orchestration beyond TensorFlow export formats -> document only, do not build here.

## Read first

- [API reference](references/api-reference.md)
- [Checkpoint guide](references/checkpoints.md)
- [Workflow guide](references/workflows.md)
- [Troubleshooting guide](references/troubleshooting.md)
- [Checkpoint inspector](scripts/inspect_checkpoint.py)
- [Export demo](scripts/export_model_demo.py)

## Operating rules

1. Prefer a clean inference graph. If you build the graph yourself, wrap it in `TowerContext(..., is_training=False)`.
2. Do not import a training metagraph for inference. Recreate only the tensors needed for prediction.
3. Restore parameters by exact name. When names or shapes differ, read the checkpoint guide before relaxing mismatch checks.
4. Expose graph endpoints with `tf.identity(..., name='...')` or by using the exact tensor names produced by the tower.
5. Use `OfflinePredictor` for the common numpy-array path.
6. Use `OnlinePredictor` only when you already own a live session and tensor handles.
7. Use `FeedfreePredictor` only when the inputs come from an `InputSource`.
8. Prefer `ModelExporter.export_serving()` for SavedModel and `export_compact()` for a frozen/pruned `.pb`.
9. Keep Caffe conversion optional. It depends on Caffe Python bindings, model files, and usually OpenCV.

## Predictor roles

- `PredictConfig` is the configuration hub. It can be built from a `ModelDesc`, a plain `tower_func` plus `input_signature`, or a `TowerFunc` wrapper.
- `OfflinePredictor` builds a fresh graph and session from that config, then accepts numpy inputs and returns numpy outputs.
- `OnlinePredictor` is a thin wrapper around an existing session plus explicit tensors.
- `FeedfreePredictor` consumes an `InputSource` instead of feeds and is useful when the input is already staged, queued, or dataflow-driven.

## Quick decision map

- I have a checkpoint, `.npz`, or dict: see [Checkpoint guide](references/checkpoints.md).
- I need to inspect variable names or dump a normalized `.npz`: run `scripts/inspect_checkpoint.py`.
- I need a simple predictor from numpy arrays: see [Workflow guide](references/workflows.md).
- I need SavedModel / TensorFlow Serving export: see [Workflow guide](references/workflows.md).
- I need a compact frozen graph: see [Workflow guide](references/workflows.md).
- I need a fake-data end-to-end export demo: run `scripts/export_model_demo.py`.
- I need a Caffe model converted to Tensorpack weights: see [Workflow guide](references/workflows.md) and [Troubleshooting guide](references/troubleshooting.md).

## Distilled example patterns

The bundled references cover these source-evidence patterns without requiring the original example checkout:

- Basic export: toy training, a separate inference graph, SavedModel export, compact graph export, and apply modes.
- Caffe-imported vision models: convert Caffe weights to `.npz`, preprocess images, and load with `SmartInit`.
- Converted ResNet inference: load converted `.npz` weights, run ImageNet-style prediction, and optionally evaluate when the user supplies data.
- Saliency and CAM: build predictors around fixed ImageNet-style models and fetch gradients or activation-map tensors.
- Detection prediction/export: detector prediction, evaluation JSON, multiple outputs, postprocessing, and compact/Serving export choices.

## What this sub-skill does not own

- Training graph construction, callbacks, monitors, or trainer wiring.
- Data loading, augmentation, serializers, or batching policy.
- General serving orchestration beyond TensorFlow export formats.

If a request mixes inference with any of the above, keep the prediction or export pieces here and route the rest to the adjacent sub-skills.
