# Preprocessing scripts

This sub-skill distinguishes between safe bundled helpers and source scripts that
should stay reference-only because they contact external services, assume a
particular private path map, or perform long-running preprocessing.

## Script inventory

| Script | Decision | Why | Runtime note |
| --- | --- | --- | --- |
| `data/download_cyclegan_data.py` | Reference-only | Network download plus symlink side effects | Downloads a named archive, stores it in cache, and links it into `data/<name>`. Use only when the user explicitly wants the download. |
| `data/download_pix2pix_data.py` | Reference-only | Network download plus symlink side effects | Same pattern as the CycleGAN downloader, but with the Pix2Pix dataset list and archive format. |
| `data/process_div2k_data.py` | Bundled as `scripts/process_div2k_data.py` | Safe local patch extraction | Crops `DIV2K_train_HR` and the bicubic LR folders into `*_sub` outputs with explicit local paths. The bundled helper refuses to overwrite existing output folders by default. |
| `data/lsr2_preprocess.py` | Reference-only | Requires ffmpeg, face detection, and long video preprocessing | Extracts frames and audio from raw LRS2 videos into `lrs2_preprocessed`. It may skip frames or clips when no face is detected. |
| `data/realsr_preprocess/create_bicubic_dataset.py` | Reference-only | Depends on repo-local path assumptions | Generates RealSR bicubic training pairs and writes into generated folders. Treat its path map as source evidence, not as a runtime dependency. |
| `data/realsr_preprocess/create_kernel_dataset.py` | Reference-only | Depends on repo-local path assumptions and KernelGAN outputs | Generates RealSR kernel-based pairs from `.mat` kernels. Keep the folder mapping explicit in any runtime rewrite. |
| `data/realsr_preprocess/collect_noise.py` | Reference-only | Writes new generated directories | Collects low-variance patches into new noise folders. Use as behavior reference only. |

The RealSR helper stack also includes `imresize.py` and `utils.py`; treat them
as internal algorithm support rather than standalone user entry points.

## Bundled helper behavior

### `scripts/process_div2k_data.py`

- Input: one explicit `--data-root` that already contains the raw DIV2K folders.
- Output: `DIV2K_train_HR_sub` and `DIV2K_train_LR_bicubic/X2_sub`, `X3_sub`, `X4_sub`.
- Safety: stops if an output folder already exists.
- Use case: create patch-level DIV2K crops for SR configs that expect `_sub`
  folders.

### `scripts/check_dataset_layout.py`

- Read-only validator for common PaddleGAN layouts.
- Supports unpaired, paired, DIV2K, REDS, Vimeo90K, LRS2, RealSR, and a generic
  recursive image scan.
- Intended for local sanity checks before running a full preprocessing or
  training workflow.

## No-download policy

- Do not run dataset download scripts by default.
- If a download is requested, make the cache and symlink behavior explicit first.
- If a download is interrupted, clear the broken link or partial cache before
  retrying instead of layering another archive on top.
- If a preprocessing helper depends on a private path map, rewrite it to accept
  explicit local folders instead of carrying the original source assumption into
  runtime guidance.
