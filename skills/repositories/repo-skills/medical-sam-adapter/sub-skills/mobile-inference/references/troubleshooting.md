# Troubleshooting

| Symptom | Likely cause | Safe action |
|---|---|---|
| `ObjectAwareModel` or detector import fails | The prompt-guided module depends on the compatible Ultralytics runtime/import layout; this optional path was not executed in inspection. | Verify the dependency in the user-selected environment and use the package-qualified layout described in [dependencies and weights](dependencies-and-weights.md). Do not copy vendored trees into this skill and do not “fix” it by installing an unverified latest detector. |
| `No module named mobilesamv2` or relative-import errors | The package was imported as top-level `mobilesamv2`. | Use the repository-qualified route `models.MobileSAMv2.mobilesamv2` in a separately maintained runner. The preflight helper intentionally never imports it. |
| Missing `PromptGuidedDecoder`, `ObjectAwareModel`, or checkpoint file | One of the three explicit local model artifacts is absent, unreadable, or supplied under the wrong path. | Run the wrapper again with existing local files. Confirm the decoder state dict has source-required `PromtEncoder` and `MaskDecoder` entries. Never allow a missing file to trigger a model-name download. |
| `KeyError` for encoder | `mobile_sam`, `efficientvit_l1`, or `efficientvit_l0` is parser-accepted but absent from the standalone source mapping. | Select `tiny_vit`, `sam_vit_h`, or `efficientvit_l2` and provide its compatible checkpoint. Do not substitute a registry key without verifying the builder and state dict. |
| CPU-only request appears to place the model successfully, then fails at `.cuda()` | The source's CPU fallback is misleading; transformed boxes are moved to CUDA unconditionally. | Stop and use CUDA. CPU preflight/import is diagnostic only and cannot validate actual inference. |
| No images or OpenCV returns `None` | `--img_path` is not a directory, files have unsupported extensions, or an image is corrupt/unreadable. | Supply a local directory containing readable `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tif`, `.tiff`, or `.webp` files. Keep detector input as a validated RGB array. |
| Colors or masks look wrong | OpenCV loads BGR while SAM expects RGB. | Convert `cv2.imread` output with BGR→RGB before detector and predictor calls; render the original RGB image/background consistently. |
| Output is overwritten, collision, or permission denied | Source concatenates output directory and filename and may overwrite; output directory is not writable or equals input. | Use a separate writable output directory, run preflight without `--allow-overwrite`, and resolve collisions before a real run. The helper never writes files. |
| CUDA out-of-memory | Image size, feature repetition, or 320-box decoding exceeds available VRAM. | Reduce `--imgsz` only after confirming model compatibility, reduce the implementation's box batch size from 320 with an explicit deviation record, process fewer images, and clear stale allocations. Do not switch to CPU and claim success. |
| Missing output despite no exception | No detector boxes, Matplotlib display/save behavior, or an empty result was not handled. | Treat an empty detector result as a valid no-object case, log it, and save a deliberate empty/annotated result in a maintained runner. Ensure the output directory exists and is writable. |
| `--retina False` still behaves as true | Source uses `type=bool`, where non-empty strings are truthy. | Use the source default or change the maintained parser to a real boolean action and document the adaptation; do not assume the original spelling disables masks. |

## Recovery order

1. Rerun `scripts/run_mobile_samv2.py --help`, then a dry-run with all paths.
2. Fix local path, extension, image, output, and encoder errors before imports.
3. Confirm CUDA availability and the optional detector dependency separately.
4. Check checkpoint architecture/state keys, then run only a small, isolated
   image set with a new output directory.
5. Preserve the traceback and artifact versions if failure remains; do not
   retry by enabling network downloads or falling through to defaults.

For shared environment/checkpoint or route-level failures, consult
[the root troubleshooting guide](../../../references/troubleshooting.md). For
training failures, route to [training](../../training/); for input layout
failures, route to [data preparation](../../data-preparation/).
