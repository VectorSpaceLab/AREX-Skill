# WorldGen installation and runtime troubleshooting

## Start from a clean, compatible environment

WorldGen declares Python `>=3.11` and a GPU-heavy dependency set. Prefer a
private environment rather than repairing a shared environment that already
contains another diffusion stack. Install a CUDA-capable PyTorch build before
installing the package, then run:

```bash
python -m pip install -e .
python scripts/check_worldgen_env.py
```

The source metadata includes a Nunchaku wheel, a modified Viser dependency, and
`utils3d`. The README additionally documents DA-2 and PyTorch3D installs. If a
fresh install resolves incompatible torch, xformers, Nunchaku, or PyTorch3D
variants, keep the framework, CUDA runtime, Python ABI, and compiled extensions
on a consistent version family instead of accepting a CPU-only fallback.

## Import errors

- **`ModuleNotFoundError: open3d`**: install Open3D before using mesh output or
  the demo viewer.
- **`ModuleNotFoundError: viser`**: install Viser before using the interactive
  viewer. Mesh rendering may need a Viser build that supports double-sided mesh
  display; if faces appear culled, switch to a compatible Viser build or use a
  splat viewer.
- **`ModuleNotFoundError: nunchaku`**: install the Nunchaku wheel selected by
  the project and verify that its Python ABI and torch/CUDA build match.
- **`ModuleNotFoundError: da2` or `utils3d`**: install DA-2 using its documented
  source distribution and its required support package. The DA-2 package may
  pin exact versions of torch, diffusers, transformers, timm, OpenCV, and
  xformers; use a clean environment if those pins conflict with WorldGen.
- **`ModuleNotFoundError: pytorch3d`**: install a PyTorch3D build compatible
  with the chosen Python, torch, and CUDA versions. Its `transforms` module is
  imported by the splat conversion utilities, so a CPU-only import is not
  sufficient evidence for the complete GPU workflow.
- **`cannot import name 'SiglipImageProcessor' from transformers`**: the
  Transformers version is too old for the installed Diffusers loader. Upgrade
  Transformers to the minimum declared by WorldGen and rerun the import check.
- **`pip check` reports unrelated packages**: use a clean private environment;
  shared environments often retain strict requirements from another project.

## CUDA and VRAM

- **`torch.cuda.is_available()` is false**: verify that the environment has a
  CUDA-enabled torch build, the host exposes an NVIDIA device, and the driver
  supports the wheel's CUDA runtime. A CPU import does not prove WorldGen can
  run its diffusion and depth models.
- **The demo fails at `torch.cuda.get_device_properties(0)`**: the demo is
  intentionally GPU-first. Install a CUDA-capable torch environment and verify
  a tiny CUDA allocation with `scripts/check_worldgen_env.py`.
- **Out-of-memory during generation**: pass `--low_vram` or construct
  `WorldGen(..., low_vram=True)`. Lower `resolution`, avoid optional Sharp and
  inpainting paths, and close other GPU processes. The bundled demo auto-enables
  low-VRAM mode below 24 GB of visible memory.
- **Nunchaku or xformers import crashes with undefined symbols**: the extension
  was built for a different torch/Python/CUDA ABI. Recreate the environment with
  the project-compatible torch build rather than mixing wheels from unrelated
  environments.

## Model, network, and license failures

- **FLUX or LoRA download fails**: first-use generation downloads large model
  assets. Check network access, Hugging Face authentication, local cache space,
  and acceptance of the gated `FLUX.1-dev` license. A successful package import
  does not prove model availability.
- **DA-2 weights fail to download**: the depth model is loaded from the model
  hub during `build_depth_model()`. Check the hub cache and retry outside the
  final generation command so a failed download is easy to diagnose.
- **Generation hangs after startup**: diffusion and depth inference are long
  GPU operations. Watch GPU memory/utilization and model-download progress
  before interrupting. Avoid starting multiple viewer processes that compete
  for the same GPU.
- **Sharp path cannot load**: `--use_sharp` is optional and requires the
  external `sharp` package plus Apple Sharp weights. Remove the flag to validate
  the base WorldGen path first.
- **Background inpainting cannot load**: `--inpaint_bg` imports iopaint/LaMa and
  segmentation dependencies and may download a LaMa checkpoint. Remove the
  flag to validate base splat or mesh generation first.

## Input and output mistakes

- **`Invalid mode`**: use exactly `t2s` or `i2s` when constructing `WorldGen`.
  `t2s` rejects an image; `i2s` requires one.
- **Panorama artifacts or shape errors**: use an RGB equirectangular image with
  a 2:1 width-to-height ratio. The bundled demo normalizes panorama inputs to
  2048x1024 before the depth stage.
- **`--inpaint_bg` with `--return_mesh`**: the demo intentionally rejects this
  combination. Inpainting is implemented for the Gaussian-splat background
  merge path, not the mesh branch.
- **Unexpected image memory use**: image-to-scene inputs are resized so their
  longest edge is at most 1024 before mapping into panorama space. Reduce the
  input size yourself when debugging memory pressure.
- **Saved splat is not viewable**: confirm that `SplatFile.save()` received a
  writable `.ply` path and that the viewer understands Gaussian-splat PLY
  fields. The file stores RGB DC coefficients, opacity, log-scales, and wxyz
  rotations rather than a triangle mesh.
- **Saved mesh is empty or visually incorrect**: inspect the Open3D mesh before
  writing `mesh.glb`, check the RGB/depth/ray shapes, and verify that your Viser
  build handles double-sided textured mesh display.

## Viewer behavior

The interactive helper starts a Viser server on port 8080 and remains alive
until Ctrl-C. Scene generation happens before the first browser connection.
Camera-path generation and novel-view export happen from the browser UI; they
write `images/*.png` and `rgb.mp4` under the selected output directory. These
writes can be large, so choose an explicit output directory with enough space.
