# Inference API and signature notes

Use these prompt-safe notes to adapt LatentSync inference without reopening source files.

## Bundled wrapper: `scripts/run_inference.py`

Primary single-pair options:

```text
--repo-root PATH              LatentSync runtime tree; defaults to LATENTSYNC_REPO_ROOT or current directory.
--config PATH                 U-Net config; default configs/unet/stage2_512.yaml.
--checkpoint PATH             U-Net checkpoint; default checkpoints/latentsync_unet.pt.
--video-path PATH             Input video; default assets/demo1_video.mp4.
--audio-path PATH             Input audio; default assets/demo1_audio.wav.
--output PATH                 Output mp4; default video_out.mp4.
--steps INT                   Diffusion denoise steps; default 20.
--guidance-scale FLOAT        Audio guidance scale; default 1.5.
--seed INT                    Seed; default 1247; use -1 for random torch seed.
--temp-dir PATH               Scratch directory; default temp.
--enable-deepcache            Enable DeepCache with the repo defaults.
--preflight-only              Validate prerequisites and print the planned jobs.
--dry-run                     Print commands without executing them.
```

Small-batch options:

```text
--pairs-file PATH             TSV/CSV/whitespace rows: video, audio, optional output.
--video-list PATH             Text file of videos, paired with --audio-list.
--audio-list PATH             Text file of audios, paired with --video-list.
--output-dir PATH             Directory for generated outputs when batch rows omit output.
--pairing zipped|shuffled     Pair list rows by order or independent shuffle.
--continue-on-error           Continue later batch jobs after a failed subprocess.
```

Safety behavior:

- Resolves relative paths against `--repo-root`.
- Verifies repository markers, config, scheduler config, U-Net checkpoint, required Whisper checkpoint, mask image, video, audio, output parent, ffmpeg, CUDA, and import prerequisites before the first denoise call.
- Rejects path strings containing whitespace or common shell metacharacters by default because downstream video reading and muxing shell out to ffmpeg.
- Executes the repo module with an argument list and `cwd=--repo-root`; it does not invoke `eval/inference_videos.py` with `shell=True`.

## Repo module CLI: `scripts.inference`

`python -m scripts.inference` accepts:

```text
--unet_config_path STR        OmegaConf config path. Source default is configs/unet.yaml; use explicit stage config.
--inference_ckpt_path STR     Required U-Net checkpoint.
--video_path STR              Required input video path.
--audio_path STR              Required input audio path.
--video_out_path STR          Required output mp4 path.
--inference_steps INT         Default 20.
--guidance_scale FLOAT        Default 1.0 in parser; demo shell uses 1.5.
--temp_dir STR                Default temp; deleted/recreated by pipeline.
--seed INT                    Default 1247; -1 means random torch seed.
--enable_deepcache            Enable DeepCache.
```

`main(config, args)` performs these steps:

1. Fails if `args.video_path` or `args.audio_path` does not exist.
2. Chooses `torch.float16` when CUDA is available and device capability major version is greater than 7; otherwise `torch.float32`.
3. Loads `DDIMScheduler.from_pretrained("configs")` from the runtime root.
4. Selects Whisper checkpoint by `config.model.cross_attention_dim`: `384 -> checkpoints/whisper/tiny.pt`; `768 -> checkpoints/whisper/small.pt`.
5. Creates `Audio2Feature(model_path, device="cuda", num_frames=config.data.num_frames, audio_feat_length=config.data.audio_feat_length)`.
6. Loads `AutoencoderKL.from_pretrained("stabilityai/sd-vae-ft-mse", torch_dtype=dtype)` and sets `scaling_factor=0.18215`, `shift_factor=0`.
7. Loads `UNet3DConditionModel.from_pretrained(OmegaConf.to_container(config.model), args.inference_ckpt_path, device="cpu")`, casts to `dtype`, and moves the pipeline to CUDA.
8. Optionally enables DeepCache with `cache_interval=3` and `cache_branch_id=0`.
9. Calls `LipsyncPipeline(...)` with config data fields and runtime parameters.

