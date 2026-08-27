# Rendering and Cython

The geometry and dense-render helpers in this repo are split between reference Python implementations and a compiled Cython extension.

## What the extension does

- `utils.render` imports `mesh_core_cython` at module import time.
- `utils.lighting.RenderPipeline` uses the extension to compute normals and then rasterizes the lit mesh.
- Depth and PNCC helpers call the accelerated rasterizer for the operational path.

Because of that import structure, `ImportError` from `utils.render` is expected until the extension is built.

## Build the extension

The repo ships the usual Cython build command in `utils/cython/readme.md`:

```bash
cd utils/cython
python3 setup.py build_ext -i
```

The build requires:

- Cython
- NumPy headers
- a working C/C++ compiler toolchain

The compiled library name is platform-specific and usually looks like `mesh_core_cython.*.so`.

## Dense render helper flow

The Obama demo shows the intended render/video workflow:

1. `demo@obama/rendering.py` loads precomputed dense vertices, a triangle matrix, and the background frame.
2. `RenderPipeline` applies simple lighting and dense rasterization.
3. The frames are written to `obama_res@dense_py/`.
4. `scripts/images_to_video.py` can stitch the frames into an MP4.

That helper expects the same general vertex convention as the main pipeline: image-space vertices and a triangle matrix that matches the selected mesh basis.

## Safe fallback guidance

If the extension is unavailable:

- sparse and dense geometry reconstruction still works;
- PLY/OBJ serialization still works;
- pose estimation still works;
- PAF construction still works;
- depth, PNCC, and lighting-based dense rendering should be treated as unavailable until the extension is built.

The Python source includes reference implementations of several render loops, but the packaged skill treats the compiled path as the supported operational path because the import itself depends on the extension.

## Fast checks

Useful quick checks after building:

```bash
python -c "from utils.cython import mesh_core_cython; print(mesh_core_cython.__file__)"
python -c "import utils.render; print('render import ok')"
```

If the second command fails, the extension is still missing or built for the wrong Python ABI.
