# Troubleshooting

Use this reference to diagnose demo and invisible-watermark issues without defaulting to launching UI servers or importing heavyweight modules.

## Demo Dependencies

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: streamlit` | Streamlit demo dependencies are missing. | Explain that UI execution is optional; install UI extras only if the user explicitly wants the demo, or route automation to `../inference-api/SKILL.md` / `../video-sampling/SKILL.md`. |
| `ModuleNotFoundError: gradio` | Gradio community app dependencies are missing. | Treat Gradio files as reference unless the user wants the app. For generation workflows, prefer non-UI video paths. |
| `ModuleNotFoundError: st_keyup` or `streamlit-keyup` | SDXL Turbo demo uses live prompt entry through `streamlit-keyup`. | Install `streamlit-keyup` for UI use, or convert prompt/seed/step settings into direct Turbo sampling/API usage. |
| `ModuleNotFoundError: rembg` | SV4D Gradio background-removal option requires `rembg`. | Disable background removal, preprocess externally, or install `rembg` only for that optional UI feature. |
| `ModuleNotFoundError: cv2`, `imwatermark`, or `invisible-watermark` | Full image watermark decoding dependencies are missing. | If bit counts are already available, use `scripts/watermark_match_thresholds.py`; otherwise prepare the original detector dependencies before decoding images. |

## Checkpoints and Model Loading

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| File-not-found for `checkpoints/*.safetensors` | Required model weights are absent. | Ask the user to confirm license/access and checkpoint location; do not invent checkpoint names beyond the version dictionaries. |
| Gradio app downloads unexpectedly | `gradio_app.py` and `gradio_app_sv4d.py` check/download checkpoints at module import time. | Warn before importing or running those modules; prefer reading source or using non-UI sub-skills for automation. |
| App appears idle until `Load Model` is checked | Streamlit demos keep mode as `skip` until the checkbox is enabled. | Explain that this is intentional to avoid loading models immediately. |
| CUDA error or CPU-only host failure | Demos assume CUDA in many paths and call `.cuda()` or use `torch.autocast("cuda")`. | Do not promise CPU execution. Route to lower-memory options where supported, reduce `decoding_t`, or ask for a GPU-backed environment. |
| Out-of-memory during video/SV4D | Large frame counts, resolution, or decode batches exceed VRAM. | Lower `decoding_t`/`encoding_t`, reduce resolution where supported, use fewer denoising steps for a smoke test, or use a stronger GPU. |

## Ports and Servers

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Streamlit port already in use | Existing server is bound to the requested port. | Choose a different explicit `--server.port` after user confirmation, or stop the existing server. |
| Gradio link/share behavior surprises user | `demo.launch(share=True)` in Gradio apps may expose a share tunnel. | Ask before running share-enabled demos; edit/adapt launch settings only with user approval. |
| Agent session hangs after launch | UI servers are long-running foreground processes. | Run only when requested, with a clear stop plan. Prefer source analysis or API/video routes for normal tasks. |

## Setting Translation Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| User asks to automate a Streamlit SDXL sample | UI state must be mapped into model/config/sampler arguments. | Preserve model version, resolution, prompt, seed, sampler, step count, guidance, img2img strength, refiner choice, and save path; route to `../inference-api/SKILL.md`. |
| User asks to automate `video_sampling.py` | UI state maps to video model version and conditioning fields. | Preserve version, dimensions, frame count, fps, motion bucket, cond_aug, camera trajectory, decoding chunk size, and seed; route to `../video-sampling/SKILL.md`. |
| Output dimensions differ from input | Demo resizes images to multiples of 64 or crops to model-trained size. | Explain the resize/crop rule and capture final H/W explicitly in automation. |
| SV3D camera path is wrong | Elevation/azimuth trajectory settings were lost. | For `sv3d_p`, preserve same-elevation vs dynamic trajectory plus elevation/azimuth sequences. |

## Watermark Detection

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `image too small, should be larger than 256x256` | Full detector cannot decode tiny images. | Use a larger image or classify only if a valid bit count was produced elsewhere. |
| No watermark detected for a generated image | Transformations may have reduced bit recovery, or decoding failed. | Check whether the image was resized, cropped, recompressed, filtered, or converted through video; avoid treating absence as proof. |
| Likely or partial watermark on a real image | Chance matches can occur. | Report the threshold bucket and caveat; only `very likely` had zero false positives in the repository's cited 10,000-image test. |
| Very likely watermark on unrelated content | The watermarking code is public and can be applied by anyone. | State that the result indicates watermark presence, not authoritative source provenance. |
| User only has bit-match counts | Full image decoder is unnecessary. | Use `scripts/watermark_match_thresholds.py` with integer inputs or a JSON list. |
