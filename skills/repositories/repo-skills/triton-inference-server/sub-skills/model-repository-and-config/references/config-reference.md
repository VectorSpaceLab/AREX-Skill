# config.pbtxt Reference

## Required minimal settings

A minimal config usually needs:

- `platform` and/or `backend`
- `max_batch_size`
- `input` tensors
- `output` tensors

Each input/output needs a name, datatype, and dims. Batchable models use a nonzero `max_batch_size`; then Triton prepends the batch dimension to the shape.

## Common rules

- Input/output tensor names must match what the model expects.
- `dims` must describe the non-batch dimensions.
- `-1` can represent variable dimensions when the backend supports them.
- `reshape` is required when Triton request shapes differ from backend shapes.
- `allow_ragged_batch` is only relevant to dynamic batching.
- Ensemble and BLS configs require additional topology/step details and should be treated as separate workflow depth, not mere syntax noise.

## Backend-specific notes

- PyTorch/TorchScript naming conventions differ from most backends; confirm the exact input/output names before building a config.
- Python backend models can often auto-complete part of the config through `auto_complete_config`.
- Custom backends may require `backend` in `config.pbtxt` or a `name.backend` model directory form.

## Generated config inspection

The model config endpoint can be used to read back the minimal generated config from a live server once a model is loaded. That is a runtime check, not a substitute for config authoring.
