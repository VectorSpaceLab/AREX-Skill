# Data Preparation Troubleshooting

Use this matrix to diagnose dataset and preprocessing blockers before switching to training, inference, or backend performance work.

## Manifest and path issues

| Symptom | Likely cause | Action |
|---|---|---|
| `No caption column found` | Manifest uses `prompt`, `text`, or another caption name. | Rename to `caption` or pass a caption-column override in the preprocessing command. Validate with `validate_dataset_manifest.py --caption-column YOUR_COLUMN`. |
| `No media column found` | Manifest lacks `video`, `media_path`, or `audio`; or path column is named `file`, `path`, etc. | Rename to `video`/`audio` or pass `--video-column` for target video. |
| Both `video` and `media_path` exist | Ambiguous target media columns. | Keep only one target column or explicitly choose `--video-column`; prefer `video`. |
| Both `reference_video` and `ref_media_path` exist | Ambiguous reference columns. | Keep only one; prefer `reference_video`. |
| Path validation fails | Relative paths are resolved from the manifest directory, not the current shell directory. | Move manifest beside media, rewrite paths relative to the manifest, or use absolute paths intentionally. |
| CSV rows contain blank `nan` paths | Empty cells parsed from CSV. | Fill or remove the row; every required path column must be non-empty. |
| Empty JSON accepted but later fails | JSON must be a non-empty list of objects. | Rewrite as `[{...}]` or JSONL lines. |

## Bucket and media-shape issues

| Symptom | Likely cause | Action |
|---|---|---|
| Width/height multiple error | Bucket dimensions are not divisible by the video VAE spatial factor, usually 32. | Use values like `960x544`, `768x448`, `512x512`, or verify the VAE's actual factors. |
| Frame count error | Bucket frame count does not satisfy `F % T == 1`, usually `F % 8 == 1`. | Choose `1, 9, 17, 25, 33, 41, 49, 57, 65, 73, 81, 89, 97, 121`, etc. |
| Images are skipped or shape mismatch | Mixed dataset lacks an `F=1` bucket. | Add a bucket such as `960x544x1`. Later training must use batch size 1 with multiple buckets. |
| Videos skipped as too short | Clip frame count is below the smallest requested bucket. | Split/filter differently, lower the minimum `F`, or add a shorter valid bucket. |
| Multi-bucket training collate failure | Training batch size greater than 1 with variable shapes. | Route to training-workflows and set training batch size 1; use gradient accumulation for effective batch size. |
| Reference downscale error | Downscale factor does not divide width/height or scaled dimensions are not VAE-aligned. | Use factor 1, 2, or 4 only when dimensions support it; otherwise adjust bucket size. |
| Reference temporal scale error | `(F - 1)` is not divisible by temporal scale, or the resulting frame count is not VAE-aligned. | Pick a compatible frame bucket and scale factor, e.g. `49` with factor `2` gives `25`. |

## Checkpoint layout and preprocessing flags

| Symptom | Likely cause | Action |
|---|---|---|
| Split transformer used without VAE flags | LTX split packs keep VAE weights outside the transformer file. | Add both `--video-vae-path` and `--audio-vae-path` when building preprocessing commands. |
| Audio VAE error during video preprocessing | Auto audio extraction is enabled and the audio VAE cannot be resolved. | Provide `--audio-vae-path` for split packs, or use `--skip-audio` only if the later training mode does not need audio latents. |
| Audio-only preprocessing asks for durations | No video bucket exists to infer audio length. | Add `--audio-durations "2.0;4.0;8.0"` or choose durations appropriate to the dataset. |
| Conditions look incompatible after model switch | `conditions/` were produced with a different Gemma/text encoder. | Use a fresh output root or `--overwrite`; LTX model versions can use different Gemma feature spaces. |
| Existing `.pt` files are reused unexpectedly | Preprocessing resumes by skipping existing outputs. | Use `--overwrite` or a new output directory after changing model, Gemma, trigger, buckets, references, masks, or manifest. |

## Captioning issues

| Symptom | Likely cause | Action |
|---|---|---|
| qwen_omni connection refused | vLLM captioner server is not running or URL is wrong. | Do not start it silently. Ask for approval or switch to an approved Gemini path. |
| qwen_omni cannot fit | Local captioner model is very large. | Route resource planning to performance-backends, or use `gemini_flash` if cloud use is acceptable. |
| Gemini auth error | Missing API key or Google Cloud/Vertex credentials. | Ask user to provide credentials through environment or approved secret handling; never print secrets. |
| Gemini rate limit | Too many parallel calls. | Lower `--num-workers` to 3-5 or retry later. |
| Captions contain hallucinated objects/audio | Multimodal captioners are not ground truth. | Spot-check captions, edit instruction, manually correct manifest, and require approval before bulk captioning. |
| Re-caption does not update rows | Existing captions are skipped. | Use `--override` only after confirming replacement is desired. |

## Reference and mask issues

| Symptom | Likely cause | Action |
|---|---|---|
| Missing `reference_latents/` for IC-LoRA | Manifest lacks `reference_video` or preprocessing did not include it. | Add/validate the column and rerun preprocessing. |
| Reference latents have unexpected shape | Reference downscale/temporal scale flags differ from plan, or stale cache reused. | Inspect shapes; rerun with fresh output or `--overwrite`; align validation/inference scale factors. |
| Reference filenames do not match target names | Outputs align to target media paths when `main_media_column` is target video. | This is expected for process_dataset; compare by relative target names. |
| `video_masks/` missing | Manifest lacks `video_mask`, target `latents/` missing, or stale run skipped. | Ensure target latents exist and rerun with correct manifest. |
| Mask appears inverted | Mask convention misunderstood. | Values `>0.5` are conditioning/clean; values `<=0.5` are generated. Invert source mask if needed before preprocessing. |
| Audio mask warning: no audio latents | `audio_latents/` absent because audio was skipped or not provided. | Rerun preprocessing with target audio enabled and then process masks. |
| Audio latents absent for audio training | `--skip-audio` was used, source videos had no audio, or explicit `audio` paths failed. | Inspect `audio_latents/`; fix sources/flags before training. |

## Multi-GPU shard and resume behavior

| Symptom | Likely cause | Action |
|---|---|---|
| Some ranks report nothing to do | Existing outputs for that rank are already present. | Normal resume behavior if outputs are current. |
| Partial `.tmp.<pid>` files remain | Interrupted atomic save. | They are ignored by skip logic; remove only after confirming no process is running. |
| Re-run after interruption skips many items | Existing `.pt` outputs are treated as complete. | Normal resume behavior. Use `inspect_precomputed_latents.py` to check coverage. |
| Re-run after config change still skips old outputs | `--overwrite` omitted or same output root reused. | Add `--overwrite` or choose a fresh output root. |

## When to route elsewhere

- If the fix is reducing VRAM, changing quantization, tuning VAE tiling, or choosing GPU/device flags, route to `../performance-backends/SKILL.md`.
- If the fix is selecting a training strategy, YAML config, LoRA rank/targets, batch size, optimizer, or launch command, route to `../training-workflows/SKILL.md`.
- If the question is how to use a trained LoRA or inspect generated outputs, route to `../inference-pipelines/SKILL.md`.
