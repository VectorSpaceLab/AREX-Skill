# SANA-WM and SANA-Streaming

This reference covers the camera-controlled world-model paths and video-to-video streaming editing paths. Use it to distinguish argument surfaces before planning commands.

## Workflow map

| Workflow | Native script | Core input | Default/typical frames | Output naming | Best for |
| --- | --- | --- | --- | --- | --- |
| SANA-WM bidirectional | `inference_video_scripts/wm/inference_sana_wm.py` | image + prompt file + action or camera trajectory | `161` default, `321` demo, `961` benchmark | `<name>_generated.mp4` | High-quality camera-controlled world generation. |
| SANA-WM chunk-causal teacher | `inference_video_scripts/wm/inference_sana_wm.py` with chunk config/checkpoint | image + prompt + action/camera | long rollouts such as `961` | `<name>_generated.mp4` | Research checkpoint / Stage-1 causal experiments; refiner remains bidirectional unless disabled. |
| SANA-WM streaming | `inference_video_scripts/wm/inference_sana_wm_streaming.py` | image + prompt + action/camera | `241` default, `961` for ~60s | `<name>_streaming.mp4` | Progressive MP4, chunk-causal Stage 1/refiner/VAE, lower-latency long world modeling. |
| SANA-Streaming V2V long | `inference_video_scripts/v2v/inference_sana_streaming.py --mode long_streaming` | source video + edit prompt | `969` default | `output.mp4` by default | Minute-level video-to-video editing. |
| SANA-Streaming V2V short | `inference_video_scripts/v2v/inference_sana_streaming.py --mode bidirectional_short` | source video + edit prompt | `81` default | `output.mp4` by default | 5-second bidirectional editing and local/object edits. |

Do not mix the SANA-WM and SANA-Streaming surfaces: SANA-WM uses first-frame image plus camera/action controls; SANA-Streaming uses a source video and text edit instruction.

## SANA-WM bidirectional

Use this for standard world-model generation with image, prompt, and camera control.

Safe command planning:

```bash
python sub-skills/video-world-streaming/scripts/plan_sana_video_command.py \
  --mode sana-wm \
  --image first_frame.png \
  --prompt-file prompt.txt \
  --action "w-100,dw-60,w-100,aw-60" \
  --intrinsics intrinsics.npy \
  --num-frames 321 \
  --output-dir results/sana_wm_demo \
  --name demo_0
```

Canonical command shape:

```bash
python inference_video_scripts/wm/inference_sana_wm.py \
  --image first_frame.png \
  --prompt prompt.txt \
  --action "w-100,dw-60,w-100,aw-60" \
  --intrinsics intrinsics.npy \
  --num_frames 321 \
  --output_dir results/sana_wm_demo \
  --name demo_0
```

Camera trajectory alternative:

```bash
python inference_video_scripts/wm/inference_sana_wm.py \
  --image first_frame.png \
  --prompt prompt.txt \
  --camera camera_c2w.npy \
  --intrinsics intrinsics.npy \
  --num_frames 321 \
  --output_dir results/sana_wm_demo \
  --name demo_0
```

Key arguments:

| Argument | Meaning |
| --- | --- |
| `--image` | First-frame RGB image; resized and center-cropped to 704 x 1280. |
| `--prompt` | UTF-8 text file. The script exits if the file is empty. |
| `--action` | Action DSL rolled into `(N+1,4,4)` camera-to-world poses. Mutually exclusive with `--camera`. |
| `--camera` | `.npy` camera-to-world matrices of shape `(F,4,4)`. Mutually exclusive with `--action`. |
| `--intrinsics` | Optional `.npy` intrinsics; if omitted, Pi3X estimates them from the image. |
| `--num_frames` | Requested output frames; native logic limits it to trajectory length and snaps to `8*k+1`. |
| `--step` | Stage-1 DiT sampling steps; default `60`. |
| `--cfg_scale` | Default `5.0` for SANA-WM. |
| `--flow_shift` | Optional scheduler flow-shift override. |
| `--no_refiner` | Skip LTX-2 refiner and decode Stage-1 latents for fast/lower-quality debugging. |
| `--offload_vae`, `--offload_refiner` | Reduce VRAM by moving components off GPU between phases. |

Default release weights:

- Stage-1 DiT: `hf://Efficient-Large-Model/SANA-WM_bidirectional/dit/sana_wm_1600m_720p.safetensors`.
- Inference config: `hf://Efficient-Large-Model/SANA-WM_bidirectional/config.yaml`.
- Refiner/text encoder roots come from the same SANA-WM bidirectional release.

