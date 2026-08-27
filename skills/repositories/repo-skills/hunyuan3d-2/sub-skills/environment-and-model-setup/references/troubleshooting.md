# Environment and Model Setup Troubleshooting

## PyTorch CUDA mismatch

Symptoms:

- `torch.cuda.is_available()` is false despite visible GPUs.
- CUDA allocation fails immediately.
- Extension builds find a different CUDA version than PyTorch expects.

Fixes:

1. Install a PyTorch wheel/conda package matching the desired CUDA runtime.
2. Confirm driver supports the runtime version.
3. Build texture extensions after PyTorch is installed.
4. Re-run `scripts/check_install.py --check-cuda --json`.

## `cusparse.h` missing while building `custom_rasterizer`

The custom rasterizer needs CUDA development headers, not only runtime libraries. Install CUDA library development packages for the active CUDA version and rebuild with build isolation disabled:

```bash
python -m pip install --no-build-isolation hy3dgen/texgen/custom_rasterizer
```

## `ImportError: libc10.so` when importing `custom_rasterizer`

Import PyTorch first so its shared libraries are loaded:

```python
import torch
import custom_rasterizer
```

If this still fails, inspect `LD_LIBRARY_PATH`/shared-library visibility for the active environment.

## `libOpenGL.so.0` or pymeshlab plugin warnings

Install an OpenGL runtime library visible to the active environment. This affects mesh cleanup and pymeshlab import behavior. Do not ignore it if tasks require `FloaterRemover`, `DegenerateFaceRemover`, or `FaceReducer`.

## Model download failures

- Verify the exact model repo id and subfolder.
- Confirm network/Hugging Face access if not using a pre-populated cache.
- Set `HY3DGEN_MODELS` for local caches.
- For texture, cache both `hunyuan3d-delight-v2-0` and the paint subfolder.
- For FlashVDM, cache the turbo VAE subfolder too.

## `pip check` conflicts

If `pip check` fails after installing requirements, resolve package conflicts before generation. Do not assume a parser check proves inference readiness. Pay special attention to `torch`, `torchvision`, `diffusers`, `transformers>=4.48.0`, `onnxruntime`, and compiled extension ABI compatibility.

## Blender unavailable

`blender_addon.py` requires Blender's `bpy`; ordinary Python environments will fail to import it. Treat Blender runtime as optional integration coverage. Use static payload guidance and API client checks outside Blender.

## Stale repository documentation

Some source documentation pages in the distilled checkout contained stale placeholder text unrelated to Hunyuan3D. Do not use those pages for install or workflow truth. Prefer package metadata, model zoo facts, and this skill.

## Full inference is slow or unsafe to run in verification

Full shape/texture examples can download large weights and use long CUDA inference. For ordinary verification, run:

```bash
python scripts/check_install.py --check-cuda --check-extensions --json
python ../shape-generation/scripts/generate_shape.py --image fixture.png --dry-run
python ../texture-and-mesh/scripts/texture_mesh.py --mesh fixture.glb --image fixture.png --dry-run
```

Run full model examples only when model cache/network and GPU time are approved.
