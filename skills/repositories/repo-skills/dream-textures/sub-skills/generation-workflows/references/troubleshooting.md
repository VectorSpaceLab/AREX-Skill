# Generation workflow troubleshooting

## Quick triage

1. Identify the task that DreamPrompt will emit: `PromptToImage`, `ImageToImage`, `DepthToImage`, `Inpaint`, `Outpaint`, or `Upscale`.
2. Check that the selected model type matches the task. Model acquisition and checkpoint import route to setup.
3. Check image availability: source image, depth map, ControlNet image, inpaint alpha/prompt mask, or upscaling input.
4. Check size/tile/origin bounds before running a heavy backend call.
5. Prefer safe bundled scripts for JSON and outpaint math before opening Blender.

## Symptom map

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Generate` button disabled | Backend validation failed or generator actor cannot be used. | Look for fix-it message in the Actions panel; choose a compatible model; route backend startup issues to setup/backend troubleshooting. |
| `No model selected.` | `DreamPrompt.model` does not match an installed/listed model. | Select a model in the Dream panel. If the model is missing, route to setup-and-models. |
| `Incorrect model type selected for ... tasks` | Task/model mismatch. | Prompt/image-to-image needs prompt-to-image model; depth modes need depth model; inpaint/outpaint need inpainting model; upscale needs x4 upscaler. |
| Size or CUDA/VRAM errors | Width/height too large, too many steps/iterations, accurate preview, large batch, high tile size, or insufficient memory optimizations. | Start at 512x512 for generation; use 64-pixel increments; lower size/steps/batch; use `Fast` or `None` preview; enable attention slicing/CPU offload/half precision where supported; release cached generator. |
| Image output changes despite same text seed | Text seeds are hashed by Python process, not guaranteed stable across sessions. | Use numeric seed values and recall history. Treat history's stored result seed as authoritative. |
| Random seed cannot reproduce expected image | `random_seed=True` uses an automatically chosen seed and writes it after generation. | Recall/export the history entry and use the stored numeric `seed` with `random_seed=False`; also match scheduler, steps, CFG, model revision, size, seamless axes, and backend optimizations. |

## Source image failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Source modify/inpaint/outpaint uses no image | `init_img_src=file` has no `Init Image`, or `open_editor` cannot find an unpinned/open Image Editor image. | Choose a file image datablock or open/select the image in an Image Editor. |
| Image-to-image ignores requested size | `fit` is disabled. | Enable `Fit to width/height`, or accept source-native dimensions. |
| Depth mode asks for or downloads depth assets | `depth_generated` uses a depth estimator; depth modes require a depth model. | Use `color` mode if depth is not required; use `depth_map` with an existing map; route model/dependency acquisition to setup. |
| Colors/depth look wrong in `depth` or `depth_map` mode | Source image was interpreted as grayscale depth; color-space may not match expectations. | Use actual grayscale depth maps; use `color` or `color and generated depth` when color guidance should remain. |

## Inpaint and mask failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Inpaint fills wrong region | Alpha channel mask is inverted/unexpected or prompt mask threshold is poor. | For alpha masks, erase/mark only the intended region with the inpaint brush. For prompt masks, adjust `Mask Prompt` and `Confidence Threshold`. |
| Prompt mask fails before diffusion | CLIPSeg/transformers model `CIDAS/clipseg-rd64-refined` unavailable, no network/cache, or dependency mismatch. | Use alpha-mask source for offline deterministic work; route dependency/cache repair to setup. |
| Seamless repair still shows edges | Seamless axes off/incorrect, mask did not cover seams, or source image was not detected as seamless. | Explicitly set `Seamless Axes` to `Both` for tiling textures; mask the borders; use an inpainting model; lower strength if too much texture changes. |
| `Replace` slider appears ineffective | Source generation path primarily consumes `strength`, mask source, prompt, and confidence. | Diagnose with `strength`, mask source, and model type first; do not rely on `Replace` as a portable backend parameter. |

## Outpaint origin and overlap failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Outpaint origin X/Y must be between ...` | Origin coordinate outside valid bounds. | Run `scripts/plan_outpaint_origin.py`; ensure `-tile_width <= x <= source_width` and `-tile_height <= y <= source_height`. |
| UI warns `Outpaint has no overlap, so the result will not blend` | Tile starts completely outside source bounds on at least one axis. | Use positive overlap, e.g. 64 pixels for a 512 tile. Avoid origins equal to `source_width`, `source_height`, `-tile_width`, or `-tile_height` unless unrelated extension is intended. |
| Outpaint extends wrong side | Origin is the tile's top-left coordinate relative to the original image, not a direction enum. | Use the planner with `--region`; inspect reported tile rectangle and overlap rectangle before entering values. |
| Bottom-right recipe seems not diagonal | The documented `(448,448)` for a 512x960 source and 512 tile extends the right edge while aligned to the bottom. | To grow both below and right, use sequential passes or planner `--strategy outside` and accept lower/edge overlap trade-offs. |
| Outpaint result unrelated to original | No overlap or too little overlap; model/prompt too different. | Increase overlap, keep prompt close to the source material/style, and use an inpainting model. |

