---
name: reid-lifecycle
description: "Use BoxMOT for ReID training, evaluation, comparison, export,
  embedding extraction, and registry inspection."
metadata:
  disco-role: operating
disable-model-invocation: true
license: AGPL 3.0
---

# ReID Lifecycle

Use this sub-skill when the task involves ReID models: training a backbone, evaluating a checkpoint, comparing checkpoints across datasets, exporting deployment formats, generating embeddings, or inspecting registries.

## Covers

- `boxmot train`
- `boxmot eval-reid`
- `boxmot compare-reid`
- `boxmot export`
- `BoxMOT.train(...)`, `BoxMOT.eval_reid(...)`, `BoxMOT.export(...)`, and `BoxMOT.embed(...)`
- `boxmot.ReIDModel`
- training recipes, ReID dataset names, export formats, and checkpoint metadata

## Does not cover

- live tracking or tracker output schemas unless the question is about ReID features used by a tracker
- benchmark `generate` / `eval` / `tune` / `research` cache workflows
- native C++ build tooling except native ReID notes relevant to C++ trackers

## Read first

- [ReID lifecycle workflows](references/reid-lifecycle.md)
- [Model and export overview](references/model-and-export-overview.md)
- [Troubleshooting](references/troubleshooting.md)
- [Registry summary script](scripts/reid_registry_summary.py)

## Good prompts for this route

- "Train a ReID model on Market1501."
- "Evaluate this checkpoint and save mAP/rank metrics."
- "Compare these two checkpoints across Duke and Market1501."
- "Export an OSNet checkpoint to ONNX or TensorRT."
- "Generate embeddings for image crops and pass them to a tracker."

## Typical workflow

1. Determine whether the user needs training, single-checkpoint evaluation, multi-checkpoint comparison, export, or embedding inference.
2. Verify the dataset root and expected split layout before suggesting heavy runs.
3. Check checkpoint metadata when model architecture is ambiguous.
4. Match `preprocess`, image size, and inference feature overrides between train/eval/export as needed.
5. Use the registry summary script for a safe inventory before recommending a model or format.

## Entry points

```bash
boxmot train --model osnet_x0_25 --dataset market1501 --data-dir /data/reid --device cpu
boxmot eval-reid --weights runs/reid_train/exp/best.pt --dataset market1501 --data-dir /data/reid --device cpu
boxmot compare-reid --weights runs/reid_train/exp/best.pt --target market1501=/data/reid/Market-1501-v15.09.15
boxmot export --weights osnet_x0_25_msmt17.pt --include onnx
```

Python facade:

```python
from boxmot import BoxMOT, ReIDModel

api = BoxMOT()
train_result = api.train(model="mobilenetv4", dataset="market1501", data_dir="/data/reid", epochs=5)
metrics = api.eval_reid(weights=train_result.weights_path, dataset="market1501", data_dir="/data/reid")
features = ReIDModel("osnet_x0_25_msmt17.pt", device="cpu").embed("crop.jpg")
```

Use `scripts/reid_registry_summary.py` when the user needs to know registered backbones, recipes, datasets, or export formats before launching a heavy job.
