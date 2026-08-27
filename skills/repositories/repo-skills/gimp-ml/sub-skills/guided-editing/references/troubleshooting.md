# Guided Editing Troubleshooting

Use this table after deterministic preflight. The first repair is always to
preserve the input files and make the contract explicit; do not hide a failure
with an automatic resize or inversion.

| Symptom | Likely cause | Recovery |
|---|---|---|
| Inpainting removes the background or preserves the object | Mask polarity is reversed, or the manual/source implementation conventions differ | Preserve the manual's 255-background/0-object input rule. Use a controlled fixture on the actual compatible host to verify observed behavior; report the discrepancy rather than silently inverting the source. |
| Inpainting or matting says layer size is wrong | A layer is offset, cropped, or smaller than the image canvas | In GIMP apply **Layer -> Layer to Image Size** to the image and every participating layer. Re-run the preflight; do not rely on visual overlap. |
| Validator reports shape mismatch | Exported files have different width/height, or one file is a crop | Re-export aligned layers from the same canvas. Never stretch a mask merely to silence the error. |
| Validator reports incompatible channels | A mask is grayscale when RGB is required, channels disagree, or color guidance lacks alpha | For inpainting, use a single channel or consistent RGB. For matting use consistent RGB triplets. For color guidance preserve RGBA. Rewrite the asset and rerun. |
| Trimap contains values other than 0, 128, or 255 | Anti-aliasing, interpolation, or a soft alpha was supplied | Use nearest-neighbor/explicit thresholding to author exact RGB values. `--trimap-tolerance` diagnoses near values but does not make arbitrary values safe for the plugin. |
| Trimap has no gray boundary | There is no unknown region for the matting model | Add a meaningful 128 gray boundary around the foreground, aligned to the image. If the edit intentionally has no unknown region, it is a hard-mask operation, not useful deep matting. |
| Trimap edges look shifted | Trimap and image were independently resized/cropped | Recreate both from the same canvas and apply Layer to Image Size. Avoid bilinear interpolation of label/trimap layers. |
| Face generation rejects or produces nonsensical labels | Original and modified masks are not exact supported palette colors, or a mask was antialiased | Use the faceparse output as the original mask; edit the duplicate with exact palette colors and nearest-neighbor operations. Validate all three layers. |
| Face parser or generator cannot start | GIMP/Python 2 `gimpfu` host is absent, imports are incompatible, or a plugin dependency is missing | Stop at static preparation and report the host limitation. Do not claim a generated face. A compatible host is required. |
| Checkpoint `FileNotFoundError` or state-dict mismatch | Weights are not installed, wrong checkpoint variant, or model/options do not match | Treat as a hard stop. Verify the expected route's checkpoint and configuration through the deployment environment owner; do not download or substitute weights in this skill. |
| CUDA is visible but allocation fails or process OOMs | Device capacity is insufficient or another process owns memory | Select explicit CPU only if the model and checkpoint can load there. Otherwise report device-blocked. Do not interpret `torch.cuda.is_available()` as a successful inference test. |
| CPU fallback still fails | CPU dependencies, RAM, or legacy Python/package versions are incompatible | Preserve the preflight evidence and stop. A modern Python import check is not proof of legacy GIMP plugin execution. |
| Face parsing completes but face generation is unavailable | Parsing and generation have separate checkpoints/model stacks | Keep the parsed mask as a preparation artifact; do not treat parsing as generation or silently use a generic segmentation result. |
| Color guidance has no effect | Mask is fully transparent, points are outside the canvas, or image is single-channel | Keep the image RGB-mode, retain alpha, place visible local RGB points on an aligned layer, and rerun the static check. The optional mask may be omitted for unguided coloring. |
| Color mask appears as a black rectangle | Alpha was dropped during export or the layer was flattened | Export RGBA with transparency and keep the mask as a separate layer. A visual black background is not an optional transparent mask. |
| Output is stretched or cropped | Model preprocessing resized/padded internally or a wrong layer was selected | Compare output dimensions to the original canvas, retain source layers, and inspect the plugin's resize path. Do not use output to excuse input misalignment. |

## Checkpoint and device decision record

For every attempted model route, record:

- operation and input contract result;
- host/runtime status (GIMP, `gimpfu`, Python compatibility);
- checkpoint presence and load result, without embedding private paths;
- requested device and observed allocation/load result;
- whether the result is model-generated, static-only, or blocked.

The known inspection facts for this skill are conservative: Python 3.11 and
common scientific/ML packages imported successfully, while GIMP and Python 2
were unavailable; CUDA was visible but a tiny allocation was blocked by current
host CUDA OOM; and no weights or OpenAI calls may be assumed. Use these facts
to explain why a static contract pass cannot be promoted to a runtime claim.

## Safe validator recovery

The bundled validator reads explicit image files and reports errors without
writing output. If it cannot open an input, check the path, permissions, and
image format. It does not invoke GIMP, network services, credentials, model
weights, or destructive writes. Fix the file or call it with the correct
operation arguments; do not add a hidden auto-repair step.
