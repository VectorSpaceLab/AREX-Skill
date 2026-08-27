# Inference/evaluation troubleshooting

## Checkpoint and config mismatch

**Symptoms:** `load_state_dict` reports missing/unexpected keys or tensor-size
mismatches; construction fails at the transformer; predictions have a wrong
class vocabulary; AP is implausibly low after a successful non-strict load.

**Checks and recovery:**

1. Pair 4-scale weights with `DINO_4scale.py` and 5-scale weights with
   `DINO_5scale.py`. The configs use four versus five feature levels and have
   different intermediate backbone indices.
2. Match the backbone family (ResNet-50, Swin, or ConvNeXt), query count,
   hidden width, and class count. For COCO, `num_classes=91` preserves COCO
   category IDs; custom training must use `num_classes >= max_obj_id+1`.
3. Confirm the checkpoint is a DINO state dict with a `model` key (or an
   intentionally selected `ema_model` key). The official eval path loads
   `checkpoint['model']`; an optimizer-only file is not an inference checkpoint.
4. Do not solve a structural mismatch with `strict=False` for an evaluation
   claim. Use the data/model setup route for config mutation or conversion.
5. Record the checkpoint epoch/variant. A 12-epoch 4-scale result is not
   interchangeable with a 24/36-epoch or 5-scale model-zoo entry.

The bundled smoke script strips only a leading `module.` prefix and then loads
strictly. This makes an error preferable to a silently invalid image result.

## Missing CUDA extension or imports

**Symptoms:** `ModuleNotFoundError: MultiScaleDeformableAttention`, an
undefined symbol error during import, an operator-not-implemented runtime
error, or failure in `models/dino/ops/test.py`.

**Checks:**

```bash
python -c "import MultiScaleDeformableAttention as m; print(m)"
python -c "import torch, torchvision, timm, pycocotools; print(torch.__version__, torchvision.__version__)"
```

For a panoptic/mask route, additionally check `python -c "import panopticapi"`;
ordinary bbox inference does not require or import that optional package.

The verified environment is `torch 2.5.1+cu121` with
`torchvision 0.20.1+cu121`, and imports the extension plus the listed packages.
If the active shell reports another Torch/CUDA ABI, stop before a long run.
Compilation/install of `models/dino/ops` and dependency repair belongs to
`../data-model-setup/`; do not paper over it by switching to a different
attention implementation. The source visualizer additionally imports
`cv2`, `matplotlib`, and `pycocotools`; the bundled Pillow drawing intentionally
avoids importing that visualizer, but model imports still need the verified DINO dependencies.

## COCO layout and loader failures

The accepted root is:

```text
COCODIR/
├── train2017/
├── val2017/
└── annotations/
    ├── instances_train2017.json
    └── instances_val2017.json
```

`datasets.coco.build` derives these exact paths. `main.py` constructs both train
and validation datasets before entering its eval branch, so a val-only partial
copy can still fail. Check file permissions, annotation JSON readability,
image IDs, and that the root passed to `--coco_path` is `COCODIR`, not
`COCODIR/val2017`. A missing or malformed COCO installation is a setup/data
issue; route it to `../data-model-setup/`.

For test-dev submission, the source uses `test2017` and
`annotations/image_info_test-dev2017.json`; that is a different contract from
COCO val AP.

## Score thresholding and labels

DINO's `PostProcess` first selects the configured top `num_select` flattened
query/class scores after sigmoid. A threshold applied afterward only filters
that selected set. Therefore:

- a high threshold can produce an empty visualization without proving that the
  model emitted no candidates;
- a low threshold can expose many weak candidates without improving AP;
- changing a threshold does not reproduce a different COCO evaluation; and
- use the same threshold, class map, and coordinate conversion when comparing
  custom-image pictures.

Labels are output class/category IDs, not human-readable strings. For COCO,
load the numeric ID map and remember that IDs are sparse (category 12 is absent,
for example); do not use `labels[i]` as an index into an 80-item compact list.
For a custom model, provide a map that matches its training IDs.

## Image normalization and box coordinates

The expected custom-image path is:

1. open and convert to RGB;
2. resize the shorter side to 800 by default, capping the longer side at 1333;
3. convert uint8 RGB to float `[0,1]` CHW;
4. normalize channels with mean `[0.485, 0.456, 0.406]` and standard deviation
   `[0.229, 0.224, 0.225]`; and
5. run the model in eval/no-grad mode.

Do not normalize twice, pass BGR from OpenCV without conversion, or pass raw
uint8 data to the model. The model's raw `pred_boxes` and the notebook-style
smoke output use normalized `cxcywh`. `PostProcess` normally emits absolute
`xyxy` when given `[H,W]`; `[H,W]` is ordered height then width, while the
scaling vector is `[W,H,W,H]`. Passing width/height in the wrong order produces
transposed or shifted boxes.

The notebook's `[1,1]` target size is intentional for a normalized
visualization: it produces normalized `xyxy`, which is converted to normalized
`cxcywh` before drawing against the transformed image. For COCO evaluation,
never use `[1,1]`; use each target's original `[H,W]`.

## Optional visualization dependencies

If the source `util.visualizer.COCOVisualizer` is used directly, it imports
Pillow-adjacent plotting dependencies including OpenCV, Matplotlib, and
`pycocotools`, and it expects all tensors on CPU. It also expects `boxes` in
normalized `cxcywh` plus `size=[H,W]`. Missing one of these dependencies or
passing absolute `xyxy` is a visualization failure, not a model failure.

Prefer the bundled `scripts/inference_smoke.py` for a one-image artifact. It
uses Pillow's `ImageDraw`, writes JSON and optionally PNG, does not import the
original notebook or source visualizer, and keeps numeric labels when no label
map is available. If Pillow is absent, install/repair the runtime in the setup
route rather than adding a hidden dependency or falling back to a browser-only
notebook.

## Benchmark-specific failures

- `tools/benchmark.py` failing at `model.cuda()` or `torch.cuda.synchronize()`
  means the requested CUDA benchmark cannot run; it is not a CPU-compatible
  command.
- A flop warning about skipped operations means the reported GFLOPS is partial.
  Record the warning and do not present it as a complete hardware FLOP count.
- A benchmark that writes no `flops/log.txt` likely has an empty/unwritable
  `--output_dir` or failed before completion. It did not produce a valid timing
  result.
- The tool does not load a checkpoint. Use `main.py --eval` for quality and
  `tools/benchmark.py` only for the bounded architecture measurement.
