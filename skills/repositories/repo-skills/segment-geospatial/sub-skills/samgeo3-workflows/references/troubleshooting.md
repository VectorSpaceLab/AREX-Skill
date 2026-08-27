# SAM3 troubleshooting

## CUDA readiness

Run the bundled backend check before real SAM3 inference:

```bash
python scripts/samgeo3_backend_check.py --require-cuda
```

If CUDA is unavailable:

- Confirm the environment installed a CUDA torch build, not CPU-only torch.
- Confirm the container or host exposes an NVIDIA GPU.
- Confirm the driver supports the CUDA runtime bundled with torch.
- Do not claim SAM3 runtime readiness from CPU-only imports.

## Backend selection errors

| Error fragment | Meaning | Recovery |
| --- | --- | --- |
| `Invalid backend` | Backend string is neither `meta` nor `transformers` | Use `SamGeo3(backend="meta")` or `SamGeo3(backend="transformers")`. |
| `only supported with backend='meta'` | `facebook/sam3.1` was sent to the transformers backend | Use `SamGeo3(backend="meta", model_id="facebook/sam3.1")`. |
| Dependency import says install `[samgeo3]` | SAM3 optional dependencies are missing | Install `segment-geospatial[samgeo3]` or the selected broad extras. |

## Checkpoint and Hugging Face failures

- SAM3/SAM3.1 may require gated Hugging Face access. The user must request
  access and authenticate outside the skill.
- For SAM3.1, the package can fall back to `huggingface_hub` when the installed
  `sam3` downloader lacks a `version=` parameter.
- Use `checkpoint_path=` when deploying with a pre-downloaded checkpoint.
- Environment variable `SAM3_CHECKPOINT_PATH` can override the SAM3.1 checkpoint
  path for deployment compatibility.

## Dtype and repeated-image failures

- SAM3 Meta backend can produce bfloat16/float16 tensors. The package contains a
  conversion helper that upcasts unsupported floating dtypes before NumPy
  conversion.
- Reusing an encoded image state across SAM3 API requests can fail with dtype
  mismatch. The REST API deliberately re-encodes for SAM3 rather than using the
  image-cache skip that is safe for SAM/SAM2.

## Memory and tiling failures

- Lower `tile_size`, increase `overlap` only as needed, and keep `batch_size=1`
  until memory is known.
- Test a small raster crop before full-scene tiled segmentation.
- If output seams appear, increase overlap and inspect adjacent tile masks.
- If masks are too small or too many, adjust `confidence_threshold`, `min_size`,
  and `max_size` before vector conversion.

## Video workflow failures

- Large videos can exhaust GPU memory and disk; downsample with `frame_rate`.
- Use one object id and one prompt first; then add more prompts and propagate.
- If propagation drifts, add corrective point/box prompts at later frames before
  saving masks or blended videos.
