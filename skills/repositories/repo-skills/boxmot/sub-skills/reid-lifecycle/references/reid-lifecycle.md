# ReID Lifecycle Workflows

## Train a ReID model

```bash
boxmot train \
  --model osnet_x0_25 \
  --dataset market1501 \
  --data-dir /data/reid \
  --device cpu
```

Training from a recipe or config:

```bash
boxmot train --recipe csl_tinyvit_11m --data-dir /data/reid --epochs 5
boxmot train --cfg custom_config.yaml --epochs 3
```

Training from one or more dataset YAMLs:

```bash
boxmot train \
  --data market1501.yaml \
  --data duke.yaml \
  --epochs 120 \
  --device 0
```

Dataset YAMLs can include fields such as `dataset`, `path`, `train`, `query`, `gallery`, and optional `download` code. Treat `download` as side-effecting and do not run it unless the user accepts that behavior.

## Evaluate a ReID checkpoint

```bash
boxmot eval-reid \
  --weights runs/reid_train/exp/best.pt \
  --dataset market1501 \
  --data-dir /data/reid \
  --device cpu
```

Python:

```python
from boxmot import BoxMOT

metrics = BoxMOT().eval_reid(
    weights="runs/reid_train/exp/best.pt",
    model="mobilenetv4",
    dataset="market1501",
    data_dir="/data/reid",
    device="cpu",
)
```

The evaluator extracts query/gallery embeddings, computes distances, and reports `mAP`, `rank1`, `rank5`, and `rank10`.

## Compare ReID checkpoints

Use `compare-reid` for model-by-target evaluation matrices.

```bash
boxmot compare-reid \
  --weights runs/reid_train/exp/best.pt \
  --target market1501=/data/reid/Market-1501-v15.09.15 \
  --output runs/reid_cross_domain
```

Repeat `--weights` for multiple checkpoints and repeat `--target DATASET=DATA_DIR` for multiple target datasets. Use `--label` to control output labels, `--model` to override architecture inference, `--include-same-dataset` when same-domain evaluation should be included, and `--continue-on-error` to record failed pairs instead of failing fast.

## Export ReID weights

```bash
boxmot export --weights osnet_x0_25_msmt17.pt --include onnx
boxmot export --weights runs/reid_train/exp/best.pt --include onnx --include openvino
```

Python:

```python
from boxmot import BoxMOT

exported = BoxMOT(reid="osnet_x0_25_msmt17.pt").export(include=("onnx",), dynamic=True)
print(exported.files)
```

TensorRT engine export uses ONNX as an intermediate and requires a compatible GPU/TensorRT stack. TFLite static quantization requires representative calibration crops.

## Embed crops or boxes

```python
from boxmot import ReIDModel

reid = ReIDModel("osnet_x0_25_msmt17.pt", device="cpu", preprocess="resize")
features_from_crop = reid.embed("crop.jpg")
features_from_boxes = reid.embed(image_array, boxes=dets[:, :4])
```

`BoxMOT(reid="...").embed(source=..., boxes=...)` exposes the same flow through the facade.

## Dataset layout expectations

Built-in names include:

- `market1501`
- `duke` / `dukemtmcreid`
- `cuhk03`
- `msmt17`
- `msmt17_merged`
- `veri` / `veri776`

Market1501-style datasets have split directories like:

```text
Market-1501-v15.09.15/
  bounding_box_train/
  query/
  bounding_box_test/
```

Use explicit dataset YAMLs when custom layouts differ from the registered defaults.
