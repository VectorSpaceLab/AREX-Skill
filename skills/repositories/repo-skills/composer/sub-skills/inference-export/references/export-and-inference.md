# Export and inference workflows

This reference covers the normal export path for Composer or plain PyTorch modules.

## Core APIs

```python
def export_for_inference(
    model: nn.Module,
    save_format: Union[str, ExportFormat],
    save_path: str,
    save_object_store: Optional[ObjectStore] = None,
    sample_input: Optional[Any] = None,
    dynamic_axes: Optional[Any] = None,
    surgery_algs: Optional[Union[Callable[[nn.Module], nn.Module], Sequence[Callable[[nn.Module], nn.Module]]]] = None,
    transforms: Optional[Sequence[Transform]] = None,
    onnx_opset_version: Optional[int] = None,
    load_path: Optional[str] = None,
    load_object_store: Optional[ObjectStore] = None,
    load_strict: bool = False,
    input_names: Optional[Sequence[str]] = None,
    output_names: Optional[Sequence[str]] = None,
) -> None


def export_with_logger(
    model: nn.Module,
    save_format: Union[str, ExportFormat],
    save_path: str,
    logger: Logger,
    save_object_store: Optional[ObjectStore] = None,
    sample_input: Optional[Any] = None,
    transforms: Optional[Sequence[Transform]] = None,
    input_names: Optional[Sequence[str]] = None,
    output_names: Optional[Sequence[str]] = None,
) -> None
```

Supported formats are `torchscript` and `onnx`.

## Export order

The utility uses this order:

1. reject direct export of DDP or FSDP wrapped modules
2. return immediately on non-zero global ranks
3. deep-copy the model and sample input
4. move the model and sample input to CPU
5. apply `surgery_algs`
6. load checkpoint weights from `load_path` / `load_object_store` when provided
7. switch to eval mode
8. apply `transforms`
9. export to TorchScript or ONNX
10. upload to `save_object_store` when provided

That order matters:

- `surgery_algs` are for structural changes before checkpoint weights are loaded.
- `transforms` are for inference-time optimizations after the model is loaded.
- `load_strict=False` keeps missing or unexpected keys as warnings rather than a hard failure.

## TorchScript recipe

Use TorchScript when the model is scriptable or when you are happy with the trace fallback.

```python
export_for_inference(
    model=model.eval(),
    save_format="torchscript",
    save_path="model.pt",
)
```

Notes:

- `sample_input` is optional for TorchScript.
- If scripting fails and `sample_input` is available, the export helper tries `torch.jit.trace`.
- If both scripting and tracing fail, the export raises an error.

## ONNX recipe

Use ONNX when the target runtime needs it.

```python
export_for_inference(
    model=model.eval(),
    save_format="onnx",
    save_path="model.onnx",
    sample_input=sample_batch,
    dynamic_axes={
        "input": {0: "batch_size"},
        "output": {0: "batch_size"},
    },
    input_names=["input"],
    output_names=["output"],
    onnx_opset_version=14,
)
```

Rules for ONNX:

- `sample_input` is required.
- `sample_input` must match the model's forward-call structure. For some Composer model flows this is a batch object or a `(batch, {})` args/kwargs-style tuple; for a plain `nn.Module.forward(x)`, use the tensor or tuple that `forward` actually accepts.
- `input_names` and `output_names` should match the exported graph.
- `dynamic_axes` keys must match those names.
- If `sample_input` contains dict inputs, the utility uses those keys to infer default input names.
- If no names are inferred, the fallback is `input` for inputs and `output` for outputs.

## Checkpoint-backed export

Use `load_path` when the export should start from saved weights rather than the current in-memory weights.

```python
export_for_inference(
    model=model,
    save_format="torchscript",
    save_path="export/model.pt",
    load_path="checkpoints/ep1-ba4-rank0.pt",
)
```

Use `load_object_store` when `load_path` points to a remote object name rather than a local file.

Guidelines:

- If the checkpoint is remote, provide the matching object store.
- Keep `load_strict=True` when you want exact key matching.
- Expect missing or unexpected key warnings when `load_strict=False`.
- If the model architecture changes before loading, put those changes in `surgery_algs` so they run before weights are loaded.

## Logger-backed export

`export_with_logger` is the helper used by the callback and by trainer-aware export flows.

Behavior:

- if `save_object_store` is provided, it uploads there
- otherwise, if the logger can upload files, it writes to a local temp file and uploads through the logger
- otherwise, it writes locally to `save_path`

Use this when you want the export artifact to follow the same file-upload path as other training artifacts.

## Rank-zero behavior

Export only happens on global rank 0.

This means:

- distributed launches should not expect every rank to write the artifact
- a missing local file on non-zero ranks is normal
- if an export unexpectedly produces no file, confirm the run reached rank 0 and the output path was reachable there

## Validation checks

### TorchScript

1. call `torch.jit.load(save_path)`
2. run the same example input through the loaded model
3. compare outputs with the original model using `torch.testing.assert_close`

### ONNX

1. install `onnx` and `onnxruntime` if they are not already available
2. call `onnx.load(save_path)`
3. run `onnx.checker.check_model(...)`
4. execute an ONNX Runtime inference pass on the exported artifact
5. compare the ONNX outputs against the original model with a slightly looser tolerance than TorchScript

### Size / optimization checks

If you use `quantize_dynamic`, a useful smoke check is that the exported file gets smaller and still produces acceptable outputs.

## Common transform patterns

- `surgery_algs`: model edits that should happen before weights load
- `transforms`: inference optimizations such as dynamic quantization
- `quantize_dynamic`: bundled shorthand for dynamic quantization over linear layers

You can pass either a single callable or a sequence of callables to `surgery_algs`, and a sequence to `transforms`.

## Practical recipe

A good export flow usually looks like this:

1. create or load the base model
2. decide whether the checkpoint should be loaded during export
3. decide whether the graph needs structural surgery
4. decide whether inference transforms should be applied
5. set export format-specific options
6. export
7. reload and validate the artifact

Keep HuggingFace-specific tokenizer, PEFT, and checkpoint metadata details in the adjacent integration reference.