## SANA-WM chunk-causal teacher

Use this when the user specifically asks for chunk-causal Stage-1 teacher planning or the `SANA-WM_chunk_causal` checkpoint.

Command shape:

```bash
python inference_video_scripts/wm/inference_sana_wm.py \
  --config configs/sana_wm/sana_wm_chunk_causal_1600m_720p.yaml \
  --model_path hf://Efficient-Large-Model/SANA-WM_chunk_causal/dit/sana_wm_chunk_causal_1600m_720p.safetensors \
  --image first_frame.png \
  --prompt prompt.txt \
  --action "w-240,dw-120,w-120,aw-180,w-300" \
  --num_frames 961 \
  --offload_refiner \
  --output_dir results/sana_wm_chunk_causal \
  --name sample
```

Important distinctions:

- The public config uses `chunk_flow_euler`; `--sampling_algo auto` selects the chunk sampler.
- `--chunk_interval_k` defaults to `1 / num_chunks`; override only for ablations.
- The chunk-causal teacher release intentionally focuses on Stage 1 and may show artifacts or weaker camera adherence.
- Refiner stays enabled unless `--no_refiner` is passed. Use `--no_refiner` only for fast Stage-1 debugging.

## SANA-WM streaming

Use this for the chunk-pipelined world-model path that emits a progressive MP4.

Safe command planning:

```bash
python sub-skills/video-world-streaming/scripts/plan_sana_video_command.py \
  --mode sana-wm-streaming \
  --image first_frame.png \
  --prompt-file prompt.txt \
  --action "w-80,dw-40,w-80,aw-40" \
  --intrinsics intrinsics.npy \
  --num-frames 241 \
  --output-dir results/sana_wm_streaming \
  --name demo_0
```

Canonical command shape:

```bash
python inference_video_scripts/wm/inference_sana_wm_streaming.py \
  --image first_frame.png \
  --prompt prompt.txt \
  --action "w-80,dw-40,w-80,aw-40" \
  --intrinsics intrinsics.npy \
  --num_frames 241 \
  --output_dir results/sana_wm_streaming \
  --name demo_0
```

Streaming defaults and constraints:

| Knob | Default | Why it matters |
| --- | --- | --- |
| `--num_frames` | `241` | About 15s at 16 fps; snapped to `8 * refiner_block_size * k + 1`. |
| `--denoising_step_list` | `1000,960,889,727,0` | 4-step distilled Stage-1 schedule; list must end with `0`. |
| `--num_frame_per_block` | `3` | Must match the checkpoint chunk size. |
| `--refiner_block_size` | `3` | Refiner latent frames per AR block; affects snapping stride. |
| `--refiner_kv_max_frames` | `11` | Sink + history + active frames in the refiner sliding window. |
| `--num_cached_blocks` | `2` | Stage-1 sliding-window cache; `-1` keeps all chunks. |
| `--streaming_preset` | `medium` | H.264 preset for progressive MP4 writer; `ultrafast` is useful for smoke runs. |
| `--no_compile` | off by default | Use for quick smoke/debug; canonical performance uses `torch.compile` on the refiner. |

Streaming output:

- Output path is `<output_dir>/<name>_streaming.mp4`.
- The file grows progressively while inference continues.
- Optional benchmark outputs can include JSON throughput and sampled-frame NPZ files.

Precision planning:

| `--stage1_precision` / `--refiner_precision` | Hardware | Requirement | Use when |
| --- | --- | --- | --- |
| `bf16` | Any supported CUDA GPU | no Transformer Engine precision dependency | Best default and quality baseline. |
| `fp8` | Hopper or Blackwell | NVIDIA Transformer Engine >= 2.x | Need lower VRAM without Blackwell-only fp4. |
| `fp4` | Blackwell only (`sm_100`/`sm_120`, e.g. B200/GB200/RTX 50-series) | NVIDIA Transformer Engine >= 2.x with NVFP4 | Need 32GB-class memory fit. |

Planning notes:

- Quantization affects transformer linear GEMMs and is mainly a memory optimization.
- `fp4` on non-Blackwell is a plan error; use `fp8` on Hopper.
- Avoid compiling the causal VAE streaming decoder; evidence notes it corrupts the cross-chunk cache. The script skips VAE compile even if requested.
- `--refiner_kv_max_frames 2` can reduce VRAM but costs temporal quality/flicker.

