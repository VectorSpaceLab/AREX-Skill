# WorldGen API and output contracts

The live package exposes `WorldGen` from `worldgen.__init__`. The verified
inspection signatures below are the stable entry points to use in new code.
Use `scripts/check_worldgen_env.py` to re-check them after an environment or
package refresh.

## `WorldGen`

```python
WorldGen(
    mode: str = "t2s",
    use_sharp: bool = False,
    inpaint_bg: bool = False,
    lora_path: str = None,
    resolution: int = 1600,
    device: torch.device = "cuda",
    low_vram: Optional[bool] = None,
)
```

- `mode` must be `"t2s"` for text-to-scene or `"i2s"` for image-to-scene.
- `device` is CUDA-oriented in the documented workflow. A CPU import is useful
  for diagnostics, but it is not a substitute for real generation.
- `low_vram=None` lets the constructor infer a low-VRAM choice from the visible
  GPU. The bundled demo also enables it automatically below 24 GB of VRAM.
- `use_sharp=True` loads the optional ml-sharp Gaussian predictor and is a
  separate, experimental dependency path.
- `inpaint_bg=True` loads segmentation and LaMa-based inpainting components.
  The interactive demo rejects `inpaint_bg` together with mesh output.
- `lora_path` overrides the WorldGen LoRA checkpoint path. If omitted, the
  panorama generation helpers download the project checkpoint from the model
  hub on first use.
- `resolution` controls generated panorama dimensions: the panorama helpers use
  `height=resolution // 2` and `width=resolution`.

### Main methods

```python
WorldGen.generate_pano(
    self,
    prompt: str = "",
    image: Optional[PIL.Image.Image] = None,
) -> PIL.Image.Image

WorldGen.generate_world(
    self,
    prompt: str = "",
    image: Optional[PIL.Image.Image] = None,
    return_mesh: bool = False,
) -> SplatFile | open3d.geometry.TriangleMesh

WorldGen._generate_world(
    self,
    pano_image: PIL.Image.Image,
    return_mesh: bool = False,
) -> SplatFile | open3d.geometry.TriangleMesh
```

`generate_world()` first creates a panorama (`generate_pano`) and then converts
that panorama to a scene. Use `_generate_world()` when the input is already an
equirectangular panorama; the public README documents this route for 2:1
panorama images.

- Default output is a `SplatFile` suitable for Gaussian-splat viewers.
- With `return_mesh=True`, the output is an Open3D triangle mesh.
- With `use_sharp=True`, the panorama is processed through six cubemap faces
  and merged into a globally aligned Gaussian scene.
- With `inpaint_bg=True`, the generated foreground splat is merged with an
  inpainted background splat; this path is experimental and download-heavy.

## `SplatFile`

```python
SplatFile(
    centers: numpy.ndarray,      # (N, 3)
    rgbs: numpy.ndarray,         # (N, 3), normalized RGB
    opacities: numpy.ndarray,    # (N, 1)
    covariances: numpy.ndarray,  # (N, 3, 3)
    rotations: numpy.ndarray,    # (N, 4), wxyz quaternions
    scales: numpy.ndarray,       # (N, 3)
)

SplatFile.save(path: str) -> None
```

`save()` writes a PLY vertex file with positions, zero normals, RGB spherical
harmonic DC coefficients, opacity, log-scales, and quaternion rotations. Use a
`.ply` suffix and validate the output path before starting a long generation.

Useful conversion helpers:

```python
convert_rgbd_to_gs(rgb, distance, rays, dis_threshold=0.0, epsilon=1e-3, scale_factor=0.65)
mask_splat(splat, mask)
merge_splats(splat1, splat2)
convert_rgbd2mesh_panorama(rgb, distance, rays, mask=None, max_size=4096, device="cuda")
```

`convert_rgbd_to_gs()` expects an RGB tensor shaped `(H, W, 3)`, a distance
map shaped `(H, W)`, and unit rays shaped `(H, W, 3)`. `convert_rgbd2mesh_panorama`
uses the same aligned RGB-D-ray contract and returns an Open3D mesh.

## Panorama and model helpers

Use these helpers only when a task needs a lower-level stage than
`WorldGen.generate_world()`:

```python
build_depth_model(device="cuda")
pred_pano_depth(model, image)
pred_depth(model, image)

build_pano_gen_model(lora_path=None, device="cuda", low_vram=True)
build_pano_fill_model(lora_path=None, device="cuda", low_vram=True)
gen_pano_image(model, prompt="", output_path=None, seed=42,
               guidance_scale=7.0, num_inference_steps=50,
               height=800, width=1600, blend_extend=6, ...)
gen_pano_fill_image(model, image, mask, prompt="a scene",
                     output_path=None, seed=42, guidance_scale=30.0,
                     num_inference_steps=50, height=800, width=1600,
                     blend_extend=6, ...)
```

The text and image panorama helpers prepend a high-quality 360-panorama prefix
and append an HDR/RAW/omnidirectional suffix. They use CPU-seeded generators
with default seed `42`, but the diffusion model and its LoRA/model-hub assets
still require a compatible GPU environment and model access.

Lower-level optional helpers include `build_inpaint_model()`,
`inpaint_image()`, `inpaint_pano()`, `build_segment_model()`, `seg_pano()`,
and `seg_pano_fg()`. The Sharp path exposes `build_sharp_model()` and
`predict_equirectangular()`, but importing that module requires the external
`sharp` package and should be treated as optional.

## Geometry utilities

```python
pano_unit_rays(h, w, device)
pano_to_cube(pano_img, face_w, mode="bilinear")
cube_to_pano(cube_faces, h, w, mode="bilinear")
resize_img(img, max_size=1024)
map_image_to_pano(predictions, crop_center=False, map_h=1024,
                  map_w=2048, nn_batch=8192, device="cuda")
```

`resize_img()` limits the longest edge of an image-to-scene input to 1024
pixels before it is mapped into panorama space. A panorama supplied to the
high-level demo is normalized to 2048x1024, preserving the required 2:1 shape.
