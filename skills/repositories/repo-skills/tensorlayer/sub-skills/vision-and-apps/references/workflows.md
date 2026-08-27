# Workflows

## Pretrained constructor smoke

1. Instantiate the image constructor with `pretrained=False`.
2. Confirm the returned object is a TensorLayer model.
3. Optionally run a tiny forward pass on a synthetic 224x224x3 tensor.

## Vision wrapper guidance

- For object detection, use the app wrapper as a reference and keep the bundled smoke import-only.
- For human pose estimation, treat the full example as reference-only because it expects external weights and data.
- For spatial-transformer or quantized-vision workflows, start from the model constructor or the preprocessing helper and use tiny synthetic inputs.

The bundled `scripts/smoke_vision_models.py` focuses on constructor availability instead of downloading weights.
