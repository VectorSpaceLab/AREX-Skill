# Cross-Modal Generation Troubleshooting

## Purpose

Read this when ImageBind/StableUnCLIP generation or StyleGAN/DragGAN editing fails before, during, or after a tool call. The table focuses on symptoms a future agent can diagnose without importing heavy models.

## ImageBind and StableUnCLIP failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| The user asks for audio+text generation but only an audio-to-image tool appears available. | The normal app creates `Audio2Image`, `Thermal2Image`, `AudioImage2Image`, and `AudioText2Image` as template wrappers only when the `Anything2Image` foundation object is loaded. | Plan to load the foundation `Anything2Image` for the service. Do not instantiate a wrapper as if it were an independent device-only model; wrappers expect the shared foundation object. Route exact `--load` edits to the app-deployment sub-skill. |
| No ImageBind generation tools appear after launch. | `Anything2Image` was omitted from the load plan, failed during model initialization, or failed while downloading/loading StableUnCLIP or ImageBind. | Verify the load plan includes the foundation object, confirm the runtime can access/download or cache the StableUnCLIP and ImageBind weights, and check CUDA availability. Use energy-saving mode for memory pressure, but do not treat it as proof that the model can fit during inference. |
| A path-related exception or no output occurs for audio or thermal generation. | The provided local file path is missing, points to a directory, or has an unexpected extension. | Run `python scripts/validate_multimodal_assets.py --audio ./sound.wav` or `python scripts/validate_multimodal_assets.py --thermal ./thermal.jpg` from this sub-skill directory. Replace the path with a real local file accepted by the running app. |
| `AudioImage2Image` fails with a split/unpack error. | Its input grammar is exactly `image_path,audio_path`; missing commas, extra commas, or comma-containing filenames break the simple split. | Validate with `python scripts/validate_multimodal_assets.py --tool AudioImage2Image --tool-input "./image.jpg,./sound.wav"`. Rename files to avoid commas or pass paths with exactly one separator comma. |
| `AudioText2Image` produces an empty prompt or wrong audio path. | It treats the first comma as the divider between the audio path and prompt. | Use `audio_path,prompt`. Later commas are allowed inside the prompt, but the audio path itself should not contain a comma. Validate with the bundled script before tool invocation. |
| Generation starts but CUDA runs out of memory. | StableUnCLIP plus ImageBind and any other loaded tools exceed available VRAM. Full-feature launches load many models. | Reduce the load plan to only the needed foundation, enable energy-saving mode, close other GPU workloads, or run the workflow on a larger GPU. Do not run general image/video/Husky tools just to test ImageBind readiness. |
| Model download or cache errors appear. | StableUnCLIP and ImageBind are large external model assets; the runtime may lack network/cache access or have partial downloads. | Use the app-deployment sub-skill for global model-zoo/cache placement. For this sub-skill, record that generation is blocked until model assets are present; do not attempt repeated downloads without user approval. |
| Thermal-to-image gives poor semantic results despite valid paths. | Thermal inputs are image files but must contain meaningful thermal modality content. Ordinary RGB images with a thermal filename are not equivalent thermal data. | Confirm the file is a real thermal image or use an ordinary image-generation/visual workflow in the visual-dialogue sub-skill instead. |

## DragGAN and StyleGAN failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Chat shows `Please load StyleGAN!`. | The service did not load the StyleGAN foundation model for the DragGAN tab. | Route launch changes to app-deployment and load the StyleGAN model before using `New Image` or `Drag It`. |
| Chat shows `Please click the button New Image`. | DragGAN state is absent or was cleared. | Click `New Image` to generate a fresh StyleGAN sample and initialize latent/noise/F state before selecting points. |
| Chat shows `Please click the image`. | No start points were selected. | Click a start point on the generated image, then click its matching target/end point. |
| Chat shows `Start points ... can not match end points ...`. | The number of start and end points differs. | Add the missing paired point if the intended pair is clear, or use `Clear Points` and recreate all pairs. The app alternates start then end; the manual describes blue as start and red as end. |
| Points are overlaid incorrectly after several edits. | The controller updates start/handle points during optimization, so old visual assumptions can become stale. | Use the current preview as authoritative. Clear and recreate points if the intended correspondence is ambiguous. |
| No final MP4 or final image appears. | The optimizer has not reached `max_iters`, stopped early due to runtime failure, or ran out of GPU memory. | Watch the progress value. If it stops before the requested max iteration count, inspect CUDA errors and reduce iterations or image/model load. |
| StyleGAN checkpoint load fails. | The expected StyleGAN2 checkpoint is absent, named differently, incompatible, or unreadable. | Ensure the default FFHQ checkpoint named by the runtime is installed where the app expects model checkpoints. Do not assume commented checkpoint variants are available. |
| Custom op or extension import/build fails. | DragGAN/StyleGAN implementations often require CUDA-compatible custom operations matching the installed PyTorch/CUDA versions. | Use a runtime environment with compatible CUDA, PyTorch, compiler, and prebuilt or buildable custom ops. If compilation is required, keep it out of this safe validation sub-skill and obtain user approval before changing the environment. |
| CUDA out-of-memory during DragGAN. | 1024px StyleGAN2 generation/editing and history/video accumulation can be memory intensive. | Run only the DragGAN tab and StyleGAN foundation, enable energy-saving mode, reduce max iterations for quick checks, close other GPU jobs, or use a larger GPU. |

## When to stop

Stop and report a runtime block instead of retrying blindly when the next action would require downloading large model weights, starting Gradio, compiling CUDA extensions, changing package versions, using credentials, or running full GPU inference outside the user's confirmed environment.
