# Troubleshooting Sana Video, World Modeling, and Streaming

Use this reference when a plan fails, an input is ambiguous, or hardware/runtime constraints are unclear.

## HF downloads and model caches

Symptoms:

- First run spends a long time before sampling.
- `hf://...` path does not resolve.
- Hugging Face authorization, network, or snapshot-cache errors.
- Missing `gemma-2-2b-it`, LTX-2, SANA-WM refiner, or streaming component.

Likely causes:

- Weights are downloaded on first use.
- Network access is unavailable.
- A local path override points to an incomplete bundle.
- Gated or very large model components were not pre-cached.

Recovery:

1. Decide whether to use `hf://...` defaults or explicit local paths.
2. For SANA-WM streaming with a local bundle, ensure the bundle has `sana_dit/`, `ltx2_causal_vae/`, `refiner_diffusers/`, and `gemma3_12b/`.
3. For SANA-WM bidirectional, ensure DiT, VAE, refiner, and refiner text encoder are all available.
4. Retry after network/cache preparation, not by changing workflow family.
5. Keep cache paths out of runtime instructions and reports unless the user explicitly asks for machine-local debugging.

## GPU VRAM and OOM

Symptoms:

- CUDA out-of-memory during model load, VAE encode/decode, refiner load, or first compiled streaming chunk.
- Generation succeeds without refiner but fails with refiner.
- 720p path fails while 480p path succeeds.

Likely causes:

- 720p uses LTX-2 VAE with 128 latent channels and larger spatial frames.
- SANA-Video + LTX-2 refiner loads multiple heavy components.
- SANA-WM bidirectional refiner uses large LTX-2 refiner/text encoder components.
- SANA-WM streaming default bf16 stage1/refiner can require around 47GB-class memory before precision/offload changes.

Recovery:

- Try 480p instead of 720p for standard SANA-Video.
- Use `--offload_vae` and/or `--offload_refiner` for SANA-WM.
- Use `--no_refiner` only for fast Stage-1 debugging; mark the quality trade-off.
- For SANA-WM streaming, consider `--stage1_precision fp8 --refiner_precision fp8` on Hopper/Blackwell, or `fp4/fp4` only on Blackwell.
- Reduce `--refiner_kv_max_frames` only when the user accepts temporal quality loss.
- Use `--no_compile` for smoke/debug if cold compile workspace or time is the immediate obstacle.

## 720p LTX-2 VAE/refiner memory

Symptoms:

- OOM appears around VAE tiling/decoding or LTX-2 Stage 2.
- Refiner path fails after base SANA latent generation.

Likely causes:

- 720p SANA-Video uses the LTX-2 VAE path; SANA-Video + LTX-2 refiner is a multi-component two-stage pipeline.
- Saving both base and refined outputs temporarily increases residency and transfers.

Recovery:

- Plan CPU offload for Diffusers pipelines where supported.
- Avoid unnecessary simultaneous decode of base and refined outputs.
- Use the native 720p non-refiner command first to establish baseline feasibility.
- If the request only needs temporal structure, skip LTX-2 refiner and mention lower spatial quality.

## Frame-count snapping and horizon mistakes

Symptoms:

- Warning says `num_frames` was snapped.
- Output is shorter than requested.
- SANA-WM command with action duration does not match requested frame count.
- SANA-Streaming source-video decode errors.

Likely causes:

- SANA-WM bidirectional/chunk-causal snaps to `8*k+1` for LTX-2 VAE temporal stride.
- SANA-WM streaming snaps to `8 * refiner_block_size * k + 1`.
- Action DSL with `N` held-key frames produces `N+1` poses.
- SANA-Streaming V2V long mode needs the source video to decode at least `num_frames` frames.

Recovery:

- Use `seconds * fps + 1` for LongSANA and many world-model horizons.
- For SANA-WM streaming default `refiner_block_size=3`, use `24*k+1`: `241`, `481`, `961`, etc.
- For an action string, choose total segment duration near `num_frames-1`.
- Run `validate_camera_controls.py` before SANA-WM commands.
- Count source-video frames before SANA-Streaming long editing.

## Action DSL mapping update

Symptoms:

- Camera turns when the user expected strafe, or strafes when the user expected yaw.
- Old demo action strings reproduce a different trajectory.

Cause:

- SANA-WM changed the mapping: `a/d` are now yaw left/right and `j/l` are strafe left/right.

Recovery:

- For current commands: use `a/d` for yaw and `j/l` for strafe.
- For older-release action strings: swap `a/d` with `j/l` to approximate the old motion.
- Validate action strings with:

```bash
python sub-skills/video-world-streaming/scripts/validate_camera_controls.py --action "w-80,dw-40,w-80,aw-40"
```

## Camera and intrinsics shape issues

Symptoms:

- `--camera must be a (F, 4, 4) .npy`.
- Unsupported intrinsics shape.
- Generated geometry drifts or looks inconsistent.
- Pi3X aborts due to FOV outside range.

Likely causes:

