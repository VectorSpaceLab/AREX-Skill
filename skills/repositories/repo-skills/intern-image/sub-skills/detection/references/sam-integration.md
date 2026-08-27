# SAM Integration for InternImage Detection

This reference distills source labels `sam/main_zero_shot_instance_seg.py` and `sam/engine.py`. The workflow evaluates instance masks by using an InternImage MMDetection detector to produce boxes and Segment Anything to turn those boxes into masks.

## What the SAM route does

1. Build a detector from a detection config and detector checkpoint.
2. Load a Segment Anything model from `sam_model_registry[--sam_type]` and a SAM checkpoint path.
3. Run the detector on each dataset item from the config's test pipeline.
4. Extract detector boxes in original-image coordinates.
5. Resize/pad the normalized image to SAM's 1024-length image encoder input.
6. Transform detector boxes into SAM coordinates and call `SamPredictor.predict_torch` with box prompts and `multimask_output=False`.
7. Return one mask per detected box, grouped by detector class label, then encode masks in MMDetection result format.
8. Optionally dump pickle output, run dataset evaluation, or save painted results through the source test-style options.

This is not a text-prompt or automatic-mask-generator route. The prompt source is detector bounding boxes.

## Requirements

- A working detection environment for the selected InternImage detector: MMDetection 2.x, `mmcv-full`, `mmdet`, `timm`, the local `mmcv_custom` and `mmdet_custom` registrations, and the local `ops_dcnv3` path.
- A detector config and detector checkpoint that produce usable box predictions and, in the inspected source, expose a mask-capable detector object. COCO Mask R-CNN/Cascade Mask R-CNN configs are safer choices than DINO bbox-only configs.
- A `segment-anything` Python package compatible with the active PyTorch runtime.
- A SAM checkpoint path and `--sam_type` key. Common registry keys are `vit_b`, `vit_l`, and `vit_h`, depending on the installed Segment Anything package.
- A GPU is normally expected. The source moves SAM to the detector model device.
- Dataset files must match the detector config because SAM mode uses the config's test dataloader rather than a single image argument.

## Command construction

Use the detection helper's `sam` mode. It prints a command only.

```bash
python scripts/build_detection_command.py sam \
  --repo-root <INTERNIMAGE_REPO> \
  --config-key coco/mask_rcnn_internimage_t_fpn_1x_coco \
  --checkpoint checkpoints/mask_rcnn_internimage_t_fpn_1x_coco.pth \
  --sam-checkpoint checkpoints/sam_vit_b.pth \
  --sam-type vit_b \
  --eval segm \
  --out sam_results.pkl \
  --show-dir work_dirs/sam_vis
```

The emitted command changes into `<repo-root>/detection`, sets `PYTHONPATH` for both detection and repository-root imports, and calls `../sam/main_zero_shot_instance_seg.py` with the config path relative to the detection tree.

## Source parser arguments

Positional arguments:

- `detector_cfg_path`
- `detector_ckpt_path`
- `sam_ckpt_path`

Important options:

- `--sam_type <key>` selects the Segment Anything registry entry.
- `--data_type val|test` is parsed, but the inspected code does not use it to rewrite `cfg.data`; rely on the config's test split or use careful `--cfg-options` when changing data.
- `--work-dir` writes metric JSON when evaluation runs.
- `--out results.pkl` dumps pickled results and must end in `.pkl` or `.pickle`.
- `--eval segm` is the natural mask metric for COCO-style SAM outputs; do not combine `--eval` with `--format-only`.
- `--show` and `--show-dir` follow MMDetection visualization behavior.
- `--show-score-thr` controls visualization threshold, default `0.3`.
- `--cfg-options` and `--eval-options` are forwarded to the MMDetection config/evaluator.

## Important limitations from source evidence

- Distributed SAM execution is not implemented. The source parser accepts launcher options, but the distributed branch raises `NotImplementedError`. Use single-process SAM mode unless the code is intentionally extended.
- The inspected SAM path checks `model.module.with_mask` before converting detector boxes to SAM masks. Bbox-only DINO configs are therefore risky without source changes, even though DINO boxes would conceptually be useful prompts.
- The detector's own mask head is still calculated in the observed source path before SAM masks are substituted; comments warn that FPS/FLOPs may not reflect a pure box-detector plus SAM path.
- The source may print conspicuous debug marker lines before/after initialization. Treat them as source noise unless followed by a real traceback.
- Old PyTorch versions may not accept `antialias=True` in interpolation; the inspected engine catches that `TypeError` and retries without antialias.
- SAM checkpoint/model-type mismatches usually fail at SAM load time or when loading weights. Keep `--sam-type` and the checkpoint family aligned.

## When to avoid this route

- The user only has a single image and wants ordinary detector visualization: use `image-demo`, not SAM.
- The user selected a DINO/CB-DINO bbox-only config and does not want to modify source code: use ordinary `test --eval bbox` or choose a Mask R-CNN/Cascade Mask R-CNN config for SAM.
- The user asks for TensorRT, ONNX, mmdeploy, or SAM acceleration/export: route to deployment or a separate SAM deployment plan.
- The user lacks the dataset and detector checkpoint: build a dry-run command but do not claim SAM evaluation is runnable.