## Pipeline call surface

`LipsyncPipeline.__call__` key arguments:

```python
pipeline(
    video_path: str,
    audio_path: str,
    video_out_path: str,
    num_frames: int = 16,
    video_fps: int = 25,
    audio_sample_rate: int = 16000,
    height: int | None = None,
    width: int | None = None,
    num_inference_steps: int = 20,
    guidance_scale: float = 1.5,
    weight_dtype = torch.float16,
    eta: float = 0.0,
    mask_image_path: str = "latentsync/utils/mask.png",
    temp_dir: str = "temp",
    generator = None,
    callback = None,
    callback_steps: int | None = 1,
)
```

Important behavior:

- Calls `check_ffmpeg_installed()` before processing.
- Loads the fixed mask with `load_fixed_mask(height, mask_image_path)` and creates `ImageProcessor(height, device="cuda", mask_image=mask_image)`.
- Converts audio to Whisper features, chunks them at the configured video FPS, reads audio at 16 kHz, and reads video frames through OpenCV after ffmpeg FPS conversion.
- If audio is longer than video, loops video frames forward/backward to match audio chunks.
- Detects and affine-aligns the largest suitable face per frame; no CPU face-detection fallback is implemented.
- Runs denoising chunk-by-chunk over `num_frames` frames.
- Restores generated faces into original frames, trims audio length to output frame count, writes temporary video/audio, and muxes with ffmpeg.

## Model and audio helpers

`UNet3DConditionModel.from_pretrained(model_config: dict, ckpt_path: str, device="cpu")`:

- Builds the U-Net from config.
- Loads a checkpoint with `torch.load(..., weights_only=True)` when `ckpt_path` is non-empty.
- Accepts checkpoints that differ in input/output channels or cross-attention shape by deleting incompatible keys before `strict=False` loading.
- Returns `(unet, resume_global_step)`.

`Audio2Feature(model_path, device="cuda", num_frames=16, audio_embeds_cache_dir=None, audio_feat_length=[2, 2])`:

- Uses the bundled Whisper implementation to transcribe audio to features.
- `feature2chunks(feature_array, fps)` maps 50 FPS audio feature indices to video frames.
- Optional audio embedding cache is supported by the class, but `scripts.inference` does not pass cache directories.

## Gradio app surface

The app exposes:

```python
process_video(video_path, audio_path, guidance_scale, inference_steps, seed) -> output_path
create_args(video_path, audio_path, output_path, inference_steps, guidance_scale, seed) -> argparse.Namespace
```

Source defaults:

- Config: `configs/unet/stage2_512.yaml`.
- Checkpoint: `checkpoints/latentsync_unet.pt`.
- Temp/output directory: `temp`.
- Examples: `assets/demo1_video.mp4` plus `assets/demo1_audio.wav`, and demo2/demo3 pairs.
- DeepCache: always enabled for generated Gradio jobs.
- Source launch: `demo.launch(inbrowser=True, share=True)`; use the bundled launcher to override those flags explicitly.

## Batch inference evidence

The repo's batch helper reads separate video and audio file lists, independently shuffles them twice with a fixed seed, writes outputs as `<video_stem>__<audio_stem>.mp4`, and shells out to `python -m scripts.inference --enable_deepcache`. The bundled wrapper preserves the useful file-list idea but replaces the hard-coded private defaults and shell command with explicit arguments and preflight validation.

## Prompt-safety notes

- Never paste untrusted media paths directly into shell command strings; use `scripts/run_inference.py` or build a `subprocess.run([...], cwd=repo_root)` list.
- Do not use `predict.py` as a local CLI. It is a Cog interface with network download and shell-command assumptions.
- Do not score outputs in this sub-skill. Route scoring to the evaluation sub-skill.
