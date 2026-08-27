# Inference Demo Workflows

This reference owns the planning flow after a demo script has been selected.
Use it to decide whether a script can run locally, needs a deterministic
fixture, or should hand off to another sub-skill.

## 1) Quick routing

| Situation | First check | If true | Route |
| --- | --- | --- | --- |
| Python demo script with a model default | Run `scripts/classify_runtime_script.py` | Backend and asset clues are visible | Stay here |
| Missing model, label, image, or clip | Check the default path and nearby files | The asset is absent | `../model-acquisition/` |
| Conversion, export, or quantization keywords | Look for converter names, `TFLiteConverter`, `onnxsim`, `coremltools`, `edgetpu_compiler`, or similar | The file is not a demo | `../conversion-and-deployment/` |
| Browser/TFJS sample | Look for `model.json`, shard files, `tfjs`, `browser`, or `webgl` | It is browser-driven, not Python-driven | Keep planning here, but use a browser/static-server plan |
| Live camera or webcam input | Look for `VideoCapture(0)`, `imshow`, `waitKey`, or camera args | CI would be nondeterministic | Replace with a fixed image or pinned clip |
| Edge accelerator or Raspberry Pi clue | Look for `EdgeTPU`, `libedgetpu`, `MYRIAD`, `aarch64`, `armv7l`, or `Raspberry Pi` | Concrete hardware is required | Stop until that runtime exists |

## 2) Recommended planning order

1. Identify the primary inference backend.
2. Identify wrapper/support layers such as OpenCV, MediaPipe, or camera code.
3. Check whether the model file exists locally and whether the script also needs
   labels, anchors, masks, sample images, or sample clips.
4. Check whether the script asks for a display, a camera, GPU, EdgeTPU, or a
   browser runtime.
5. Decide whether the run can be deterministic in CI.
6. If not, hand off instead of forcing a live run.

## 3) Deterministic fixture translation

| Live demo shape | Deterministic substitute | Preserve |
| --- | --- | --- |
| Webcam / `VideoCapture(0)` | A fixed image or a short local clip | Preprocess, thresholds, and postprocess |
| Video file demo | A pinned clip with a known frame count | Frame order and output path |
| Single-image demo | One frozen test image in the model folder | Resize/crop/normalize logic |
| Multi-image demo | A small ordered fixture folder | Sorting and batch logic |
| Browser/TFJS demo | Static server plus screenshot or DOM snapshot | Model load path and canvas output |
| Audio demo | One fixed WAV file | Feature extraction and label mapping |

## 4) Execution preflight

- Confirm the backend family from imports, file extensions, and provider names.
- Confirm the model artifact exists before touching the runtime.
- Confirm any fixture files, labels, and auxiliary data exist.
- Confirm the selected runtime can actually open a camera or display if the
  script requires one.
- Confirm whether the user wants a smoke test, a deterministic fixture plan, or
  a live device run.

## 5) Handoff rules

- Missing artifacts or download steps -> `../model-acquisition/`.
- Format changes, export, or quantization -> `../conversion-and-deployment/`.
- Browser-only samples -> keep the plan here, but do not promise a Python run.
- Hardware-only samples -> stop and ask for the concrete runtime.

## 6) Example command shape

```bash
python scripts/classify_runtime_script.py selected-folder/demo/demo_onnx.py --json
python selected-folder/demo/demo_onnx.py --help
python selected-folder/demo/demo_onnx.py --model selected-folder/model.onnx --image fixture.jpg
```

## 7) Ownership boundary

This sub-skill can explain what to run and what to replace, but it does not
claim native backend verification in Creator. Use a concrete runtime for that.
