# Inference and export workflows

## Inference flow

1. Load the config.
2. Load the checkpoint.
3. Build the model and move it to the selected device.
4. Run preprocessing with `cfg.data.val.pipeline` and `cfg.data.val.input_size`.
5. Decode detections with the head's post-process or result rendering helper.

### Demo modes

| Mode | What it does |
| --- | --- |
| `image` | Runs inference on one image or every image in a folder |
| `video` | Iterates through a video file frame by frame |
| `webcam` | Captures frames from a webcam / camera index |

### Demo outputs

- Optional result images are written under the configured `save_dir`.
- The skill-owned wrapper exposes the device explicitly so CPU-only users are not forced into `cuda:0`.
- Use `--show` only when you want an interactive OpenCV window.

## Export flow

### ONNX export

1. Load the config.
2. Pick the export input shape from the config or pass one explicitly.
3. Load the checkpoint.
4. Convert `RepVGG` models to deploy form if needed.
5. Export and optionally simplify the graph.

### TorchScript export

1. Load the config.
2. Load the checkpoint.
3. Convert `RepVGG` models to deploy form if needed.
4. Trace the model with a dummy input of the requested shape.
5. Save the traced module.

## FLOPs helper

- The FLOPs helper uses `mobile_cv` if available.
- When the optional dependency is absent, the helper should print a skip message instead of failing the whole skill.

## Practical command pattern

```bash
python sub-skills/inference-export/scripts/demo.py image --config path/to/config.yml --model path/to/model.ckpt --path path/to/image.jpg --device cpu
python sub-skills/inference-export/scripts/export_onnx.py --cfg_path path/to/config.yml --model_path path/to/model.ckpt --out_path nanodet.onnx
python sub-skills/inference-export/scripts/export_torchscript.py --cfg_path path/to/config.yml --model_path path/to/model.ckpt --out_path nanodet.torchscript.pth
python sub-skills/inference-export/scripts/flops.py path/to/config.yml
```

## Notes

- The heads contain ONNX-aware forward branches for export.
- `RepVGG` requires deploy conversion before export or backend conversion.
- Keep `input_shape` aligned with the model config when exporting.
- Deployment backends such as ncnn, MNN, OpenVINO, and LibTorch are documented in the next reference.
