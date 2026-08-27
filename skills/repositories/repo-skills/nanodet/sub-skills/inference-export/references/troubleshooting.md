# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Demo defaults to CUDA on a CPU-only machine | the original demo hard-codes `cuda:0` | use the skill-owned wrapper with an explicit device |
| `onnxsim` / `onnxruntime` import or simplify failure | export dependencies missing or incompatible | install the ONNX export stack and retry |
| ONNX export produces a bad graph | model was not prepared for export | make sure the model family supports the ONNX path and convert RepVGG first |
| TorchScript trace mismatch | input shape or branch behavior differs from the config | trace with the correct input shape and a compatible model config |
| FLOPs helper skips execution | `mobile_cv` is absent | treat FLOPs as optional and keep the skip message |
| webcam / video capture fails | missing camera, bad path, or OpenCV backend issue | verify the path, camera index, and `cv2` installation |
| first build downloads pretrained weights | a backbone config defaults to `pretrained=True` | cache the weights or disable pretrained loading when offline |

## Recovery pattern

1. Validate the config in `dataset-config`.
2. Confirm the checkpoint matches the selected model family.
3. For RepVGG, convert to deploy form before export.
4. Re-run the exporter or demo with a CPU-friendly device if needed.
