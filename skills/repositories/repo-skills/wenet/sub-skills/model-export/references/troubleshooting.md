# Model Export Troubleshooting

## Required files are missing

Symptoms:

- `train.yaml` not found;
- checkpoint file missing;
- exported model cannot be paired with tokenizer resources.

Recovery:

```bash
python sub-skills/model-export/scripts/check_export_inputs.py \
  --model-dir exp/conformer --mode jit
```

Locate the generated training config and the checkpoint from the same
experiment. Do not export a checkpoint with an unrelated config.

## ONNX dependencies are absent

Symptoms:

- `Please install onnx and onnxruntime!`
- import errors before the ONNX parser runs.

Recovery:

Install `onnx` and the matching `onnxruntime` or `onnxruntime-gpu` package in
the export environment. Use CPU ONNX export unless a GPU provider is required
and verified.

## Streaming parameters are inconsistent

Symptoms:

- assertion failures involving `chunk_size` and `num_decoding_left_chunks`;
- runtime uses fixed chunks but export was non-streaming;
- cache shapes fail in deployment.

Recovery:

- For streaming, use positive `chunk_size` and a compatible left-chunk count.
- For non-streaming, use `chunk_size=-1` and `num_decoding_left_chunks=-1`.
- Do not deploy a non-streaming ONNX export as a streaming runtime model.
- Keep runtime decoder chunk settings consistent with export metadata.

## CUDA provider is unavailable

Symptoms:

- GPU ONNX export or recognition falls back to CPU unexpectedly;
- ONNX Runtime reports missing CUDA provider;
- TensorRT/Triton conversion cannot load GPU libraries.

Recovery:

1. Verify PyTorch CUDA and ONNX Runtime CUDA provider in the target environment.
2. Match CUDA runtime, driver, TensorRT, and ONNX Runtime versions.
3. If the task does not require GPU provider behavior, export CPU ONNX and mark
   GPU deployment as unverified.

## Quantized JIT is not produced

Dynamic quantization applies to supported modules such as linear layers. If the
quantized artifact fails, first create the non-quantized JIT file, verify it in
the target runtime, and then debug quantization separately.

## IPEX, Horizon BPU, or vendor export fails

Vendor export paths require vendor packages, SDKs, compilers, or devices that
ordinary package installation does not provide. Run the preflight helper to
surface missing Python modules, then verify the vendor toolchain outside the
safe skill checks before launching conversion.

## Export succeeds but runtime fails

Likely causes:

- missing `units.txt`, tokenizer model, or `global_cmvn` in the runtime bundle;
- runtime chunk/cache settings do not match export metadata;
- using ONNX artifacts with a libtorch runtime or JIT artifacts with an ONNX
  runtime;
- feature extraction parameters changed between training and deployment.

Route the task to [../../runtime-deployment/SKILL.md](../../runtime-deployment/SKILL.md)
and match artifact type, runtime engine, feature config, tokenizer resources,
and streaming settings.
