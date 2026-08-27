# Troubleshooting Training and Postprocessing

Use this guide when textual inversion, hypernetwork training, preprocessing, extras upscaling, or face restoration fails after request transport has already been proven.

## Fast Triage

1. Read the endpoint `info` string; training endpoints can return HTTP 200 while embedding an `error:` message.
2. Identify whether the failure occurs before validation, during dataset preparation, during the training loop, during asset/model lookup, or during image serialization.
3. Route transport/base64/auth/client timeout issues to `../api-automation/SKILL.md` and launch/device/server setup issues to `../launch-and-config/SKILL.md`.
4. Avoid rerunning a long job unchanged; reduce steps, disable previews/saves, and validate paths first.

## Training Create Failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `file ... already exists` | `overwrite_old` is false and the target asset exists | Confirm replacement intent or choose a new name. |
| `Name cannot be empty!` | Hypernetwork name sanitized to empty | Use letters, numbers, spaces, `.`, `_`, or `-`. |
| Create embedding fails before file creation | No loaded model or condition stage unavailable | Confirm a checkpoint is loaded; route model selection to `../assets-and-models/SKILL.md`. |
| New embedding not selectable | Discovery cache stale or creation failed | Refresh embeddings or inspect the returned `info` string. |

## Training Validation Failures

| Symptom | Backend assertion | Action |
| --- | --- | --- |
| `embedding not selected` or `hypernetwork not selected` | Train target missing | Create/select the asset first; refresh discovery lists. |
| `Learning rate is empty or 0` | Empty or zero learning-rate field | Provide a non-zero learning-rate string/number. |
| `Batch size must be integer` or `positive` | Bad `batch_size` | Use a positive integer, usually `1` for first validation. |
| `Gradient accumulation step must be integer` or `positive` | Bad `gradient_step` | Use a positive integer; start with `1`. |
| `Dataset directory is empty` | Missing or empty `data_root` | Point to a non-empty image dataset directory. |
| `Dataset directory doesn't exist` | Invalid `data_root` | Correct the path in the running server's environment. |
| `Prompt template file not selected` | Empty `template_filename` | Use a known template such as `style_filewords.txt`. |
| `Prompt template file ... not found` | Template not loaded in WebUI | Refresh template list or choose a built-in template name. |
| `Max steps must be positive` | Bad `steps` | Use a positive integer; start low for smoke tests. |
| `Log directory is empty` | Save/preview interval enabled without logs | Provide a log directory or set save/preview intervals to `0`. |

## Dataset Preparation Failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `No images have been found in the dataset.` | Files exist but are unreadable/non-images, or all reads failed | Verify image formats and permissions; test with one known-good PNG/JPEG. |
| Captions not reflected in prompts | Missing same-stem `.txt` files or wrong template | Use a `_filewords` template and confirm sidecar captions exist. |
| Prompt uses filename noise | No caption sidecar and filename cleanup settings are not enough | Rename files or create `.txt` captions before training. |
| Out-of-memory during preparation | Latent encoding large images/batches | Lower width/height, disable variable size, reduce batch/gradient, or adjust launch/device settings. |
| Job stuck at `Preparing dataset...` | Dataset latent encoding is still running | Poll progress/state, wait for small datasets, or interrupt before changing plan. |

## Long-Run Training Failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `Model has already been trained beyond specified max steps` | Saved asset step is already >= requested steps | Increase `steps`, choose a fresh asset, or intentionally resume from current step. |
| Preview images fail but training starts | Preview txt2img settings, sampler, or output path issue | Disable `create_image_every` and previews until core training works. |
| Periodic saves fail | Log directory/output permissions or existing file conflict | Use a writable log directory and verify free disk space. |
| Training slows severely | High resolution, variable-size buckets, random latent sampling, caption shuffle/dropout, previews, or low VRAM | Reduce image size, use `once` latent sampling, lower intervals, and avoid concurrent jobs. |
| Interrupt appears ignored | Loop checks interrupt between batches/steps | Poll progress and wait; restart only after confirming the state did not end. |
| Hypernetwork training leaves generation behavior changed | Loaded hypernetwork state was changed during training | Reload/clear hypernetworks after training before generation tests. |

## Preprocessing Plan Failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Validator says `source_dir` missing | Plan cannot identify inputs | Add `source_dir` with the intended dataset input directory. |
| Validator says `output_dir` equals `source_dir` | In-place overwrite risk | Use a separate output directory or explicitly set overwrite intent only after backup. |
| Split/focal crop requires target size | The operation needs target dimensions from resize/upscale | Add `target_width` and `target_height` or an earlier target-size operation. |
| Caption operation warns about models | BLIP/DeepBooru may need model downloads/backend state | Confirm captioning model availability or skip captioning. |
| Face restoration/upscale warns about model prerequisites | Upscaler/restorer weights are not guaranteed present | Query runtime lists and route asset setup to `../assets-and-models/SKILL.md`. |

## Extras and Postprocessing Failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `could not find upscaler named ...` | Payload name not in the running upscaler list | Query `/sdapi/v1/upscalers` and use an exact `name`. |
| Empty or missing response image | `show_extras_results` false, save-only flow, or request mode mismatch | Enable results for API workflows and verify single vs batch endpoint. |
| Base64 decode/encode error | Transport payload issue | Route to `../api-automation/SKILL.md`. |
| Face restoration no-ops | Visibility is `0`, script disabled, or no face detected | Set visibility > 0 and confirm model/restorer availability. |
| Face restoration errors | GFPGAN/CodeFormer weights or imports missing | Route model/asset setup to `../assets-and-models/SKILL.md`. |
| Batch skips files | Unreadable inputs or interrupted state | Test one file, inspect logs, and avoid continuing after interrupt. |
| Output files overwrite or surprise location | WebUI output settings, original-name batch setting, or chosen output dir | Make output directory explicit and confirm naming policy before batch runs. |

## Restart and Recovery Guidance

- Prefer `/sdapi/v1/interrupt` for active training/extras jobs before restarting a server.
- After an interrupted or failed long job, refresh embedding/hypernetwork lists and inspect whether partial save files were created.
- When an API client timed out, assume the server may still be running the job until progress/state proves otherwise.
- After changing checkpoints, embeddings, hypernetworks, or face restoration assets, refresh the corresponding runtime lists before retrying.
