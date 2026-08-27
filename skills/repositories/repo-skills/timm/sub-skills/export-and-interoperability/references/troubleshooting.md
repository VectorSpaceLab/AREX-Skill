# Export and Interoperability Troubleshooting

Use this reference when ONNX export, ONNX Runtime validation, Hugging Face/local-dir loading, Torch Hub, checkpoint cleaning, checkpoint averaging, or conversion workflows fail.

## ONNX Problems

| Symptom | Likely cause | Response |
| --- | --- | --- |
| `ModuleNotFoundError: onnx` or `onnxruntime` | Optional export/validation dependency missing | Install the missing package in the working environment or provide a command-only answer. |
| Export fails on an operator | PyTorch/ONNX/opset mismatch or unsupported model op | Try a newer opset, `--dynamo`, or a simpler/static export; note that not every architecture is export-clean. |
| Dynamic export fails or produces bad runtime shapes | Dynamic height/width is not supported by model internals or SAME padding path | Retry with static `--input-size`; avoid `--dynamic-size` for TensorFlow-style SAME padding models unless tested. |
| `--check-forward` fails after file creation | Numerical mismatch or ONNX Runtime unsupported behavior | Separate export success from parity failure; record input shape, opset, torch/onnxruntime versions, and max error if available. |
| Caffe2 consumer rejects graph | Initializers or ATEN fallback expectations differ | Try `--keep-init` and `--aten-fallback`; treat this as legacy compatibility, not a default. |
| Exported model has wrong classifier size | Model constructed with wrong `num_classes` or checkpoint does not match architecture | Pass `--num-classes` to export or fix the source checkpoint/model pairing. |

## ONNX Validation Problems

| Symptom | Likely cause | Response |
| --- | --- | --- |
| Validation cannot open dataset | `data` path is wrong or lacks image-class folder layout | Route dataset layout details to CLI/data workflow guidance and verify the validation split path. |
| Accuracy is much lower than PyTorch | Preprocessing mismatch or wrong labels/classes | Match `--img-size`, `--mean`, `--std`, `--crop-pct`, and `--interpolation` to the model pretrained config. |
| Validation is very slow or OOMs | Batch size/workers too high for CPU or memory | Lower `--batch-size`, reduce `--workers`, and skip profiling until correctness is established. |
| Optimized graph is not written | `--onnx-output-opt` omitted or path not writable | Provide an explicit output path and check write permissions. |

## Checkpoint Cleaning Problems

| Symptom | Likely cause | Response |
| --- | --- | --- |
| Output already exists | Cleaner refuses overwrites | Choose a new output path or intentionally remove the old file outside the helper. |
| Missing/unexpected `module.` keys | DDP wrapper prefix or checkpoint structure mismatch | Cleaning strips leading `module.`; inspect keys before and after. |
| Loaded weights are not the expected version | EMA selected by default | Add `--no-use-ema` when raw model weights are required. |
| SplitBN auxiliary keys fail loading into normal BN model | Auxiliary batch norm keys remain | Use `--clean-aux-bn` for checkpoints trained with SplitBN when deploying a normal BN model. |
| safetensors save fails | `safetensors` package missing | Install `safetensors` or save `.pth` for local use. |
| Unsafe pickle/global error | PyTorch weights-only safe loading rejected custom objects | Use trusted checkpoints only; avoid automatic unsafe fallback. If full resume metadata is required, explicitly choose an unsafe load path in a controlled environment. |

## Checkpoint Averaging Problems

| Symptom | Likely cause | Response |
| --- | --- | --- |
| No checkpoints selected | Wrong `--input` or `--filter` | Print/inspect the glob pattern and use `--no-sort` if metrics are absent. |
| Top-N selection is empty | Checkpoints lack `metric` or `metrics`/`metric_name` | Use `--no-sort` or average an explicitly filtered set. |
| Averaged checkpoint loads poorly | Mixed architectures, heads, class counts, or unrelated training runs | Average only compatible checkpoints from the same or child training session. |
| Some tensors underrepresented | Missing keys across selected checkpoints | Inspect key sets before averaging; do not average incompatible checkpoint families. |
| Output extension surprises consumers | safetensors flag and extension mismatch | Use `.safetensors` with `--safetensors`; use `.pth` for PyTorch serialization. |

## Hub and Local-Dir Problems

| Symptom | Likely cause | Response |
| --- | --- | --- |
| `hf-hub` package error | `huggingface_hub` missing | Install `huggingface_hub` or use a local-dir package. |
| Hub auth or 404 failure | Private repo, missing token, typo, or revision mismatch | Verify `owner/model`, `@revision`, login/token state, and repo visibility. |
| Network/cache failure | Offline host, proxy, or unwritable cache | Use `cache_dir`, predownload weights, or package as `local-dir:`. |
| `config.json` missing | Local-dir or Hub package is incomplete | Add a timm-compatible `config.json` with `architecture` and `pretrained_cfg`. |
| No suitable checkpoint found in local-dir | Weight file name is not recognized | Rename to `model.safetensors`, `pytorch_model.bin`, `pytorch_model.pth`, or another preferred filename. |
| Wrong checkpoint selected | Multiple fallback weight files exist | Keep one preferred weight file in the directory or remove ambiguous fallback files. |
| `safetensors` not used even though desired | Package missing or no safe file present | Install `safetensors` and publish `model.safetensors`; otherwise timm falls back to PyTorch weights. |

## Torch Hub Problems

| Symptom | Likely cause | Response |
| --- | --- | --- |
| Torch Hub cannot find entrypoint | Repository source or model entrypoint mismatch | Prefer `timm.create_model`; if Torch Hub is required, verify the entrypoint exists in timm's registry. |
| Torch Hub download/cache behaves unexpectedly | Torch Hub source/cache rules differ from timm create_model | Use direct timm APIs for clearer `cache_dir`, Hub, and pretrained tag behavior. |

## Conversion Problems

| Symptom | Likely cause | Response |
| --- | --- | --- |
| Conversion script import fails | External framework dependency missing | Install the source framework only if safe and necessary; otherwise treat script as mapping reference. |
| Converted checkpoint has many unexpected keys | Architecture mapping does not match timm target | Compare source/timm layer names and adapt mapping logic before cleaning. |
| Classifier shape mismatch | Source checkpoint has different class count | Load with matching `num_classes`, drop/adapt classifier keys, or fine-tune a new head. |
| Conversion requires unavailable upstream files | External checkpoint, config, tokenizer, or model assets missing | Ask for the required assets; do not fabricate conversion results. |

## Recovery Checklist

1. Reproduce with command printing first using bundled helpers.
2. Confirm optional packages: `onnx`, `onnxruntime`, `huggingface_hub`, and `safetensors` as needed.
3. Confirm model identity, checkpoint lineage, class count, and input shape.
4. Prefer static ONNX export before dynamic export.
5. Inspect checkpoint keys before cleaning or averaging.
6. Package shared models with `config.json` and one preferred weight filename.
