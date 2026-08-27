# Troubleshooting

Evidence labels used for this reference: README.md, docs/MODELS.md, demo.py,
gradio_demo.py, mmaudio/eval_utils.py, mmaudio/model/networks.py,
mmaudio/model/sequence_config.py, mmaudio/utils/download_utils.py.

## Quick triage matrix

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `Unknown model variant` | Typo or unsupported `--variant` | Use one of `small_16k`, `small_44k`, `medium_44k`, `large_44k`, `large_44k_v2`. The helper script should reject anything else. |
| Missing or corrupted weights | Partial download, wrong filename, or network interruption | Re-run from the repo root so relative paths resolve. Delete the bad file and let the downloader fetch it again. The downloader checks MD5 for known filenames. |
| Download fails with a filename that is not in the registry | The file name is not one of the known MMAudio assets | Use the documented checkpoint names only. The downloader only knows the approved weight and auxiliary file list. |
| CPU run is very slow | No GPU backend, long duration, or high-resolution video decode/re-encode cost | Prefer GPU, shorten the clip, reduce `--num_steps`, and use `--skip_video_composite` when you only need audio. A smaller model also helps. |
| GPU OOM | Long video, large model, or unnecessary extra work | Shorten the duration to the trained 8-second window, switch to a smaller variant, avoid MP4 compositing, and lower the batch-size multipliers in custom API calls. Do not use `--full_precision` as an OOM fix. |
| Video decode or read error | Unsupported container/codec or a damaged local file | Re-encode the source to a common MP4/H.264-style file and retry. For diagnosis, test with a known-good short sample. |
| Empty prompt produces a bad filename or poor results | The demo accepts empty strings, but an empty prompt is not a useful conditioning signal | Provide a concrete prompt. If you need a safe filename, use a custom output directory or a command builder that rejects blank prompts. |
| Negative prompt mismatch in batch code | `negative_text` length does not match the prompt batch size | Either pass `negative_text=None` or provide one negative prompt per batch item. |
| Duration looks wrong or output is cut off | Duration changed without updating sequence lengths, or the source video is shorter than requested | Set `seq_cfg.duration`, call `net.update_seq_lengths(...)`, and use `video_info.duration_sec` from `load_video(...)` after truncation. |
| Browser UI starts but the browser cannot access outputs | The app only exposes its output directory | Keep generated files under `./output/gradio` or adjust the app if you intentionally want a different shared directory. |
| Hugging Face unauthenticated warning | Public weights or metric helpers are being resolved without a token | Usually harmless for MMAudio inference. Add a token only if your environment requires authenticated access to another mirror. |

## Known inference-specific gotchas

### 1. `large_44k_v2` is the default, not a hard requirement
If a user only has a small GPU, try a smaller checkpoint before changing any model code.
The 16 kHz path is smaller in audio footprint but requires the 16 kHz VAE and vocoder assets.

### 2. Duration is a first-class control
The model is trained around 8 seconds. Large deviations can produce weaker quality,
and the loader may truncate long videos to the shorter available clip/sync window.

### 3. High resolution is expensive but not helpful
The CLIP and Synchformer resizes are fixed. If the source video is huge, the decode and re-encode path can dominate runtime without improving the result.

### 4. `--full_precision` is for compatibility
Use it if bfloat16 is unsupported or numerically unstable in your environment.
It usually increases memory usage, so it is not a relief valve for OOM.

### 5. Video compositing is optional
If you only need audio, skip the MP4 reconstruction step.
That avoids extra decode/re-encode work and can materially reduce runtime.
