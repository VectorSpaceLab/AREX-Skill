# Demo workflows

The source demo supports image lists/globs, webcam, and video input. The skill-owned wrapper validates arguments and adds `MODEL.WEIGHTS` through config overrides.

## Image demo

```bash
python scripts/run_demo.py --repo-root /path/to/AdelaiDet \
  --config configs/FCOS-Detection/R_50_1x.yaml \
  --weights /path/to/model.pth \
  --input image1.jpg image2.jpg \
  --output output/demo-images \
  --confidence-threshold 0.5
```

`--input` accepts one or more paths. The source script also accepts glob-style patterns; use shell quoting if needed.

## Video demo

```bash
python scripts/run_demo.py --repo-root /path/to/AdelaiDet \
  --config configs/CondInst/MS_R_50_1x.yaml \
  --weights /path/to/model.pth \
  --video-input input.mp4 \
  --output output/condinst.mp4 \
  --confidence-threshold 0.4
```

Video output depends on OpenCV codec support. On codec failures, write image frames or install the required codec-enabled OpenCV/ffmpeg stack.

## Webcam demo

```bash
python scripts/run_demo.py --repo-root /path/to/AdelaiDet \
  --config configs/FCOS-Detection/R_50_1x.yaml \
  --weights /path/to/model.pth --webcam
```

Use webcam mode only on an interactive machine with a camera and display. It is not appropriate for headless CI/servers.

## Additional config options

Pass Detectron2 config overrides after `--opts`:

```bash
python scripts/run_demo.py --repo-root /path/to/AdelaiDet \
  --config configs/BlendMask/R_50_1x.yaml \
  --weights /path/to/model.pth --input sample.jpg --output out/ \
  --opts MODEL.DEVICE cuda INPUT.MIN_SIZE_TEST 800
```

The wrapper appends `MODEL.WEIGHTS <weights>` automatically, then any `--opts` pairs.

## Common checks

- Config and weights must match the model family.
- `MODEL.DEVICE` should be `cuda` for CUDA-only or very slow workflows.
- Output directory must be writable.
- For text models, recognized strings may depend on `MODEL.BATEXT.CUSTOM_DICT` and evaluation lexicons; route semantics to `text-spotting`.
