# Cross-cutting troubleshooting

Read this reference when a demo fails before its own workflow-specific guide
identifies the cause.

## Classify the first failure

1. **Import failure:** record the missing module and Python/TensorRT version.
   `pycuda`, `tensorrt`, `onnx`, `uff`, `graphsurgeon`, `tensorflow`,
   `pycocotools`, and `progressbar2` belong to different workflow variants;
   install only the selected isolated variant.
2. **CUDA context failure:** check `nvidia-smi`, driver visibility, selected
   device free memory, and `CUDA_VISIBLE_DEVICES`. A `cuCtxCreate failed: out of
   memory` error is a host allocation problem, not a parser or model result.
3. **Plugin/ABI failure:** errors about `libyolo_layer.so`,
   `YoloLayer_TRT`, `FlattenConcat_TRT`, or plugin creators mean the plugin was
   not built, cannot be loaded, targets the wrong compute capability, or does
   not match the TensorRT ABI. Rebuild on the target; do not reuse a copied `.so`.
4. **Engine failure:** deserialize with the same TensorRT major/minor family,
   CUDA/runtime, GPU architecture, and plugin set used for building. A file's
   existence or size is not validity.
5. **Input failure:** validate one mutually exclusive input mode, then check
   file readability, OpenCV/GStreamer decoder availability, dimensions, and
   headless display constraints. Use `--copy_frame` when overlays mutate a live
   frame that may be reused by inference.
6. **Evaluation failure:** validate COCO image IDs, annotation category IDs,
   result `bbox`/score fields, class mapping, and model/letterbox mode before a
   long run. Preserve full logs and do not compare tiny fixtures with published
   mAP.

## Version boundary

The source snapshot is historical. TensorRT 5+ is required by the UFF SSD
Python path, TensorRT 6+ by the YOLO plugin, TensorRT 7+ by DLA-era YOLO and
MODNet, and TensorRT 7.1/7.2 have a documented MODNet InstanceNormalization
split. Current TensorRT APIs can remove implicit-batch, Caffe, UFF, or legacy
`destroy()` behavior. Stop at the compatibility gate rather than silently
modernizing source calls and claiming equivalence.

## Safe recovery

Keep the original error, source commit, target versions, GPU/compute
capability, command, working directory, and artifact hashes. Use the nearest
bundled validator, then a help-only or tiny-fixture check. Do not repair a
user-owned environment or overwrite an engine without approval. If the required
GPU/backend is unavailable, mark the workflow blocked; CPU importability is not
a substitute for TensorRT execution when the workflow's CPU substitute is none.
