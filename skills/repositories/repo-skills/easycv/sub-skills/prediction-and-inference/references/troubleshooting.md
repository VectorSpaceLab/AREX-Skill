# Prediction and inference troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `please install easy_predict first` | Batch prediction extra is missing | Install `easy_predict` before using `python -m easycv.tools.predict`. |
| `model_type` mismatch or missing config sidecar | The artifact type does not match the predictor | Use the matching predictor class and keep exported sidecar files together. |
| Readable class names are wrong or missing | `label_map_path`, `CLASSES`, or `class_list` is not aligned with the artifact | Provide the right label map or config and re-export if needed. |
| Input colors look wrong | The predictor expects `RGB` but the data is `BGR`, or vice versa | Match the `mode` setting and the caller's image conversion. |
| `output_file` or table output is empty | The process pipeline failed before formatting results | Check the input list, image column, and model path first. |
| `use_trt_efficientnms` is unavailable | The export or runtime environment lacks the Blade / TensorRT helper | Drop the feature or install the extra export dependencies. |
| OCR or pose predictions are malformed | The detector / recognizer / keypoint config pair does not match | Re-check the nested predictor config and the expected stage order. |
| ONNX inference does not load | ONNX extras or sidecar config files are missing | Install `onnxruntime` and verify the exported config file layout. |

## Quick checks

- Confirm the predictor class name against the model artifact suffix.
- Confirm the config file or exported sidecar file exists next to the model.
- Confirm the image mode and input type before trying a larger batch.
- Confirm `easy_predict` is installed before batch-file or table mode.