Example validation:

```bash
python scripts/plan_outpaint_origin.py --source-size 512x960 --tile-size 512x512 --overlap 64 --region bottom-right
```

## ControlNet and processor failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| ControlNet entry has no effect | Entry disabled, no control image, processor not baked/processed, or ControlNet not applied to the selected task path. | Enable the entry; select a control image; use the bake button for processors; prefer prompt/image-to-image/inpaint paths for ControlNet. |
| Missing ControlNet model | No installed model with ControlNet type. | Route to setup-and-models to download/import a ControlNet model compatible with the base model family. |
| Processor fails | `controlnet_aux` dependency/model unavailable or processor not supported on the active device. | Use processor `none` with a precomputed control image; bake in an environment with needed dependencies; route dependency repair to setup. |
| Control image size mismatch | ControlNet preprocessing rounds/reshapes to a size compatible with the generated image. | Use source/control images with similar aspect ratio and set explicit generation size; inspect output for stretching. |
| Multiple ControlNets produce unexpected style/composition | Conditioning scales too high or models conflict. | Start with one ControlNet at scale 1.0, then add entries gradually and lower scales. |

## Upscaling failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No open image in the Image Editor space, or selected Image Texture node.` | Upscale source selection found no selected Image Texture node and no open Image Editor image. | Select a `ShaderNodeTexImage` with an image, or open the target image in an Image Editor. |
| Upscale button says huge output size and fails | Source image too large for x4 tiling memory/time. | Reduce source resolution before upscaling, lower tile size, keep batch size 1, and use memory optimizations. |
| Visible seams after upscaling | Blend too low or seamless axes not set for a tileable input. | Increase `Blend`; set `Seamless Axes` to the correct axes; keep tile size reasonable. |
| Large tile size warning | Tile size above 128 consumes more VRAM. | Use 128 as the safe starting point; only raise if GPU memory is available. |
| Wrong model type for upscale | Selected model is not the x4 upscaler. | Select/download/import `stabilityai/stable-diffusion-x4-upscaler` or equivalent upscaler model; route setup issues to setup-and-models. |

## Prompt history JSON failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Import does nothing | File extension is not `.json`, root is not an object, keys are unknown to current `DreamPrompt`, or values are `null`. | Use `.json`; validate with the bundled script; check key spellings. |
| Imported prompt loses source/control images | Blender image pointer fields are not portable JSON assets. | Re-select images, depth maps, control images, and text datablocks in Blender after import. |
| Unknown scheduler or preview mode | Edited JSON uses enum names instead of display strings, or values from another version. | Use scheduler display strings such as `DPM Solver Multistep`; validate before import. |
| Negative prompts missing in file batch | Built-in file batch uses blank negative lines and hides Negative panel. | Use separate regular generations for per-prompt negatives, or edit/recall each history entry after generation. |
| Strict validator rejects future keys | Dream Textures version may have added fields. | Run validator without `--strict` for warning-only unknown keys, then inspect source/version before importing. |

Validate prompt JSON safely:

```bash
python scripts/validate_prompt_history_json.py prompt.json --strict
```

## Seamless detection issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Auto-detect` shows `Processing` for a long time | Generator actor busy/unavailable or detector dependencies unavailable. | Set axes explicitly (`off`, `x`, `y`, `xy`) for the next run; route actor/dependency issues to backend/setup. |
| Auto-detect returns `Off` for a tiny image | Images smaller than 8x8 are not processed. | Use larger source images or set axes explicitly. |
| Auto-detect conflicts with intended texture tiling | Detector uses edge evidence/history; creative edits can change continuity. | Set `Both` explicitly for texture generation/repair when tiling is required. |
| Recalled image sets unexpected axes | Image hash matched a prior history entry with concrete axes. | Inspect/export the history entry and edit `seamless_axes`; validate JSON if importing. |
