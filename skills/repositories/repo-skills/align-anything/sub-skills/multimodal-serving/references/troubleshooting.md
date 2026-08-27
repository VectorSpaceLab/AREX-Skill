# Multimodal Serving Troubleshooting

Use this when `load_pretrained_models`, a Gradio CLI, media decoding, chat formatting, or generation fails.

## Fast triage

1. Run the import/dry-run checker:

   From this sub-skill directory:

   ```bash
   python scripts/check_model_loading.py \
     --model-name-or-path "$MODEL_NAME_OR_PATH" \
     --preset text \
     --no-load
   ```

2. If imports pass, run a real load with a small compatible model or cached target model.
3. Confirm the chosen CLI matches the model capability:
   - text-only/chat model -> text CLI;
   - single image/audio/video processor path -> multimodal CLI with matching `--modality`;
   - MiniCPM-O-style mixed media -> omni CLI.
4. Reduce variables: one file, one prompt, shorter generation, explicit dtype, one device.
5. Check the tables below for the first failing layer.

## Import and optional dependency failures

| Symptom | Likely cause | Action |
|---|---|---|
| `ModuleNotFoundError: librosa` | Base runtime dependencies are incomplete. Audio and even package config imports may need `librosa`. | Install align-anything with runtime dependencies in the active environment. For audio, also ensure `soundfile` and codec libraries work. |
| `ModuleNotFoundError: gradio` | Serving UI dependency missing. | Install/repair the package runtime dependencies before launching CLIs. |
| `ModuleNotFoundError: av` or PyAV decode errors | Video CLI uses PyAV/FFmpeg for sampling. | Install PyAV and a compatible FFmpeg stack; re-encode problematic videos to a common H.264/AAC MP4. |
| `ModuleNotFoundError: moviepy` | Omni video chunking uses MoviePy. | Install the MiniCPM-O optional dependencies or avoid omni video input. |
| `ModuleNotFoundError: decord` | Qwen2-VL-style video utility prefers decord when available but can fall back. | Install `decord` or set `FORCE_QWENVL_VIDEO_READER=torchvision` for that utility path. |
| `ModuleNotFoundError: pytorchvideo` | The generic audio processor optional path uses `pytorchvideo`. | Install the text-to-audio optional dependency only if using that processor path. |
| Importing align-anything fails before serving code runs | Top-level package imports dataset/template utilities and may surface missing media deps early. | Fix the first missing dependency rather than assuming the serving module is broken. |

## Model loading failures

| Symptom | Likely cause | Action |
|---|---|---|
| `OSError`/HTTP/auth error while loading model | Bad model id/path, missing cache, private Hugging Face model, or network blocked. | Verify `MODEL_NAME_OR_PATH`, login/token/cached files, and `cache_dir`. Use a tiny public compatible model for smoke checks when possible. |
| Prompt asks for `trust_remote_code=True` | Model repo defines custom code or align-anything wrapper requires remote code. | Enable `--trust-remote-code` only for trusted model sources. |
| MiniCPM-V/O wrapper fails before class construction | Remote wrapper reads `MODEL_NAME_OR_PATH` from the environment. | Export `MODEL_NAME_OR_PATH` before loading. The bundled scripts do this automatically. |
| `KeyError: 'ZERO_STAGE'` with MiniCPM-V | MiniCPM-V wrapper reads `ZERO_STAGE` directly. | Set `ZERO_STAGE=0` for serving unless a distributed launcher sets another supported value. |
| `MiniCPM-V does not support ZeRO stage 3` | Unsupported distributed stage for MiniCPM-V. | Use `ZERO_STAGE=0/1/2` for serving; avoid stage 3. |
| `MiniCPM-O does not support ZeRO stage 2` | Unsupported distributed stage for MiniCPM-O. | Use `ZERO_STAGE=0/1/3` as appropriate; for ordinary CLI serving use `ZERO_STAGE=0`. |
| `ValueError` involving BNB without LoRA | Loader rejects bitsandbytes-only with DeepSpeed. | Use LoRA+BNB together or avoid BNB for this loading path. |
| Reward model plus quantization/LoRA path fails unexpectedly | The score-model registry expects a `modality` kwarg in normal loading; some advanced loader branches may not pass it. | First verify reward loading without BNB/LoRA. If advanced loading is required, adapt the call so `modality` is passed consistently. |
| Tokenizer/model vocabulary warnings | Loader resizes token embeddings when pad/special tokens differ. | Usually informational. If generation quality is poor, confirm tokenizer and model checkpoints match. |
| Processor is `None` | The model lacks an `AutoProcessor` or processor load failed. | Use text CLI for text-only models. Multimodal CLI requires a working processor. |

## Device, dtype, and memory failures

