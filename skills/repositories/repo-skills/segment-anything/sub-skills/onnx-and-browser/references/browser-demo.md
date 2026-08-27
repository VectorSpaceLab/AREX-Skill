# Browser Demo Integration

The Segment Anything browser pattern is a front-end-only React app using `onnxruntime-web`, `npyjs`, WebAssembly, Web Workers, SIMD, and optionally multithreading via `SharedArrayBuffer`. The browser runs the ONNX prompt encoder/mask decoder while the image encoder runs offline to produce a `.npy` embedding.

## Asset Contract

A browser app needs these deployable assets:

- an image file, such as `/assets/data/example.jpg`
- a matching embedding file, such as `/assets/data/example_embedding.npy`
- an exported or quantized ONNX decoder, such as `/model/sam_onnx_quantized.onnx`

Keep the image, embedding, and ONNX model synchronized. If a checkpoint changes, export a new ONNX model and regenerate embeddings for every image served with that model.

## Minimal Runtime Flow

1. Load the ONNX model with `InferenceSession.create(MODEL_URL)`.
2. Load the image in the browser and record original `height` and `width`.
3. Compute `samScale = 1024 / Math.max(height, width)`.
4. Load the `.npy` embedding and wrap it as an `onnxruntime-web` float32 tensor.
5. Convert click or box prompts into resized coordinates by multiplying original-image coordinates by `samScale`.
6. Run the ONNX session with the required feed names.
7. Render `masks` output as an image or canvas overlay.

## Feed Names and Browser Shapes

Use these keys in the ONNXRuntime Web feed object:

```ts
{
  image_embeddings,
  point_coords,
  point_labels,
  mask_input,
  has_mask_input,
  orig_im_size,
}
```

For click-only prompting, append one padding point `(0, 0)` with label `-1`. Example shapes:

- `image_embeddings`: `[1, 256, 64, 64]`
- `point_coords`: `[1, n + 1, 2]`
- `point_labels`: `[1, n + 1]`
- `mask_input`: `[1, 1, 256, 256]`
- `has_mask_input`: `[1]`
- `orig_im_size`: `[2]`

The demo source organizes this logic around `App.tsx`, `Stage.tsx`, `Tool.tsx`, `helpers/onnxModelAPI.tsx`, `helpers/maskUtils.tsx`, `helpers/scaleHelper.tsx`, and shared state hooks. Recreate the contract rather than depending on the original demo source at runtime.

## SharedArrayBuffer Headers

ONNXRuntime Web multithreading needs cross-origin isolation. Configure the development or production server to include:

```http
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: credentialless
```

Without these headers, browsers can disable `SharedArrayBuffer`; ONNXRuntime Web may fall back to single-threaded execution or fail depending on the runtime configuration. Ensure all subresources are compatible with the chosen cross-origin embedder policy.

## Updating Demo Assets

When replacing the sample image or checkpoint:

1. Export the ONNX decoder for the new checkpoint and `model_type`.
2. Regenerate `.npy` embeddings using the same checkpoint and `model_type`.
3. Copy the image and embedding into the app's static assets.
4. Update constants equivalent to `IMAGE_PATH`, `IMAGE_EMBEDDING`, and `MODEL_DIR`.
5. Confirm a simple positive click produces a non-empty mask and that output dimensions match the original image size.
