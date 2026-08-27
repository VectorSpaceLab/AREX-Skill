# CLI Reference

Evidence labels used for this reference: README.md, docs/MODELS.md, demo.py,
mmaudio/eval_utils.py, mmaudio/model/sequence_config.py, mmaudio/model/networks.py,
mmaudio/utils/download_utils.py.

## Primary command

`demo.py` is the command-line inference entry point.
Run it from the MMAudio repository root so the relative weight paths resolve.

### Text-to-audio
```bash
python demo.py \
  --variant large_44k_v2 \
  --duration 8 \
  --prompt "waves, seagulls" \
  --negative_prompt "" \
  --seed 42 \
  --output ./output \
  --skip_video_composite
```

### Video-to-audio
```bash
python demo.py \
  --variant large_44k_v2 \
  --video ./samples/input.mp4 \
  --prompt "waves, seagulls" \
  --negative_prompt "music" \
  --duration 8 \
  --cfg_strength 4.5 \
  --num_steps 25 \
  --seed 42 \
  --output ./output
```

### Useful option map
| Option | Meaning | Notes |
| --- | --- | --- |
| `--variant` | Choose a pretrained model | Supported: `small_16k`, `small_44k`, `medium_44k`, `large_44k`, `large_44k_v2`. Default: `large_44k_v2`. |
| `--video` | Video input path | Omit for text-to-audio. When present, the loader reads both CLIP and Synchformer streams. |
| `--prompt` | Positive text prompt | Required for useful inference. Blank text is allowed by the script but not recommended. |
| `--negative_prompt` | Negative text prompt | Default is empty string. In Gradio, the video tab defaults to `music`. |
| `--duration` | Requested audio/video length in seconds | Default `8.0`. The model is trained around 8 seconds; large deviations can reduce quality. |
| `--cfg_strength` | Classifier-free guidance strength | Default `4.5`. Lower values reduce conditioning strength. |
| `--num_steps` | ODE sampling steps | Default `25`. Fewer steps are faster but less refined. |
| `--mask_away_clip` | Disable clip-video conditioning | Keeps Syncformer conditioning active; useful for ablations or debugging. |
| `--output` | Output directory | Default `./output`. Created automatically if needed. |
| `--seed` | Random seed | Default `42`. The CLI demo uses the seed directly. |
| `--skip_video_composite` | Do not write an MP4 composite | Use for audio-only jobs or to avoid expensive re-encoding. |
| `--full_precision` | Force float32 inference | Use for precision compatibility, not for memory reduction. |

## Output behavior
- Always writes audio as `.flac`.
- Writes an `.mp4` composite only when a video is supplied and `--skip_video_composite` is not set.
- Output filenames are derived from the input video stem or a sanitized prompt string.
- The output directory is created automatically.
- The script logs memory usage after generation.

## Default device and dtype
- Device order: CUDA, then MPS, then CPU.
- Default dtype: `torch.bfloat16` unless `--full_precision` is set.
- If neither CUDA nor MPS is available, the demo warns and runs on CPU.

## Model asset facts
The CLI uses `ModelConfig.download_if_needed()` to ensure the model checkpoint,
VAE, optional vocoder, and Synchformer checkpoint are present. CLIP is handled
by the feature stack.

| Variant | Sampling rate | Required model file | Required VAE / vocoder facts | Notes |
| --- | --- | --- | --- | --- |
| `small_16k` | 16 kHz | `weights/mmaudio_small_16k.pth` | `ext_weights/v1-16.pth` and `ext_weights/best_netG.pt` | 16 kHz path; uses the 16 kHz audio stack. |
| `small_44k` | 44.1 kHz | `weights/mmaudio_small_44k.pth` | `ext_weights/v1-44.pth` | 44 kHz path; no 16 kHz BigVGAN file. |
| `medium_44k` | 44.1 kHz | `weights/mmaudio_medium_44k.pth` | `ext_weights/v1-44.pth` | Same 44 kHz audio stack, larger network. |
| `large_44k` | 44.1 kHz | `weights/mmaudio_large_44k.pth` | `ext_weights/v1-44.pth` | Larger 44 kHz network. |
| `large_44k_v2` | 44.1 kHz | `weights/mmaudio_large_44k_v2.pth` | `ext_weights/v1-44.pth` | Recommended default. Benchmark distance may be slightly worse than `large_44k`, but it generalizes better in practice. |

Every variant also expects `ext_weights/synchformer_state_dict.pth`.
The 44.1 kHz vocoder is handled automatically by the feature stack; the 16 kHz path additionally uses `ext_weights/best_netG.pt`.
The downloader checks the known filenames and verifies MD5 checksums.

## Video handling facts
- CLIP input is resized to `384 x 384`.
- Synchformer input is resized on the shorter edge to `224`, then center-cropped to `224 x 224`.
- The CLIP stream runs at `8 FPS`.
- The Synchformer stream runs at `25 FPS`.
- If the source video is below `25 FPS`, frames are duplicated to satisfy the Synchformer rate.
- If the source video is shorter than the requested duration, the loader truncates the run to the shorter available length.
- Higher-resolution source video slows decoding and re-encoding, but does not improve quality.

## Text-only command checklist
For a safe text-to-audio command:
1. Use `large_44k_v2` unless another variant is requested.
2. Omit `--video`.
3. Include `--skip_video_composite`.
4. Keep `--duration` near `8` seconds unless there is a specific reason not to.
5. Provide a non-empty prompt and a writable output directory.

## When the CLI should not be used
- If the user wants the browser UI, use `gradio_demo.py` instead.
- If the user needs programmatic generation inside Python, use the API reference.
- If the user needs training, evaluation, or data preparation, route out of this sub-skill.