| Symptom | Likely cause | Action |
|---|---|---|
| CUDA out-of-memory at load | Model too large for one device or dtype too wide. | Try `--auto-device-mapping`, reduce model size, use `float16`/`bfloat16` as supported, free other GPU memory, or choose a sharded/offload setup. |
| CPU load is extremely slow or crashes | Large model loaded without accelerator. | Use CPU only for import/dry-run checks or tiny models. Full multimodal generation usually needs accelerator memory. |
| `bfloat16` unsupported or produces dtype errors | Hardware/backend does not support BF16. | Use `--dtype float16` on CUDA GPUs that support FP16, or `--dtype float32` on CPU. |
| `float16` CPU errors | Many CPU kernels do not support FP16. | Use `--dtype float32` for CPU smoke loads. |
| Cross-device tensor error during multimodal generation | Processor tensors are moved to `model.device`, which can be insufficient with `device_map="auto"`. | Try single-device loading for smaller models, a model-specific device map, or an offload strategy supported by Transformers. |
| NPU/XPU/MPS selected but generation fails | Device utility can select those backends, but dependencies/dtypes may not match. | Confirm backend-specific PyTorch packages and dtype support. Treat CUDA verification as not transferable to other accelerators. |

## CLI and Gradio failures

| Symptom | Likely cause | Action |
|---|---|---|
| CLI starts but exposes a public share link | Packaged CLIs call `launch(share=True)`. | Use only in trusted sessions. If a private local UI is required, copy the launcher pattern and change the Gradio launch arguments in a local wrapper. |
| Port/server binding fails | Gradio server conflict or blocked network. | Set Gradio environment variables such as `GRADIO_SERVER_NAME` and `GRADIO_SERVER_PORT`, or stop the conflicting process. |
| Text CLI raises `AttributeError: chat` | Model does not implement `model.chat(messages=..., tokenizer=...)`. | Use a generation-based path or a model family with the expected chat helper. |
| Multimodal CLI raises around `processor.decode` | Processor lacks a single-token decode method or output format differs. | Try `processor.batch_decode` in a local adaptation or use a model-specific inference snippet. |
| Uploading files in `--modality text` fails | The multimodal CLI only handles processor branches for image/audio/video files. | Use no files for text mode or switch to a media modality. |

## Media preprocessing failures

| Symptom | Likely cause | Action |
|---|---|---|
| PIL cannot open image | Unsupported/corrupt file or wrong extension. | Convert to PNG/JPEG/WebP with RGB color mode. |
| Qwen-style resize raises aspect-ratio error | Image/video dimensions exceed aspect-ratio limit. | Crop/pad/resize to a less extreme aspect ratio before serving. |
| `librosa.load` fails | Missing codec support, bad file, or unsupported container. | Convert audio to WAV/FLAC at 16 kHz or the processor's target rate. |
| Audio output is nonsense | Sampling rate mismatch or stereo/mono handling mismatch. | For multimodal CLI, load at `processor.feature_extractor.sampling_rate`; for omni, use 16 kHz mono. |
| PyAV reports zero frames or index step errors | Video metadata does not expose frame count. | Re-encode with fixed frame rate and valid frame metadata; try a shorter MP4. |
| MoviePy omni video fails on `video.audio` | Video has no audio track; omni chunking expects one second of audio per frame unit. | Add/synthesize an audio track, use image/video-only multimodal CLI, or adapt the omni preprocessor. |
| Very long omni video exhausts memory/context | Each second becomes a unit with image and audio chunk. | Trim video, sample fewer seconds in a custom preprocessor, or use the video-only multimodal path. |

## Template and prompt failures

| Symptom | Likely cause | Action |
|---|---|---|
| Model ignores images/audio/video | Media placeholders and media file order/count do not match. | Keep one typed placeholder per uploaded media item and preserve order. |
| Prompt contains literal `USER:`/`ASSISTANT:` when model expects chat tokens | Formatter fell back to default format because no chat template was available. | Confirm the processor/tokenizer has `chat_template` or use a model class with `apply_chat_template`. |
| Duplicate `<image>` or `<audio>` tokens | Manual prompt inserted tokens while model custom template also inserts them. | Use typed content and let the model/processor formatter insert tokens unless that specific model requires manual tokens. |
| MiniCPM-O answers as text but no voice/audio output | Omni CLI returns `res.text`; bundled skill covers text response serving, not TTS output file handling. | Treat voice output as optional/unsupported unless you add model-specific TTS extraction. |

## Security and privacy checks

- `trust_remote_code=True` executes model-repository Python code locally; review and pin trusted model revisions where possible.
- Gradio `share=True` can create an externally reachable link; avoid sensitive prompts or private media.
- Do not paste private cache directories, environment prefixes, or tokens into generated reports.
- For user-supplied media, strip or avoid metadata when privacy matters.

## When to stop and report a gap

Stop and report a clear unsupported/optional limitation when:

- the requested model family is not in the align-anything registry and does not load through Transformers' fallback auto mapping;
- the model requires remote code the user does not trust;
- required accelerator memory is unavailable and CPU is not an acceptable substitute;
- a media modality depends on optional system codecs that cannot be installed in the environment;
- the user needs private/non-shared Gradio serving but cannot use an adapted local launcher.
