# Troubleshooting

This reference lists the most common export-specific failures and how to fix them.

## Missing sample input for ONNX

**Symptom**

- `ValueError: sample_input argument is required for onnx export`

**Likely cause**

- ONNX export was requested without a concrete example batch.

**Fix**

- pass a real example input that the model can already consume
- keep the example small, deterministic, and local
- ensure the input structure matches the model forward signature

## Missing optional ONNX packages

**Symptom**

- import errors or validation failures for `onnx` or `onnxruntime`

**Likely cause**

- the optional ONNX extras are not installed

**Fix**

- install the ONNX extras before validating the export
- rerun the export smoke after the packages are available

## Direct DDP export failure

**Symptom**

- `Directly exporting a DistributedDataParallel model is not supported`

**Likely cause**

- the wrapped DDP module was passed directly to the export helper

**Fix**

- export the underlying module instead of the DDP wrapper
- in a wrapped training job, unwrap the model before export

## Direct FSDP export failure

**Symptom**

- a failure explaining that FSDP modules cannot be deep-copied or exported directly

**Likely cause**

- the model is still wrapped with FSDP at export time

**Fix**

- recreate or load the model without FSDP wrapping for export
- do not rely on a direct deep copy of the wrapped module

## TorchScript scripting or tracing failure

**Symptom**

- `Scripting and tracing failed! No model is getting exported.`
- a `torch.jit` error mentioning unsupported control flow or unsupported ops

**Likely cause**

- the model contains TorchScript-incompatible code paths or unsupported operators

**Fix**

- simplify the model or remove unsupported ops
- supply a concrete `sample_input` so tracing fallback can run when scripting fails
- if TorchScript stays incompatible, try ONNX instead

## ONNX name or dynamic-axis mismatch

**Symptom**

- export succeeds, but ONNX Runtime input feeds fail or validation uses the wrong names

**Likely cause**

- `input_names`, `output_names`, or `dynamic_axes` do not match the exported graph

**Fix**

- make the names match the exported input and output structure
- keep `dynamic_axes` keys aligned with those names
- when exporting multiple outputs, provide one output name per output

## No file appears on every rank

**Symptom**

- only one worker writes an export artifact in a distributed run

**Likely cause**

- export is intentionally rank-zero only

**Fix**

- treat rank-zero-only export as expected behavior
- check the rank-0 worker’s output location when debugging a missing file

## Checkpoint weights do not match the exported model

**Symptom**

- missing or unexpected checkpoint keys
- exported artifact appears to use the wrong weights

**Likely cause**

- the checkpoint path is wrong
- the remote object store was not provided for a remote checkpoint
- the model architecture changed and the surgery step was not applied before loading

**Fix**

- confirm `load_path` points to the intended checkpoint
- provide `load_object_store` for remote checkpoint names
- set `load_strict=True` if exact key matching is required
- put architecture edits into `surgery_algs` so they run before checkpoint loading

## Remote save does not leave a local file behind

**Symptom**

- the export appears to succeed, but the expected local file is missing

**Likely cause**

- the export went through an object store or logger upload path

**Fix**

- confirm whether `save_object_store` was passed
- confirm the logger supports file upload destinations
- check the remote artifact location instead of the local filesystem

## HuggingFace tokenizer vocab is larger than the model

**Symptom**

- a ValueError saying the tokenizer has more tokens than the model

**Likely cause**

- the model embeddings are too small for the tokenizer vocabulary

**Fix**

- call `resize_token_embeddings(len(tokenizer))` before constructing `HuggingFaceModel`
- or pass `allow_embedding_resizing=True`

## PEFT type is rejected

**Symptom**

- an error saying only LORA is supported

**Likely cause**

- the PEFT config is not LoRA

**Fix**

- switch to a LoRA PEFT config
- confirm `peft` is installed before retrying

## Tokenizer metadata was not saved

**Symptom**

- the exported checkpoint does not contain tokenizer config

**Likely cause**

- no tokenizer was passed to `HuggingFaceModel`

**Fix**

- construct the wrapper with the tokenizer when you need tokenizer metadata in the checkpoint
