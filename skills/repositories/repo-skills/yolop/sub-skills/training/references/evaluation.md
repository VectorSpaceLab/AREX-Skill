# YOLOP Evaluation and Metrics

## When to read

Read this when running `tools/test.py`, interpreting validation output from `tools/train.py`, or debugging detection/segmentation metric calculations.

## Source evaluation command

```bash
PYTHONPATH=. python tools/test.py --weights weights/End-to-end.pth
```

`tools/test.py` builds `BddDataset(is_train=False)`, loads a checkpoint into `get_net(cfg)`, creates the multi-head loss, and calls `validate(...)` from `lib/core/function.py`.

## Checkpoint expectations

`tools/test.py` expects a checkpoint dictionary with a `state_dict` key:

```python
checkpoint = torch.load(args.weights)
checkpoint_dict = checkpoint["state_dict"]
model_dict.update(checkpoint_dict)
model.load_state_dict(model_dict)
```

If you only have `final_state.pth` from the end of training, it is a bare state dict, not the same shape as an epoch checkpoint. Adapt the loading code or wrap it into a dictionary before using `tools/test.py` unchanged.

## Detection metrics

The detection path uses:

- `non_max_suppression` from `lib/core/general.py`.
- `scale_coords` to map padded inference coordinates back to original image shape.
- IoU thresholds `torch.linspace(0.5, 0.95, 10)` for mAP@0.5:0.95.
- `ConfusionMatrix` and `ap_per_class` for precision, recall, mAP@0.5, and mAP@0.5:0.95.
- `fitness` weights `[0.0, 0.0, 0.1, 0.9]` for mAP-focused model selection logic.

The default `model.nc` is 1 because the source collapses vehicles into a single traffic-object class when `single_cls=True`.

## Segmentation metrics

The validation loop computes separate `SegmentationMetric` objects for:

- Drivable area: pixel accuracy, IoU, and mIoU.
- Lane line: line accuracy, IoU, and mIoU.

Both prediction and ground-truth masks are cropped to remove letterbox padding before metric accumulation.

## Visualization side effects

When `cfg.TEST.PLOTS=True`, validation writes visualization images under a `visualization` directory inside the logger output directory. It saves:

- Drivable-area prediction and ground truth overlays.
- Lane-line prediction and ground truth overlays.
- Detection prediction and ground-truth boxes for the first validation batch.

Turn plotting off for faster evaluation or headless CI unless those artifacts are required.

## Reported output message

Both training validation and `tools/test.py` log a multi-line summary shaped like:

```text
Driving area Segment: Acc(...) IOU (...) mIOU(...)
Lane line Segment: Acc(...) IOU (...) mIOU(...)
Detect: P(...) R(...) mAP@0.5(...) mAP@0.5:0.95(...)
Time: inference(...s/frame) nms(...s/frame)
```

Use this output to compare runs, but do not compare speed numbers across CPU, CUDA, TensorRT, different image sizes, or different batch sizes without recording the backend and config.