- Camera array has wrong axes or stores world-to-camera instead of camera-to-world.
- Intrinsics file is not one of `(3,3)`, `(F,3,3)`, `(4,)`, or `(F,4)`.
- Intrinsics frame count does not match command frame count.
- Intrinsics are expressed in a different image pixel grid than the input image.

Recovery:

1. Validate files:

```bash
python sub-skills/video-world-streaming/scripts/validate_camera_controls.py \
  --camera camera_c2w.npy \
  --intrinsics intrinsics.npy \
  --num-frames 321
```

2. Confirm camera matrix bottom row is `[0,0,0,1]` and rotation determinant is near `1`.
3. Confirm intrinsics focal lengths and principal point imply reasonable FOV.
4. Prefer trusted intrinsics over Pi3X estimates for camera-adherence tasks.
5. If Pi3X is used, remember it estimates from the input image and can fail or be wrong for unusual framing.

## Pi3X optional estimate

Symptoms:

- Import error for Pi3X.
- Intrinsics-estimation warning followed by abort.
- Large memory spike before video generation.

Cause:

- SANA-WM estimates missing intrinsics with Pi3X and validates FOV in `[25°, 120°]`.

Recovery:

- Pass `--intrinsics` when available.
- Install/prepare Pi3X only if automatic intrinsics estimation is required.
- If Pi3X FOV fails, do not ignore it; provide a trusted intrinsics file.
- Treat Pi3X memory as separate from SANA-WM generation memory when planning tight VRAM jobs.

## fp8/fp4 Transformer Engine and GPU generation limits

Symptoms:

- Error says `--stage1_precision/--refiner_precision fp8/fp4 require NVIDIA Transformer Engine >= 2.x`.
- `fp4` selected on H100 or older GPU.
- Quantized run starts but quality/camera adherence changes.

Rules:

- `bf16`: default, any supported CUDA GPU.
- `fp8`: FP8 W8A8 for Hopper and Blackwell with Transformer Engine >= 2.x.
- `fp4`: NVFP4 W4A4 for Blackwell only (`sm_100`/`sm_120`, GB200/B200/RTX 50-series) with Transformer Engine >= 2.x.

Recovery:

- On Hopper, use `fp8`, not `fp4`.
- On Blackwell with 32GB-class VRAM, use `--stage1_precision fp4 --refiner_precision fp4` if quality trade-offs are acceptable.
- If Transformer Engine is absent or too old, run bf16 or prepare a compatible environment.
- Do not treat quantization as a speed guarantee; evidence frames it primarily as a memory optimization.

## xformers, flash-attn, and SDPA fallback

Symptoms:

- Attention backend errors, xformers cross-attention mask issues, or unexpected failures in recent Torch/xformers combinations.
- Streaming script sets SDPA/Inductor environment defaults before import.

Likely causes:

- World-model and streaming scripts deliberately set `DISABLE_XFORMERS=1` for compatibility with their attention/mask paths.
- The streaming script uses flash/cuDNN/math SDPA selection and Inductor compile knobs.

Recovery:

- Do not force xformers back on for SANA-WM unless debugging a specific backend experiment.
- Keep `DISABLE_XFORMERS=1` when reproducing documented SANA-WM and SANA-Streaming behavior.
- If flash-only paths fail on unsupported text-encoder shapes, allow math SDPA fallback as the streaming script does.
- Use `--no_compile` to isolate whether a failure is compile-related.

## Long streaming source-video frame count issues

Symptoms:

- `Short decode: <video> returned N frames, expected >= 969`.
- Long V2V editing produces fewer frames than intended.
- Source video opens locally but fails via `hf://` or PyAV.

Likely causes:

- Source video has fewer decoded frames than requested.
- PyAV/ImageIO cannot decode the format/codec.
- The request used `long_streaming` defaults on a short source video.

Recovery:

- Count source frames before running long V2V.
- Lower `--num_frames` if the edit should target a shorter clip.
- Use `bidirectional_short` for 81-frame edits.
- Re-encode the source to a PyAV-readable MP4 if decode returns no frames.

## Output MP4 problems

Symptoms:

- Output file exists but has zero frames.
- SANA-WM streaming output is visible mid-run but final frame count is wrong.
- Output path overwrote a previous result.

Recovery:

- Decode-check with ImageIO/PyAV after the process exits.
- For SANA-WM bidirectional, expect `<name>_generated.mp4`.
- For SANA-WM streaming, expect `<name>_streaming.mp4` and remember it grows during inference.
- For SANA-Streaming V2V, expect `<output_dir>/<output_name>`.
- Use unique names for benchmark or multi-run planning.

## Native verification candidates

These are evidence-backed candidates for later verification, not runtime requirements:

- Video/WM/streaming sections in `tests/bash/inference/test_inference.sh` require CUDA and Hugging Face weights. They are native ground-truth candidates for final verification only after the skill is integrated.
- `tests/bash/training/test_training_sana_streaming.sh` contains useful CPU helper assertions for V2V manifests/cache/source-video edge cases if dependencies are available; route training-specific assertions to the training/data skill, but the source-video short-decode lessons inform this sub-skill.
