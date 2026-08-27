# Demo workflows

Use these workflows to run DAMO-YOLO inference without relying on repo-local `tools/` paths. The bundled helper adapts the demo behavior into a self-contained script that imports the installed `damo` package and accepts explicit config, engine, media, and output paths.

## Bundled helper

From the generated DAMO-YOLO skill root, the script path is `sub-skills/inference/scripts/damo_yolo_safe_demo.py`. If invoking from another working directory, replace that relative path with the resolved path to this bundled script.

Why use it:

- Engine extension is validated before loading heavy runtimes.
- `--save_result False` is handled as a real boolean; `--no-save-result` is also available.
- GUI display is disabled unless `--show-window` is explicit, so headless jobs do not hang on `cv2.imshow`.
- Video/camera runs support `--max-frames` for short smoke tests.
- Error messages call out missing optional ONNX/TensorRT dependencies and invalid media paths.

Run a parser/dependency preflight without loading a model:

```bash
python sub-skills/inference/scripts/damo_yolo_safe_demo.py image \
  -f /path/to/damoyolo_config.py \
  --engine /path/to/damoyolo_checkpoint.pth \
  --path /path/to/example.jpg \
  --infer-size 640 640 --check-only
```

`--check-only` validates paths, extension-to-engine selection, and import availability for the selected engine. It does not read checkpoint weights, create a TensorRT context, open video capture, or perform inference.

## Image workflow

Use image inference for single examples, visual sanity checks, or class-name verification.

```bash
python sub-skills/inference/scripts/damo_yolo_safe_demo.py image \
  -f /path/to/damoyolo_config.py \
  --engine /path/to/damoyolo_checkpoint.pth \
  --path /path/to/example.jpg \
  --infer-size 640 640 \
  --device cuda \
  --conf 0.6 \
  --output-dir demo
```

Expected observations:

- The command reports `Inference with torch engine` for `.pth`/`.pt` engines.
- A visualization image is written to `demo/<input-basename>` unless saving is disabled.
- If CUDA was requested but unavailable, Torch uses CPU; verify device logs or run a separate `torch.cuda.is_available()` probe before claiming GPU inference.

For a no-save interactive preview:

```bash
python sub-skills/inference/scripts/damo_yolo_safe_demo.py image \
  -f /path/to/damoyolo_config.py \
  --engine /path/to/damoyolo_checkpoint.pth \
  --path /path/to/example.jpg \
  --infer-size 640 640 --no-save-result --show-window
```

Avoid `--show-window` in headless CI, SSH, or notebook kernels without display support.

## Video workflow

Use video inference when the input is a media file. ONNX is often used for portable video demos, but Torch and TensorRT follow the same command shape.

```bash
python sub-skills/inference/scripts/damo_yolo_safe_demo.py video \
  -f /path/to/damoyolo_config.py \
  --engine /path/to/damoyolo.onnx \
  --path /path/to/input.mp4 \
  --infer-size 640 640 \
  --device cuda \
  --conf 0.6 \
  --output-dir demo
```

Short smoke test on the first 5 frames:

```bash
python sub-skills/inference/scripts/damo_yolo_safe_demo.py video \
  -f /path/to/damoyolo_config.py \
  --engine /path/to/damoyolo.onnx \
  --path /path/to/input.mp4 \
  --infer-size 640 640 --max-frames 5 --output-dir demo
```

Expected observations:

- The output video is written under `--output-dir` using the input basename unless `--output-name` is set.
- If `cv2.VideoCapture` cannot open the file, check the path, codec support, and OpenCV installation.
- If FPS is unavailable from the source file, use `--fps` to choose a writer FPS.

## Camera workflow

Use camera inference only on machines where OpenCV can access the camera id.

```bash
python sub-skills/inference/scripts/damo_yolo_safe_demo.py camera \
  -f /path/to/damoyolo_config.py \
  --engine /path/to/damoyolo_end2end_fp16_bs1.trt \
  --camid 0 \
  --infer-size 640 640 \
  --device cuda \
  --conf 0.6 \
  --end2end \
  --max-frames 200 \
  --output-dir demo
```

Expected observations:

- TensorRT camera inference requires the optional TensorRT stack. Torch CUDA working is not enough.
- `--end2end` must match the exported `.trt` engine. Use it only for TensorRT engines exported with NMS included.
- Camera output defaults to `camera_<camid>.mp4` under `--output-dir` when saving is enabled.

## Option reference

| Option | Meaning | Gotchas |
| --- | --- | --- |
| `input_type` | One of `image`, `video`, `camera` | Image/video need `--path`; camera uses `--camid` |
| `-f`, `--config-file` | DAMO-YOLO config used to build/interpret the model | Must match checkpoint/export architecture and class count |
| `--engine` | Engine artifact path | Extension selects runtime: `.pth`/`.pt`, `.onnx`, `.trt` |
| `--device` | `cuda` or `cpu` request | Torch can fall back to CPU; TensorRT cannot; ONNX provider selection is separate |
| `--infer-size H W` | Resize/pad target | Match model family/export; ONNX may use exported input shape |
| `--conf` | Visualization score threshold | Does not change config NMS thresholds |
| `--end2end` | TensorRT engine includes NMS | Wrong setting causes output-shape/index errors or bad boxes |
| `--save-result` / `--save_result` | Save visualization outputs | Enabled by default; source-style `--save_result False` is brittle, but the bundled helper parses it correctly |
| `--no-save-result --show-window` | Display without saving | Unsafe for headless runs unless a GUI display exists |
| `--max-frames` | Stop video/camera after N frames | Use for smoke tests and CI-sized checks |

## Minimal Python API pattern

If you need to integrate a one-off Python script instead of a CLI command, import the bundled helper class and keep file paths explicit:

```python
from pathlib import Path
from damo.config.base import parse_config
from damo_yolo_safe_demo import SafeDAMOInfer, load_runtime_modules

load_runtime_modules("torch")
config = parse_config("/path/to/damoyolo_config.py")
infer = SafeDAMOInfer(
    config=config,
    infer_size=[640, 640],
    device="cuda",
    output_dir=Path("demo"),
    engine_path=Path("weights/damoyolo_tinynasL25_S.pth"),
    end2end=False,
)
```

Keep this pattern inside the same directory as the bundled helper or add that script directory to `PYTHONPATH`; do not import from repo-local demo scripts for generated-skill workflows.
