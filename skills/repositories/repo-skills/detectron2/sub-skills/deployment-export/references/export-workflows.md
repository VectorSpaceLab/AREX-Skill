# Export Workflows

Detectron2 deployment converts Python models into artifacts that another runtime can load. The two terms that matter most are:

- Export method: how the model is serialized, such as `tracing`, `scripting`, or `caffe2_tracing`.
- Format: the artifact representation, such as `torchscript`, `caffe2`, or `onnx`.

## Method and Format Matrix

| Export method | Formats | Runtime intent | Batch behavior | Dynamic resolution | Typical fit |
|---|---|---|---|---|---|
| `tracing` | `torchscript`, `onnx` | PyTorch/TorchScript; ONNX only for advanced users | Batch size fixed to trace sample | Supported | First choice for Mask R-CNN, Faster R-CNN, Keypoint R-CNN, RetinaNet, PointRend, and Cascade R-CNN when sample inputs are representative |
| `scripting` | `torchscript` only | PyTorch/TorchScript | Dynamic batch can work | Supported | Use when dynamic batch matters and the official model family is scriptable |
| `caffe2_tracing` | `caffe2`, `torchscript`, `onnx` | Caffe2/PyTorch deployment experiments | Batch inference unsupported | Supported | Optional/deprecated path for built-in meta-architectures when Caffe2 support is present |

The safest default is TorchScript. `caffe2_tracing` is dependency-sensitive and expected to be deprecated. ONNX exports from Detectron2 can contain custom or Caffe2-oriented operators and are not guaranteed to run directly in ONNX Runtime or TensorRT without additional transformations.

## Official Model Coverage

- `GeneralizedRCNN` and `RetinaNet` official models are broadly covered by tracing and scripting.
- Mask/Faster/Keypoint R-CNN and RetinaNet are supported by tracing and scripting for common official configs.
- PointRend R-CNN and Cascade R-CNN are tracing-oriented; do not choose scripting as the default for these families.
- `caffe2_tracing` historically covers common `GeneralizedRCNN`, `RetinaNet`, and `PanopticFPN` architectures, but not Cascade R-CNN and not arbitrary custom control flow or unsupported Caffe2 ops.
- Custom extensions are exportable only if their modules and operators are traceable/scriptable or Caffe2-compatible for the chosen method.

## Command Shape

Use the bundled command builder to preview a command without running export:

```bash
python sub-skills/deployment-export/scripts/export_command_builder.py \
  --config-file CONFIG.yaml \
  --output OUTPUT_DIR \
  --export-method tracing \
  --format torchscript \
  --sample-image SAMPLE.jpg \
  --override MODEL.WEIGHTS=WEIGHTS.pkl \
  --override MODEL.DEVICE=cpu
```

The generated command follows this shape:

```bash
python EXPORT_DRIVER.py --config-file CONFIG.yaml --output OUTPUT_DIR --export-method tracing --format torchscript --sample-image SAMPLE.jpg MODEL.WEIGHTS WEIGHTS.pkl MODEL.DEVICE cpu
```

`EXPORT_DRIVER.py` is a placeholder for the caller's local export driver. The helper does not require the original checkout, never imports Detectron2, and never starts export. If no local export driver exists, write a small driver from the API patterns below instead of relying on source-repository scripts.

## TorchScript Tracing API Pattern

Tracing is useful when model inputs/outputs include Detectron2 structures that normal `torch.jit.trace` cannot handle directly. `TracingAdapter(model, inputs, inference_func=None, allow_non_tensor=False)` flattens rich inputs/outputs into tensors and records schemas.

Typical steps:

1. Build and load the model with the already-selected config and weights.
2. Put the model in eval mode.
3. Prepare representative sample inputs: usually `[{"image": tensor_chw, "height": original_h, "width": original_w}]` or a dataset batch.
4. Define an `inference_func` when the default `model(*inputs)` is not the desired export path.
5. Construct `TracingAdapter(model, inputs, inference_func)`.
6. Run `torch.jit.trace(adapter, adapter.flattened_inputs)`.
7. Save the traced module and call `dump_torchscript_IR(traced_model, output_dir)` for debugging artifacts.
8. Use `adapter.outputs_schema(traced_outputs)` when Python-side validation needs to rebuild rich outputs.

For a standard R-CNN export, use `model.inference(inputs, do_postprocess=False)` during tracing when deployment does not need Detectron2's final resize/post-processing step inside the artifact.

## TorchScript Scripting API Pattern

`scripting_with_instances(model, fields)` scripts models that use Detectron2 `Instances` by temporarily replacing dynamic `Instances` with a statically typed class. It only supports evaluation-mode models.

The `fields` dictionary must list every `Instances` field used by the model, not just fields returned to the caller. Common fields include:

- Proposal fields: `proposal_boxes`, `objectness_logits`.
- Detection fields: `pred_boxes`, `scores`, `pred_classes`.
- Mask/keypoint fields when relevant: `pred_masks`, `pred_keypoints`, `pred_keypoint_heatmaps`.

Use `Boxes` for box-valued fields and `torch.Tensor` or `Tensor` for tensor-valued fields. Missing or wrong field types are a common cause of scripting failures.

## IR Dumping

`dump_torchscript_IR(model, dir)` writes human-readable TorchScript debugging files, including code, graph, inlined graph, and model structure when available. Use it after tracing or scripting to inspect hard-coded devices, unexpected control flow, or missing output paths.

## Caffe2 Tracing Pattern

`Caffe2Tracer(cfg, model, inputs)` builds a Caffe2-compatible version of supported Detectron2 models and exposes:

- `export_caffe2()`: returns a `Caffe2Model` that can save protobuf files such as `model.pb`, `model_init.pb`, and `model.pbtxt`.
- `export_onnx()`: returns an ONNX model from the Caffe2-compatible graph; it may contain custom/Caffe2 ops.
- `export_torchscript()`: returns a traced TorchScript module of the Caffe2-compatible model.

Caffe2 tracing expects input tensors in a different deployment format internally: image data plus `im_info`. The wrapper can mimic Detectron2-style inputs in Python, but raw exported Caffe2 artifacts often expose raw layer outputs and do not include full application post-processing.

## Method Selection Examples

### Mask R-CNN on CPU

For a CPU-first Mask R-CNN deployment artifact, choose `tracing` + `torchscript` first. Provide a representative sample image and set the config device to CPU. This avoids optional Caffe2 dependencies and produces a PyTorch-loadable artifact. If dynamic batch is a hard requirement, evaluate `scripting` + `torchscript` next; include mask fields in the `Instances` field map.

### PointRend Scripting Failure

If a PointRend model fails with `--export-method scripting`, switch to `--export-method tracing --format torchscript`. PointRend is tracing-oriented in Detectron2 deployment coverage; scripting is not the supported default.

### ONNX Request

For ONNX, first confirm the caller accepts optional dependencies and possible runtime gaps. A traced ONNX export may be useful for graph inspection or custom conversion work, but direct ONNX Runtime execution is not guaranteed. If the request requires production ONNX Runtime/TensorRT support, treat it as an integration project rather than a one-command export.
