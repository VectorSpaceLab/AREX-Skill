# Models And Deployment Troubleshooting

Start with the bundled probes:

```bash
python scripts/optional_dependency_probe.py --device auto
python scripts/model_runtime_probe.py --device auto
```

The probes are no-download and do not call pretrained loaders by default.

## Optional dependency errors

| Symptom | Likely cause | Fix |
|---|---|---|
| `Optional dependency 'onnx' is not installed` | ONNX graph export/load was requested without `onnx`. | Install ONNX only if export/load is required, or stay on the PyTorch path. |
| `PIL`/`Pillow` missing | A visualization path requested `output_type="pil"` or image conversion to PIL. | Install Pillow only if rendered previews are required; otherwise keep `output_type="torch"`. |
| `Optional dependency 'onnxruntime' is not installed` | `ONNXModule` or `ONNXSequential` construction needs ONNX Runtime. | Install CPU or GPU ONNX Runtime matching the provider you need; CPU-only ORT cannot run CUDA provider requests. |
| `requests` missing | Remote ONNX catalog listing or Hugging Face ONNX-community config fetches need `requests`. | Stay on local files and cached graphs, or install `requests` only when online loading/listing is required. |
| ONNX export asks for `onnxscript` | A PyTorch ONNX export path requires the ONNX script dependency. | Install the ONNX export stack intentionally or avoid ONNX export in the current environment. |
| `Optional dependency 'ivy' is not installed` | `to_numpy`, `to_jax`, or `to_tensorflow` attempted lazy Ivy transpilation. | Install Ivy and the target framework only when that deployment path is required. |
| `huggingface_hub` or `safetensors` missing | HF pretrained builders such as Kimi-VL or SigLip2 need those packages to fetch safetensors weights. | Use config-only construction for no-download checks or install the HF dependencies before loading weights. |
| `segmentation_models_pytorch`, `basicsr`, `boxmot`, `diffusers`, or `transformers` missing | A specialized optional application/model path was imported or constructed. | Install only the feature-specific extra or route the task to the sub-skill that owns that feature. |

If the lazy loader prompts to install packages, stop and confirm the environment
policy. In controlled/offline runtimes, prefer raising a clear missing-dependency
error over interactive or automatic installation.

## Pretrained weights, cache, and network problems

| Symptom | Likely cause | Fix |
|---|---|---|
| A no-download smoke unexpectedly accesses the network | A default builder used `pretrained=True` or a remote checkpoint/`hf://` path. | Pass `pretrained=False`, use config-only paths, or provide a local/cached checkpoint explicitly. |
| `FaceDetector()` downloads at construction | High-level face detector wraps pretrained YuNet by default. | For offline shape checks, use `YuNet("test", pretrained=False)` instead. |
| `VisualPrompter()` downloads SAM-H | The no-argument prompter defaults to a pretrained SAM-H config. | Pass `VisualPrompter(SamConfig("vit_b"))` or another explicit non-pretrained config. |
| `RTDETRDetectorBuilder.build()` downloads | No model/config was passed, or `pretrained=True` with a model name was used. | Pass an explicit `model_name` plus `pretrained=False`, or pass an `RTDETRConfig` with no checkpoint. |
| `EfficientViT.from_config(...)` downloads | The config contains a remote checkpoint URL. | Use `efficientvit_backbone_b0/b1/...` for no-download feature smokes, or provide a local checkpoint. |
| TinyViT or ViT pretrained call is slow/fails | `pretrained=True` loads remote weights. | Use `pretrained=False` for API checks; approve/cache weights before correctness or quality checks. |

## Device and dtype mismatches

- Keep images, prompts, boxes, masks, model parameters, and post-processors on the
  same device.
- Use `float32` for first-pass model debug. Treat `float16`, `bfloat16`, MPS, and
  CUDA-specific behavior as optional backend claims that require verification.
- If a wrapper mixes CPU postprocessing with GPU tensors, move the wrapper and
  inputs consistently with `.to(device, dtype)` where supported.