## SANA-Streaming V2V editing

Use this when the input is a source video plus an edit prompt. Do not confuse it with SANA-WM streaming.

Safe command planning:

```bash
python sub-skills/video-world-streaming/scripts/plan_sana_video_command.py \
  --mode sana-streaming-v2v \
  --streaming-v2v-mode long_streaming \
  --source-video input.mp4 \
  --prompt "Transform the entire scene into a Sci-Fi digital painting." \
  --output-dir results/sana_streaming_long \
  --output-name output.mp4
```

Long streaming command shape:

```bash
python inference_video_scripts/v2v/inference_sana_streaming.py \
  --mode long_streaming \
  --config configs/sana_streaming/sana_streaming_2b_720p.yaml \
  --model_path hf://Efficient-Large-Model/SANA-Streaming/dit/sana_streaming_ar.pth \
  --prompt "Transform the entire scene into a breathtaking Sci-Fi Art digital painting." \
  --video_path source.mp4 \
  --num_frames 969 \
  --step 4 \
  --cfg_scale 1.0 \
  --num_cached_blocks 2 \
  --sink_token true \
  --output_dir results/sana_streaming_long \
  --output_name output.mp4
```

Bidirectional short command shape:

```bash
python inference_video_scripts/v2v/inference_sana_streaming.py \
  --mode bidirectional_short \
  --config configs/sana_streaming/sana_streaming_bidirectional_2b_720p.yaml \
  --model_path hf://Efficient-Large-Model/SANA-Streaming_bidirectional/dit/sana_bidirectional_short.pth \
  --prompt "Remove the earrings and reconstruct the exposed earlobes." \
  --video_path source.mp4 \
  --num_frames 81 \
  --step 50 \
  --cfg_scale 6.0 \
  --output_dir results/sana_streaming_bidirectional \
  --output_name output.mp4
```

Argument differences:

| Argument | `long_streaming` | `bidirectional_short` |
| --- | --- | --- |
| `--config` | `configs/sana_streaming/sana_streaming_2b_720p.yaml` | `configs/sana_streaming/sana_streaming_bidirectional_2b_720p.yaml` |
| `--model_path` | `hf://Efficient-Large-Model/SANA-Streaming/dit/sana_streaming_ar.pth` | `hf://Efficient-Large-Model/SANA-Streaming_bidirectional/dit/sana_bidirectional_short.pth` |
| `--num_frames` | `969` default | `81` default |
| `--step` | `4` | `50` |
| `--cfg_scale` | `1.0` | `6.0` |
| `--negative_prompt` | empty by default | built-in anti-artifact default if omitted |
| `--num_cached_blocks`, `--sink_token` | relevant | accepted but not the main path |

Source-video handling:

- Local files and `hf://...` URIs are supported.
- The script decodes frames with `imageio.v3.imiter(..., plugin="pyav")` and stops at `num_frames`.
- If fewer than `num_frames` frames are decoded and `num_frames != 81`, it raises `Short decode: ... expected >= num_frames`.
- For 81-frame short mode, the short-decode guard is relaxed, but zero decoded frames still raise.

## Validation checklist

Before running any command:

1. Determine whether the request is SANA-WM image+camera world modeling or SANA-Streaming source-video editing.
2. Validate `--action`, `--camera`, and `--intrinsics` with the bundled validator for SANA-WM.
3. Check frame snapping: SANA-WM bidirectional/chunk-causal `8*k+1`; SANA-WM streaming `8*refiner_block_size*k+1`.
4. Check source video decoded frame count for SANA-Streaming V2V.
5. Choose offload and precision flags according to VRAM and GPU generation.
6. Confirm the expected MP4 path and inspect it after generation.

## Source-script decisions

- `inference_video_scripts/wm/inference_sana_wm.py`: reference-only for GPU generation; command surface and validations are distilled here and in the planner/validator.
- `inference_video_scripts/wm/inference_sana_wm_streaming.py`: reference-only for chunk-pipelined GPU generation; planner exposes safe flags without running it.
- `inference_video_scripts/wm/camera_control.py`: adapted into the bundled validator's action-key schema and mapping notes.
- `inference_video_scripts/v2v/inference_sana_streaming.py`: reference-only for GPU V2V editing; planner safely emits commands and source-video warnings.
- Benchmark/evaluation tools and training scripts are excluded from this sub-skill and routed elsewhere.
