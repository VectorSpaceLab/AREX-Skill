# Cross-Cutting Troubleshooting

## License is unclear

Symptoms:
- The user wants to publish, redistribute, package, or commercially use a model.
- The selected folder has no obvious license file or has a different upstream license from the conversion scripts.

Recovery:
1. Check the selected folder's `LICENSE`, `NOTICE`, `COPYING`, and model-specific note files.
2. Treat the top-level MIT-style conversion-script license and the upstream model artifact license as separate.
3. If the selected folder does not clearly permit the intended use, mark license as unresolved and ask the user for legal approval or a different model.

## Catalog says a format exists but checkout lacks the artifact

Symptoms:
- A catalog entry lists `ONNX`, `OV`, `TPU`, `TFJS`, `CM`, or another flag, but the selected folder has no matching local file.

Recovery:
1. Run `scripts/check_model_folder.py <folder> --json` to confirm local files.
2. Use `model-acquisition` and its `inspect_download_plan.py` helper to inspect `download*.sh` without network execution.
3. Explain that flags indicate upstream availability, while local artifact presence depends on downloads and checkout state.
4. Ask before running any network download.

## Download or Google Drive acquisition fails

Symptoms:
- Google Drive confirmation token, quota, cookie, 404, proxy, or partial archive errors.
- Download scripts create `cookie` files or incomplete model files.

Recovery:
1. Dry-run the script with `model-acquisition`'s parser to identify file IDs, output names, and mutation hints.
2. Re-run only after explicit user approval and enough storage.
3. If quota/auth blocks persist, ask the user for a mirror, browser/manual download, credentials, or an alternate model.
4. Do not commit cookies, credentials, large downloaded files, or partial artifacts unless explicitly requested.

## Optional dependency or backend import fails

Symptoms:
- Missing `tensorflow`, `tflite_runtime`, `onnxruntime`, `openvino`, `cv2`, `coremltools`, TensorRT, TFJS tooling, or EdgeTPU runtime.

Recovery:
1. Route to `inference-demos` for runtime scripts or `conversion-and-deployment` for converters.
2. Install only the selected backend/runtime family, not every optional dependency in the zoo.
3. Check historical script expectations before upgrading major framework versions.
4. Keep the final answer clear about what was actually imported or executed.

## Model shape, dtype, layout, or postprocess is wrong

Symptoms:
- Runtime errors about tensor shape/dtype, incorrect boxes/keypoints/masks, wrong color channels, or missing anchor/postprocess files.

Recovery:
1. Inspect catalog remarks and the selected folder's support files.
2. Classify the runtime script and identify preprocessing: resize, RGB/BGR, normalization, NHWC/NCHW, quantized dtype, batch dimension.
3. Run a minimal tensor-shape smoke test before full visualization or postprocess.
4. Separate core model invocation from postprocess and display.

## Hardware or accelerator proof is missing

Symptoms:
- A response is about EdgeTPU, TF-TRT, GPU, browser WebGL, Raspberry Pi, Myriad/VPU, camera, or CoreML device behavior but only static or CPU checks have run.

Recovery:
1. State that backend proof is blocked until the concrete hardware/runtime is available.
2. Use `conversion-and-deployment` to define the backend preparation and native case.
3. Do not count parser checks, catalog flags, or CPU imports as hardware proof.
4. If the user accepts guidance without runtime proof, mark it as unverified guidance.

## Skill may be stale

Read `repo-provenance.md`. If the current PINTO_model_zoo commit, dirty state, model catalog, numbered directories, or public workflow scripts differ materially from the snapshot, run `refresh-repo-skill` before relying on exact catalog entries or helper assumptions.