- If an ONNX or NumPy path needs CPU arrays, explicitly detach and move tensors
  with `tensor.detach().cpu().numpy()` rather than relying on `output_type`.

## Shape and data-range errors

| Symptom | Likely cause | Fix |
|---|---|---|
| SAM shape error | `Sam.forward` requires `B,3,H,W` and `len(batched_prompts) == B`. | Pad/resize/normalize through `VisualPrompter` or provide the preprocessed tensor and one prompt dict per image. |
| `predict` called before setting image | `VisualPrompter` requires cached image embeddings. | Call `prompter.set_image(image)` before `prompter.predict(...)`. |
| SAM prompt error | Point labels/points, boxes, or mask prompts have inconsistent shapes. | Points are `K,N,2` plus labels `K,N`; boxes are xyxy; masks are `K,1,256,256`. |
| YuNet tiny input fails | The raw model has pooling stages that collapse very small spatial sizes. | Use at least a modest size such as `64x64` for raw no-download probes; use realistic sizes for meaningful detection. |
| `FaceDetectorResult` raises on data length | The result record expects the high-level detector's `15` values. | Wrap only `N,15` detector rows, not raw YuNet `loc/conf/iou` outputs. |
| ViT bad attention shape | Embedding dimension is not divisible by number of heads. | Choose compatible `embed_dim` and `num_heads`. |
| MobileViT reshape error | Intermediate feature sizes are not divisible by the patch size. | Use image sizes compatible with the model's downsampling and `patch_size`. |

Kornia application wrappers generally expect RGB float image tensors in `[0,1]`.
If your source data is BGR or uint8-like, convert and scale before model use.

## Output conversion and save errors

- `output_type="numpy"` is not supported by the shared model mixin. Use
  `output_type="torch"` then convert explicitly.
- `output_type="pil"` is for rendered images; it is not suitable for raw logits,
  dictionaries, or arbitrary detection records.
- `save()` creates directories and writes image files. Make sure tensors are
  image-like, finite, and in a sensible display range.
- If a wrapper returns a list, check each element's shape rather than assuming a
  single batched tensor.

## ONNX export and runtime errors

| Symptom | Likely cause | Fix |
|---|---|---|
| Export succeeds but output names are wrong | Generic exporter was used for a multi-output model. | Use the model-specific `to_onnx` helper; RT-DETR sets `pred_logits` and `pred_boxes`. |
| SAM full model export fails | Full SAM forward includes Python prompt dictionaries and returns dataclasses/lists. | Export `Sam.to_onnx()` image encoder only, then handle prompts/masks separately. |
| `io_maps` merge failure | Adjacent ONNX graph input/output names do not match after prefixing. | Inspect graph input/output names and pass one mapping per adjacent boundary. |
| Provider not available | Requested CUDA/TensorRT/OpenVINO provider is not installed in ORT. | Run with `CPUExecutionProvider` or install the matching provider package. |
| IR/opset incompatibility | Chained graphs use versions unsupported by the installed ORT. | Try `auto_ir_version_conversion=True` or explicitly target a supported IR/opset. |
| Custom session options fail | The ORT version or wrapper path does not accept the requested options. | First run with default session options; if needed, create and test a session manually, then set it on the wrapper. |
| Resize/postprocess differs after export | Some postprocessors are not fully supported during ONNX export. | Export model-only and reproduce pre/postprocessing in the deployment application, or verify the wrapper graph end to end. |

## Ivy transpilation limits

- Missing `ivy` means `to_numpy`, `to_jax`, and `to_tensorflow` are unavailable.
- The first call can be much slower because conversion is lazy.
- NumPy transpilation does not support trainable modules.
- JAX `jit` and TensorFlow `tf.function` compatibility is limited for transpiled
  paths. Probe a small function before using a full model.
- Custom kernels and stateful training objects are not good transpilation
  candidates.

## Development/doc update failures

If a new public model or deployment helper is added but missing from generated
API documentation, add it to the corresponding Sphinx model/application page and
include a minimal example. If the public symbol has pretrained behavior, the
example must make no-download versus download behavior explicit.
