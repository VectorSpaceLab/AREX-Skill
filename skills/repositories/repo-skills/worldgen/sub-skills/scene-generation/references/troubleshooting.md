# Scene-generation troubleshooting

## Input selection

- If `WorldGen(mode="t2s")` receives an image, the package raises an assertion;
  switch to `mode="i2s"`.
- If `WorldGen(mode="i2s")` receives no image, the image-to-scene pipeline
  cannot build its panorama condition; provide an RGB PIL image.
- A panorama must be equirectangular and 2:1. Convert or crop it before calling
  `_generate_world()`; do not pass a perspective image as a panorama.
- For a very large source image, resize its longest edge to about 1024 before
  image-to-scene preprocessing to reduce depth-model memory use.

## Model and generation failures

- **First run stalls while downloading**: WorldGen builds DA-2 depth and FLUX
  panorama models lazily. Separate model download failures from inference
  failures and check the hub cache, license acceptance, and free disk space.
- **FLUX license/authentication error**: accept the gated FLUX.1-dev license and
  authenticate with the model hub before retrying. Do not repeatedly restart
  the full scene command while the checkpoint is unavailable.
- **OOM in panorama generation**: lower `resolution`, pass `low_vram=True`, and
  close other GPU consumers. Standard and Nunchaku branches have different
  memory behavior; do not infer success from a CPU import.
- **Sharp import failure**: remove `use_sharp` and confirm the default splat
  path first. Sharp is optional and has its own package and checkpoint.
- **Inpainting import/download failure**: remove `inpaint_bg` until the base
  splat path works. LaMa and segmentation are extra downloads, not part of the
  minimal import check.

## Output and viewer failures

- **`inpaint_bg` plus mesh**: choose either background-inpainted splats or mesh
  output. The bundled launcher rejects this combination because the inpaint
  implementation merges splats.
- **PLY viewer shows black or malformed splats**: confirm the viewer expects
  WorldGen's `SplatFile.save()` format, including RGB DC coefficients, opacity,
  log-scales, and wxyz rotations.
- **Mesh has missing back faces**: use a double-sided mesh viewer or inspect the
  Open3D mesh; some Viser builds cull back faces.
- **Novel-view export writes nothing**: connect a browser client first, create a
  camera path, then click Save Novel Views. The export is a client render loop,
  not an automatic post-processing step.
- **Port 8080 is occupied**: stop the competing Viser process or run the helper
  in an environment where the default port is available. The bundled helper
  currently follows the package's documented local-server behavior.

## Reproducibility

The panorama helpers default to seed `42`, but model weights, torch kernels,
GPU memory, and optional backend versions still affect output. Record the
prompt, input image, mode, resolution, low-VRAM setting, optional flags, and
output path whenever comparing scenes.
