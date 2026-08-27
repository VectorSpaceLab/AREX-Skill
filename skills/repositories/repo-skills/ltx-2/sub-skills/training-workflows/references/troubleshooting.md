# Training Troubleshooting Matrix

Use this reference to recover safely from configuration, launch, runtime, and resume problems. Do not promise that any recovery will improve training quality; these fixes address correctness, resource use, or observability.

## Config and Install Symptoms

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No module named 'ltx_trainer'` | Trainer package is not installed in the current environment or command is not run through the repo's `uv` environment. | Use the documented install flow for the LTX-2 repo, then run through `uv run`. If the task is only command construction, use the bundled command builder and ask the user where LTX Trainer is installed. |
| Typos such as extra config fields or wrong nesting fail validation | Config models use `extra="forbid"`. | Run `validate_training_config.py` and fix the exact field path named by the Pydantic error. Keep `target_modules` under `lora`, not top level. |
| `Model path cannot be a URL` or model path does not exist | `model.model_path` must be a local file. | Download/locate the model through an approved setup path, then patch the local path. Do not put Hugging Face URLs directly in `model_path`. |
| Split transformer reports missing video VAE/audio VAE | `model_path` points at a split LTX 2.5 transformer, which carries no VAE. | Add `video_vae_path` for video-loading runs and `audio_vae_path` for any run touching audio. Use the component files from the same checkpoint pack. |
| Wrong `text_encoder_path` or Gemma version mismatch | Checkpoint and Gemma/text-projection pack do not match. | Use the text encoder requested by checkpoint metadata. LTX 2.5 requires the LTX-specific Gemma 4/text-projection pack, not vanilla Gemma 4 or a Gemma 3 directory. |
| Required data directory missing under `preprocessed_data_root` | Strategy condition uses a latent/mask/reference directory that was not produced. | Route back to `data-preparation` or patch the strategy directory names to match verified preprocessing output. Do not create empty directories as a fake pass before real launch. |
| Audio mode silently has no audio latents | Metadata/preprocessing did not produce `audio_latents/`, or strategy omitted audio. | Stop before training. Verify dataset preprocessing for the selected audio/joint mode through `data-preparation`; then rerun strict config validation. |

## Model-Version and Stale Embedding Issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Training fails after switching LTX-2.3 to LTX 2.5 or vice versa | Cached text embeddings in `conditions/` were generated with the old Gemma/checkpoint pair. | Reprocess into a fresh output directory or rerun preprocessing with overwrite after user approval. Existing `.pt` text features are not interchangeable across Gemma versions. |
| Resume I2V after a version switch starts but validation behaves inconsistently | Checkpoint weights, base model paths, and precomputed features may come from different model families. | Verify `model.load_checkpoint`, base `model_path`, matching text encoder, split VAE paths, and preprocessing timestamp/output root. Prefer fresh preprocessing and an explicit resume/no-resume decision. |

## OOM and Slow Training

| Symptom | First safe fixes |
| --- | --- |
| OOM during training step | Enable `optimization.enable_gradient_checkpointing`; set `batch_size: 1`; increase `gradient_accumulation_steps` if preserving effective batch; use `optimizer_type: "adamw8bit"`; set `acceleration.quantization: "int8-quanto"`; reduce LoRA rank only with user awareness; reduce resolution/frame count only after routing reprocessing through `data-preparation`. |
| OOM during validation but training steps fit | Set `acceleration.load_text_encoder_in_8bit: true`; set `acceleration.offload_optimizer_during_validation: true`; reduce validation `video_dims`; reduce `validation.inference_steps`; increase `validation.interval`; for V2A/audio-only validation set `generate_video: false` if video output is not needed. |
| Slow training | If memory allows, test non-compile vs compile Accelerate configs, disable unnecessary validation frequency, reduce data-loader bottlenecks, and monitor GPU utilization. Do not change resolution or preprocessing without user approval. |
| NaN loss | Prefer `mixed_precision_mode: "bf16"` over fp16; lower learning rate; verify latent decoding through data-preparation/debug tooling; try `quantization: null` if quantized training is unstable; keep `max_grad_norm: 1.0`. |

## Validation Output Debugging

Training-time validation is a monitoring tool. It uses the trainer's validation runner and may not match the production inference pipeline.

| Symptom | Checks |
| --- | --- |
| Audio validation is silent or mismatched | Confirm `validation.generate_audio: true`, audio-generating strategy, `audio_vae_path` for split pack, prompts that describe audio, and existing `audio_latents/`. |
| V2A validation wastes VRAM or crashes decoding video | For Foley/V2A monitoring, set `validation.generate_video: false` and use `video_to_audio` validation conditions. |
| A2V validation condition rejected | Use `conditions: [{type: audio_to_video, audio: "..."}]`; do not combine audio-freezing conditions with other audio-targeting conditions. |
| Reference validation scale is wrong | For video `reference` validation, set `downscale_factor` and `temporal_scale_factor` to match reference preprocessing. Validation encodes files on the fly and cannot infer training reference scale from the dataset. |
| Validation looks poor | Check that the validation recipe matches the checkpoint family, dimensions are VAE-aligned, prompts describe relevant audio/visual content, and target modules match the mode. Do not infer final quality from this alone; hand off production inference to `inference-pipelines`. |

## Checkpoints and Resume

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Existing checkpoints are ignored | `model.load_checkpoint` is null; trainer does not auto-scan `output_dir`. | Patch `model.load_checkpoint` to the desired weights file or checkpoint directory and rerun validation. |
| Weights load but step starts at 0 | Matching `training_state_step_*.pt` is missing/corrupt, `checkpoints.no_resume: true`, or state fingerprint mismatch. | Decide whether the user wants true resume or fresh continuation. For true resume, use matching state, same optimizer/scheduler/training mode/LoRA rank, and `no_resume: false`. |
| Resume warns about optimizer/scheduler/rank mismatch | Config differs from saved state's fingerprint. | Either restore the old settings for true resume or keep the new settings and set `no_resume: true` to load weights fresh. |
| Resume after interrupted save | Latest weights or state file may be incomplete. | Prefer the latest checkpoint with both weights and nonzero matching state. If uncertain, use the previous complete checkpoint. |

## Credentials and External State

| Surface | Recovery |
| --- | --- |
| W&B not logging | Check with `uv run python -c "import wandb; print(bool(wandb.Api().api_key))"`. If false, ask the user to log in or disable `wandb.enabled`. Do not inspect or print tokens. |
| Hub push fails | Verify `hub.push_to_hub: true`, valid `hub_model_id`, write credentials, and network access. Ask before retrying because it writes external state. |
| Network or gated model failure | Treat downloads/auth as setup, not training. Ask the user to accept terms or provide credentials; do not embed tokens in configs. |

## Unsupported Mode

If a user request requires a new loss, new noising rule, novel conditioning mechanism, or additional model output not covered by flexible conditions, stop and use `custom-strategies.md`. Do not choose the nearest mode silently and do not edit trainer code without consent.

## Before Asking the User

Try at most a small number of grounded fixes. If the error remains unclear, report:

- The exact failing command that was attempted.
- The relevant config sections.
- The last error message.
- Which fixes were already tried.
- The next decision the user must make.
