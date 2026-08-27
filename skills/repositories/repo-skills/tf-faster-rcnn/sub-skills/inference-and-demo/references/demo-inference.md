# Demo and Image Inference

This repository's demo path is intentionally narrow:
`tools/demo.py` restores one pretrained checkpoint, loops over five bundled images in `data/demo/`, and renders detections with matplotlib.
It is not a general image-directory CLI.

## Control flow

1. `cfg.TEST.HAS_RPN = True` turns on RPN proposals for demo inference.
2. The demo loads each image from `cfg.DATA_DIR/demo/<image_name>` with `cv2.imread`.
3. `model.test.im_detect` builds a single-image blob, runs `net.test_image`, rescales boxes back to the original image size, and applies bbox regression if enabled.
4. `tools/demo.py` applies per-class NMS, filters with a fixed confidence threshold, and visualizes the surviving boxes.
5. The script ends with `plt.show()`, so the window blocks until the figures are dismissed.

## Supported selectors

The demo script only accepts these choices:

- `--net vgg16`
- `--net res101`
- `--dataset pascal_voc`
- `--dataset pascal_voc_0712`

The dataset selector does **not** change the label set.
It only changes the checkpoint folder that the script looks in.
Both paths still use the VOC 20-class label list.

### Checkpoint family mapping

| `--net` | Snapshot filename |
| --- | --- |
| `vgg16` | `vgg16_faster_rcnn_iter_70000.ckpt` |
| `res101` | `res101_faster_rcnn_iter_110000.ckpt` |

| `--dataset` | Train-imdb folder used by `tools/demo.py` |
| --- | --- |
| `pascal_voc` | `voc_2007_trainval` |
| `pascal_voc_0712` | `voc_2007_trainval+voc_2012_trainval` |

Example checkpoint prefixes:

- `output/vgg16/voc_2007_trainval/default/vgg16_faster_rcnn_iter_70000.ckpt`
- `output/res101/voc_2007_trainval+voc_2012_trainval/default/res101_faster_rcnn_iter_110000.ckpt`

The demo refuses to start unless the matching `.meta` file exists beside the checkpoint prefix.

## VOC class labels

The demo uses the fixed Pascal VOC label order:

1. `__background__`
2. `aeroplane`
3. `bicycle`
4. `bird`
5. `boat`
6. `bottle`
7. `bus`
8. `car`
9. `cat`
10. `chair`
11. `cow`
12. `diningtable`
13. `dog`
14. `horse`
15. `motorbike`
16. `person`
17. `pottedplant`
18. `sheep`
19. `sofa`
20. `train`
21. `tvmonitor`

`net.create_architecture("TEST", 21, tag='default', anchor_scales=[8, 16, 32])` matches that label space.

## Command shapes

Recommended stock command:

```bash
cd /path/to/tf-faster-rcnn && CUDA_VISIBLE_DEVICES=0 python ./tools/demo.py --net res101 --dataset pascal_voc_0712
```

CPU-style preview:

```bash
cd /path/to/tf-faster-rcnn && unset CUDA_VISIBLE_DEVICES && python ./tools/demo.py --net vgg16 --dataset pascal_voc
```

The bundled helper prints the same shape of command without running the demo.

## Output expectations

- The script prints a per-image timing line from `Timer`.
- Each class gets its own plotted figure if detections survive the confidence threshold.
- Boxes are drawn in image coordinates after rescaling from the network input blob.
- The displayed image is converted from OpenCV BGR to RGB before plotting.
- On headless machines, `plt.show()` will need an off-screen backend or a local copy of the script that saves figures instead of displaying them.

## Demo image flow

The demo is hardcoded to these five files under `data/demo/`:

- `000456.jpg`
- `000542.jpg`
- `001150.jpg`
- `001763.jpg`
- `004545.jpg`

If you want to use different images, copy the script locally and replace the `im_names` list or swap the files in `data/demo/`.

## Relationship to `test_net.py`

`tools/test_net.py` uses the same `model.test.im_detect` core, but it loops over a dataset, applies `cfg.TEST.NMS`, and writes `detections.pkl` for evaluation.
Keep that workflow in `training-and-evaluation`; this sub-skill stays on the demo/image path.
