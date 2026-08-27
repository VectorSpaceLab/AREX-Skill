# InstructVideo troubleshooting

Use this reference when InstructVideo reward fine-tuning, LoRA inference, base-comparison inference, or WebVid/caption preparation fails.

## Stale eval shell paths

**Symptom:** the original source shell snippet cannot find configs whose names start with `infer_UNetSD...`.

**Likely cause:** the repository's `configs/instructvideo/eval_generate_videos.sh` references stale LoRA filenames. The actual files in the checkout are prefixed with `instructvideo_infer_...`.

**Fix:**

- Use `scripts/run_eval.sh --list-presets` from this sub-skill.
- Choose a preset such as `lora-ddim50-in-domain` or `base-ddim20-in-domain`.
- If you need a custom eval config, pass it with `--config` and keep it in a copied YAML.

## Missing reward or model assets

**Symptom:** `FileNotFoundError`, raw `torch.load` failure, or strict state-dict mismatch before training/eval starts.

**Likely cause:** required ModelScope/InstructVideo assets have not been downloaded or moved into the expected `models/` layout.

**Fix:** verify these paths before a long run:

- `models/model_scope_v1-4_0600000.pth` for the base ModelScope checkpoint.
- `models/instructvideo-finetuned/ddim20_1102-18-52_non_ema_0620000.pth` or another LoRA-compatible fine-tuned checkpoint for LoRA eval configs.
- `models/HPS_v2.pt` for `DiffRewardModel(reward_type="HPSv2")`.
- `models/stable-diffusion-v/open_clip_pytorch_model.bin` for the InstructVideo OpenCLIP embedder.
- `data/stable_diffusion_image_key_temporal_attention_x1.json` for the train config's `Pretrain` block.

Do not substitute DreamVideo, I2VGen, or generic T2V checkpoints unless the config is deliberately rewritten.

## Dependency import failures

**Symptom:** `ModuleNotFoundError` for `piq`, `skimage`, `open_clip`, `fairscale`, `xformers`, `diffusers`, or OpenCV/NumPy ABI errors.

**Likely cause:** the runtime environment is missing reward/model packages or has an incompatible OpenCV/NumPy pair.

**Fix:**

- Install the normal VGen requirements plus `configs/instructvideo/requirements.txt` extras.
- Ensure `piq` and `scikit-image` are available; the reward path imports `piq.ssim`, `SSIMLoss`, and `skimage.metrics.structural_similarity`.
- Use a NumPy 1.x version when OpenCV wheels fail with a NumPy ABI error.
- Keep CUDA PyTorch, torchvision, xformers, open-clip-torch, and fairscale in one compatible environment.

## CPU-only or NCCL failures

**Symptom:** `.cuda()` errors, NCCL initialization failures, or distributed startup hangs.

**Likely cause:** InstructVideo is CUDA-first. The train and inference entrypoints set CUDA devices, use NCCL outside debug mode, and query GPU state.

**Fix:**

- Run on a CUDA-capable host.
- Clear stale `RANK`, `WORLD_SIZE`, `MASTER_ADDR`, and `MASTER_PORT` values if a previous distributed run was interrupted.
- Start with one GPU and a reduced `webvid_test_caps` or small training list while debugging.
- Do not treat a CPU import as proof that reward fine-tuning works.

## WebVid or custom data-list mistakes

**Symptom:** training starts but batches are bad, many clips become zero tensors, or evaluation saves unexpected filenames.

**Likely cause:** the list rows do not match the dataset loader format, the relative paths do not exist under `vid_reward_dataset.data_dir_list`, or the eval caption file has the wrong number of fields.

**Fix:**

- Training rows: `relative_video_path|||caption text`.
- Eval rows: `video_or_placeholder.mp4|||caption text|||frame_count`.
- Do not include `|||` inside captions.
- Keep enough readable frames for the configured `frame_lens` and `sample_fps`.
- In copied YAMLs, edit `vid_reward_dataset.data_list` and `vid_reward_dataset.data_dir_list` together.

## LoRA/base checkpoint mismatch

**Symptom:** `load_state_dict` fails, LoRA merge fails, or output looks like the wrong model family.

**Likely cause:** `UNet.use_lora` does not match the selected checkpoint family.

**Fix:**

- Use LoRA eval presets for checkpoints saved with LoRA keys.
- Use base presets for `models/model_scope_v1-4_0600000.pth`.
- If comparing multiple checkpoints, keep separate copied YAMLs with explicit `infer_checkpoint` and `UNet.use_lora` values.

## Reward fine-tuning OOM

**Symptom:** CUDA out-of-memory during autoencoder decode, partial DDIM sampling, reward scoring, or backward.

**Likely cause:** reward fine-tuning keeps more tensors live than plain inference.

**Fix:**

- Keep `chunk_size: 1` and `decoder_bs: 1` while debugging.
- Reduce batch sizes for 16-frame clips before increasing frame count.
- Keep `use_fp16: True` and `reward_precision: 'fp16'` on supported hardware.
- Use a small filtered training list before scaling to a larger WebVid subset.

## Reward over-optimization

**Symptom:** reward scores improve while generated videos become visually repetitive, over-smoothed, or less aligned with general prompts.

**Likely cause:** the InstructVideo docs warn that reward fine-tuning can over-optimize.

**Fix:**

- Evaluate periodically on in-domain, new-animal, and non-animal caption sets.
- Compare against base ModelScope eval presets.
- Stop or roll back to an earlier checkpoint when generalization degrades.
- Track `starting_partial`, `truncated_backprop`, `segments`, and `selection_method` in run notes so failed experiments are reproducible.

## CLI override type mistakes

**Symptom:** a YAML run works, but the same change through positional CLI overrides fails later with type errors.

**Likely cause:** the VGen config parser forwards many CLI overrides as raw strings.

**Fix:**

- Use CLI overrides only for string-safe paths such as `infer_checkpoint`, `webvid_eval_text`, or `webvid_dir_save`.
- Copy and edit YAML for booleans, integers, floats, lists, and nested dict fields.
- Use the bundled wrappers' `--dry-run` to inspect the command before launch.
