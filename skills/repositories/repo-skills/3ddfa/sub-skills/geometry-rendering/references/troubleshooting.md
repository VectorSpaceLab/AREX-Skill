# Troubleshooting

## Common failure modes

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError: cannot import name 'mesh_core_cython' from 'utils.cython'` | The Cython extension has not been built yet, or it was built for another Python ABI. | Build it in `utils/cython` with `python3 setup.py build_ext -i`, then re-run the import checks from [`rendering-and-cython.md`](rendering-and-cython.md). |
| `import utils.render` fails immediately | `utils.render` imports the compiled extension at module import time. | Treat this as a build issue, not a geometry bug. Rebuild the extension or avoid depth/PNCC/lighting until it is available. |
| Sparse or dense reconstruction has the wrong shape | The caller passed the wrong parameter length or skipped the geometry smoke. | Use the bundled [`scripts/smoke_geometry.py`](../scripts/smoke_geometry.py) to verify the zero-vector path. The expected shapes are `(3, 68)` and `(3, 53215)`. |
| OBJ appears mirrored or the colors look swapped | The helper writes vertices in `(y, x, z)` order and samples colors from an image loaded with OpenCV conventions. | Keep the helper’s axis and channel ordering exactly as documented in [`output-formats.md`](output-formats.md). |
| Depth or PNCC images are blank or distorted | Triangle indices were offset incorrectly. | Use `visualize/tri.mat` as the canonical triangle matrix, and subtract 1 only for the accelerated rasterizer calls that require zero-based indices. |
| `utils.params` or `utils.paf` fails to import | A `train.configs/` artifact is missing or unreadable. | Check that the `.npy` and `.pkl` files listed in [`data-artifacts.md`](data-artifacts.md) are present and readable. |
| `imageio.mimwrite` fails when writing MP4 | The imageio video backend is missing or cannot find a codec. | Install the backend required by your environment, or write the frames first and use a system encoder afterwards. |
| `bfm.ply` / `bfm_refine.ply` look inconsistent with the training basis | The neck-removal note warns that the z-axis convention differs in `model_refine.mat`. | Keep those files for visualization only unless you deliberately reconcile the coordinate system. |

## Safe fallback policy

If the compiled renderer is unavailable, continue with the geometry-only path:

- `reconstruct_vertex`
- `predict_68pts`
- `predict_dense`
- `dump_to_ply`
- `dump_vertex`
- `write_obj_with_colors`
- `parse_pose`

Reserve depth, PNCC, and lighting outputs until the extension is built.
