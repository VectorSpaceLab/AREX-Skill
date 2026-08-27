# Single-model deployment workflow

The commands below assume the generated skill root is the current working directory.

This is the path for one detector in one DeepStream app.

## 1. Confirm the model family

- Use `references/model-family-matrix.md` to match the checkpoint or ONNX file to the right config template.
- If the model is still a checkpoint, route to `model-conversion` first.
- If the model is Darknet-style, keep the `.cfg` and `.weights` pair together.
- If the model is already ONNX, start from the family-specific `config_infer_primary*.txt` template.

## 2. Probe the host

Run `sub-skills/deployment/scripts/check-deepstream-toolchain.sh` and confirm:

- `CUDA_VER` is known.
- `deepstream-app` is installed.
- `nvcc` and the DeepStream build path are present.
- `pkg-config` can see the optional OpenCV dev package when INT8 calibration is planned.

## 3. Build the custom library

Use the build wrapper once the host is ready:

```bash
CUDA_VER=12.8 sub-skills/deployment/scripts/build-nvdsinfer-plugin.sh --output-dir ./deepstream-yolo-runtime
```

If you only need to inspect or edit the packaged runtime tree before a DeepStream host is available, run:

```bash
sub-skills/deployment/scripts/build-nvdsinfer-plugin.sh --stage-only --output-dir ./deepstream-yolo-runtime
```

Set `OPENCV=1` only when you are intentionally enabling the calibration build path.

## 4. Edit the deployment config

Update the family-specific `config_infer_primary*.txt` file:

- `onnx-file` for ONNX models, or `custom-network-config` + `model-file` for Darknet.
- `model-engine-file` so the engine cache matches the model, batch size, and precision.
- `num-detected-classes` so the labels and parser match the checkpoint.
- `parse-bbox-func-name` and `engine-create-func-name` according to the family.
- `maintain-aspect-ratio`, `symmetric-padding`, `model-color-format`, and `cluster-mode` according to the matrix.

Then point `deepstream_app_config.txt` at the chosen infer config inside `./deepstream-yolo-runtime`.

## 5. Run the app

Launch the sample app once the model, labels, and engine cache are in place:

```bash
deepstream-app -c deepstream_app_config.txt
```

## 6. Debug by symptom

- No `deepstream-app`: install the SDK or use a DeepStream container.
- Wrong boxes or class count: compare the template against the model-family matrix.
- Engine rebuilds every time: check `model-engine-file` and the batch / precision settings.
- GLib or GStreamer runtime error: use the troubleshooting reference.

## Notes

- Keep deployment guidance separate from exporter guidance.
- Keep multi-detector layouts in `multi-gie`.
- Keep INT8 calibration in `int8-benchmarking`.