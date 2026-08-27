# Inference Workflows

This reference covers the model-side inference contract for Photo2Cartoon.
It intentionally does not explain face detection, alignment, crop expansion, or segmentation internals.

## Shared input contract

The inference recipes expect a face patch that has already been prepared by the preprocessing flow:

- aligned portrait face crop
- alpha mask or equivalent foreground mask
- image content suitable for a 256 by 256 resize before model input
- RGB pixel order before normalization
- a face large enough to be detected upstream; the source README recommends a face larger than roughly 200 by 200 pixels

If you only have a raw portrait, route it through the preprocessing sub-skill first.

## Shared tensor contract

The source inference flow uses the same model-side normalization for both PyTorch and ONNX:

```python
face = (face * mask + (1 - mask) * 255) / 127.5 - 1
```

Practical interpretation:

- `face` is `uint8` RGB with shape `H x W x 3`
- `mask` is `float32` or `uint8` alpha with shape `H x W x 1`
- resize the face patch to `256 x 256` before model inference
- convert to `float32`
- transpose to `NCHW`
- the model expects a single portrait at a time

The output tensor is a portrait image in `[-1, 1]`. Convert it back with:

```python
cartoon = (cartoon + 1) * 127.5
cartoon = (cartoon * mask + 255 * (1 - mask)).astype(np.uint8)
```

The final file should be an ordinary RGB image after save-time validation.

## PyTorch workflow

### Entry point

- Script: [`../scripts/pytorch_inference_recipe.py`](../scripts/pytorch_inference_recipe.py)
- Checkpoint: `photo2cartoon_weights.pt`
- Model class: `ResnetGenerator(ngf=32, img_size=256, light=True)`
- Checkpoint key: `genA2B`

### Runtime steps

1. Load the checkpoint with `torch.load(..., map_location=device)`.
2. Load `params['genA2B']` into the generator.
3. Move the model to `cuda` when available, otherwise `cpu`.
4. Run the model under `torch.no_grad()`.
5. Take the first output image from `net(face)[0][0]`.
6. Rescale, composite, and save the result.

### Validation checks

- the checkpoint exists and contains `genA2B`
- the input tensor has shape `1 x 3 x 256 x 256`
- the saved file is decodable
- the saved file has nonzero dimensions

### Example command

```bash
python scripts/pytorch_inference_recipe.py \
  --repo-root /path/to/photo2cartoon \
  --face-rgba-path /path/to/preprocessed_face.png \
  --save-path /path/to/cartoon.png
```

## ONNX workflow

### Entry point

- Script: [`../scripts/onnx_inference_recipe.py`](../scripts/onnx_inference_recipe.py)
- Checkpoint: `photo2cartoon_weights.onnx`
- Expected input name: `input`
- Expected output name: `output`

### Runtime steps

1. Open the graph with `onnxruntime.InferenceSession`.
2. Confirm the provider list you asked for is available.
3. Feed the normalized tensor under the `input` name.
4. Read the first output tensor from `output`.
5. Rescale, composite, and save the result.

### Validation checks

- the graph opens successfully in onnxruntime
- the input name is `input` unless you deliberately exported a different graph
- the output name is `output` unless you deliberately exported a different graph
- the saved file is decodable
- the saved file has nonzero dimensions

### Example command

```bash
python scripts/onnx_inference_recipe.py \
  --repo-root /path/to/photo2cartoon \
  --face-rgba-path /path/to/preprocessed_face.png \
  --save-path /path/to/cartoon.png
```

## Cog-like workflow

The Cog surface is a thin wrapper around the PyTorch recipe:

- input field: `photo`
- input type: `Path`
- return type: output image path or `None`

The source wrapper reads the uploaded portrait with OpenCV, converts it to RGB, calls the same model-side generation logic, writes a temporary `out.png`, and returns that path.

## Output validation

For every workflow:

- confirm the output file exists
- confirm the output file size is greater than zero
- confirm the image decodes successfully
- confirm the decoded image has width and height greater than zero
- if the output looks color-shifted, recheck the RGB/BGR handoff
