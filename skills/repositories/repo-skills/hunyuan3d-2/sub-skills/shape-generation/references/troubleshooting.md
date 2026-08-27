# Shape Generation Troubleshooting

## Real generation needs CUDA and weights

The prepared environment verified CUDA import/allocation and custom extension readiness, but full model examples were not run by default because they can download large Hugging Face checkpoints and take substantial GPU time. Treat full generation as requiring:

- CUDA-capable PyTorch.
- Model subfolders cached locally or network access to Hugging Face.
- Enough VRAM: repository docs quote roughly 6 GB for shape generation, but high resolution, multiview, or concurrency may need more.

## Model path and subfolder failures

Symptoms:

- `FileNotFoundError: Model path ... not found`.
- Long or unexpected network download.
- A base model loads when a turbo/multiview model was intended.

Fixes:

1. Check exact pairings: `tencent/Hunyuan3D-2mv` must use `hunyuan3d-dit-v2-mv*`; `tencent/Hunyuan3D-2mini` must use `hunyuan3d-dit-v2-mini*`.
2. For offline runs, populate `${HY3DGEN_MODELS:-~/.cache/hy3dgen}/<repo-id>/<subfolder>` before calling `from_pretrained()`.
3. Remember that FlashVDM may also load a VAE turbo subfolder.

## Input image issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Subject geometry includes background | Input lacks clean alpha or background remover was skipped. | Use RGBA cutouts or run `BackgroundRemover` on RGB inputs. |
| Multiview call fails or produces poor alignment | Wrong model or view dictionary. | Use `tencent/Hunyuan3D-2mv` and keys `front`, `left`, `back`, `right`; provide the most reliable `front` view. |
| Fully transparent or empty crop | Bad input alpha. | Inspect image alpha before background removal; use an image with a centered visible subject. |

## CUDA memory failures

Reduce cost in this order:

1. Use turbo/mini variant when acceptable.
2. Lower `octree_resolution` from 384 to 256 or 196.
3. Lower `num_chunks` during export.
4. Reduce concurrent server jobs or run one generation at a time.
5. Clear stale GPU memory between attempts.

Do not fall back to CPU and claim equivalent support. CPU generation was not verified for this skill and is not a full substitute.

## FlashVDM failures

- Use turbo DiT subfolders with `enable_flashvdm()`.
- Try `pipeline.enable_flashvdm(mc_algo="mc")` if the default marching-cubes path fails.
- FlashVDM VAE replacement depends on the model repo name ending in `Hunyuan3D-2`, `Hunyuan3D-2mv`, or `Hunyuan3D-2mini`. Local model directory names outside that pattern may need explicit VAE handling.

## `pymeshlab` / OpenGL warnings during cleanup

Postprocessors use pymeshlab. On headless Linux a warning like `libOpenGL.so.0: cannot open shared object file` means the OpenGL runtime library is missing from the active environment. Install an OpenGL runtime package for the environment and ensure its library directory is visible to the process.

## Export problems

- Use `.glb` for portable single-file outputs.
- If `trimesh.load()` returns a `Scene`, concatenate or export directly depending on the downstream tool.
- For very large meshes, reduce face count with `FaceReducer(max_facenum=...)` before sending to texture, Blender, or web APIs.

## Stale documentation warning

Some source documentation pages in the distilled checkout were stale placeholder pages unrelated to Hunyuan3D. Prefer the README-derived and source-verified guidance captured in this skill for Hunyuan3D-specific shape workflows.
