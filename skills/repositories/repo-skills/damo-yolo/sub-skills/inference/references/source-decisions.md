# Source script and helper decisions

This sub-skill distills the repository's inference path into bundled runtime guidance. The goal is to keep the future agent self-contained without depending on the original checkout.

## File decisions

| Source file or section | Decision | Reason |
| --- | --- | --- |
| `tools/demo.py` | **Adapt** into `scripts/damo_yolo_safe_demo.py` | It contains the full image/video/camera demo flow, engine dispatch, preprocessing, postprocessing, and visualization. A bundled helper is useful, but the original script is path-sensitive and its `--save_result` handling is brittle. |
| `damo/apis/detector_inference.py` | **Reference-only** | It is a dataset/evaluation inference loop, not the demo CLI. It belongs with evaluation or training workflows rather than this user-facing media demo route. |
| `damo/utils/demo_utils.py` | **Reference and reuse** | The sub-skill relies on `transform_img`, `postprocess`, and the NMS helpers for Torch/ONNX/TensorRT postprocessing behavior. |
| `damo/utils/visualize.py` | **Reference and reuse** | It defines the demo drawing behavior and class-name formatting. |
| `damo/utils/boxes.py` | **Reference and reuse** | It provides `postprocess(...)` and the NMS path used by Torch/ONNX and non-end2end TensorRT. |
| `damo/structures/bounding_box.py` and `damo/structures/image_list.py` | **Reference and reuse** | They define `BoxList` and `ImageList`, which are the demo output and preprocessing container types. |
| README demo/deploy sections | **Reference** | They provide the only documented CLI examples for the demo and explain Torch/ONNX/TensorRT engine choices. |
| ONNX export / TensorRT export internals | **Exclude** | Export and engine-building internals belong to deployment, not demo inference. |
| Evaluation loops and distributed inference helpers | **Exclude** | They are useful for evaluation tasks but not for image/video/camera demos. |

## Bundled helper scope

The bundled helper keeps the source demo flow but adds safer defaults and clearer errors:

- explicit engine-extension validation;
- optional dependency checks for ONNX Runtime and TensorRT/CUDA Python;
- a real boolean parser for `--save_result` plus `--no-save-result`;
- `--check-only` for preflight validation;
- `--max-frames` for short video/camera smoke tests;
- explicit media path validation and clearer output-path handling.
