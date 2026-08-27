# Benchmark reference

All commands below assume they are run from an ECCV2022-RIFE checkout that has repository dependencies installed. External benchmark datasets and external RIFE/RIFE_m checkpoints are not bundled and must be supplied by the user. The README-reported numbers are targets from the upstream documentation, not proof that a later checkout/session has reproduced them.

## Quick benchmark matrix

| Benchmark | Command | Dataset layout expected by source script | Checkpoint | Metric / expected signal | Dependencies | Backend | Verification decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Random throughput smoke | `python benchmark/testtime.py` | None; creates random tensors shaped `1x3x480x640`. | None; does **not** load official weights. | Prints average seconds per inference over 100 timed iterations after warmup. Timing only, no quality metric. | Base requirements: PyTorch, OpenCV import, model package. | Any; CUDA used if available, CPU can be slow. | Safe no-data candidate if runtime budget allows; mark `SKIP_EXPENSIVE` on slow CPU or tight budget. |
| UCF101 | `python benchmark/UCF101.py` | `UCF101/ucf101_interp_ours/<case>/frame_00.png`, `frame_01_gt.png`, `frame_02.png`. | `train_log/flownet.pkl` from external RIFE evaluation checkpoint. | Streaming `Avg PSNR: ... SSIM: ...`; README reports `PSNR: 35.282 SSIM: 0.9688`. | Base requirements plus checkpoint. | Any; CUDA if available else CPU. | `SKIP_DATA` unless dataset and checkpoint are present; `SKIP_EXPENSIVE` if full sweep not approved. |
| Vimeo90K interpolation test | `python benchmark/Vimeo90K.py` | `vimeo_interp_test/tri_testlist.txt`; for each list entry, `vimeo_interp_test/target/<entry>/im1.png`, `im2.png`, `im3.png` where `im2.png` is ground truth. | `train_log/flownet.pkl` from external RIFE evaluation checkpoint. | Streaming `Avg PSNR: ... SSIM: ...`; README reports `PSNR: 35.615 SSIM: 0.9779`. | Base requirements plus checkpoint. | Any; CUDA if available else CPU. | `SKIP_DATA` unless dataset and checkpoint are present; `SKIP_EXPENSIVE` if full list is outside budget. |
| MiddleBury OTHER | `python benchmark/MiddleBury_Other.py` | `other-data/<sequence>/frame10.png`, `frame11.png`; `other-gt-interp/<sequence>/frame10i11.png` for 12 fixed sequence names. | `train_log/flownet.pkl` from external RIFE evaluation checkpoint. | Prints running mean interpolation error (IE); README reports `IE: 1.956`. Lower is better. | Base requirements plus checkpoint. | Any; CUDA if available else CPU. | `SKIP_DATA` unless both data and ground-truth roots plus checkpoint are present. |
| ATD12K | `python benchmark/ATD12K.py` | `datasets/test_2k_540p/<case>/frame1.png`, `frame2.png`, `frame3.png` where `frame2.png` is ground truth. | `train_log/flownet.pkl` from external RIFE evaluation checkpoint. | Streaming `Avg PSNR: ... SSIM: ...`; no README target value in this checkout. | Base requirements plus checkpoint. | Any; CUDA if available else CPU. | `SKIP_DATA` unless dataset and checkpoint are present; `SKIP_EXPENSIVE` for full sweep if not approved. |
| HD YUV 2X | `python benchmark/HD.py` | Exact YUV files under `HD_dataset/HD720p_GT/`, `HD_dataset/HD1080p_GT/`, and `HD_dataset/HD544p_GT/` listed below. | `train_log/flownet.pkl` from external RIFE evaluation checkpoint. | Per-video PSNR values and final `avg psnr`; README reports `PSNR: 32.14`. Uses Y-channel PSNR computed via RGB/YUV conversion. | Base requirements plus `scikit-image` and PIL used by `yuv_frame_io.py`. | **CUDA required** because tensors are moved with `.cuda()`. | `SKIP_DATA` if HD files/checkpoint missing; `required-CUDA` if CUDA unavailable; `SKIP_EXPENSIVE` if full 101-frame YUV sweep is outside budget. |
| HD YUV 4X / RIFE_m | `python benchmark/HD_multi_4X.py` | Same HD YUV files as HD 2X. The script evaluates 4X interpolation by generating three intermediate frames between endpoints. | `RIFE_m_train_log/flownet.pkl` from external RIFE_m evaluation checkpoint. | Grouped PSNR: README reports `22.96(544*1280), 31.87(720p), 34.25(1080p)`. | Base requirements plus `scikit-image` and PIL used by `yuv_frame_io.py`. | **CUDA required** because tensors are moved with `.cuda()`. | `SKIP_DATA` if HD files/RIFE_m checkpoint missing; `required-CUDA` if CUDA unavailable; `SKIP_EXPENSIVE` for full run. |

## Checkpoint expectations

- RIFE benchmarks (`UCF101.py`, `Vimeo90K.py`, `MiddleBury_Other.py`, `ATD12K.py`, `HD.py`) call `model.load_model('train_log')` and therefore expect `train_log/flownet.pkl`.
- RIFE_m HD 4X (`HD_multi_4X.py`) builds `Model(arbitrary=True)`, calls `model.load_model('RIFE_m_train_log')`, and expects `RIFE_m_train_log/flownet.pkl`.
- `benchmark/testtime.py` does not call `load_model`; it times randomly initialized model inference and should not be used for PSNR/SSIM/IE claims.
- The source `Model.load_model` loads a PyTorch state dict from `flownet.pkl`. A file with a different checkpoint format can fail even if the filename exists.

## HD YUV expected files

The HD scripts hard-code these YUV420 files and resolution pairs:

```text
HD_dataset/HD720p_GT/parkrun_1280x720_50.yuv       720x1280
HD_dataset/HD720p_GT/shields_1280x720_60.yuv       720x1280
HD_dataset/HD720p_GT/stockholm_1280x720_60.yuv     720x1280
HD_dataset/HD1080p_GT/BlueSky.yuv                  1080x1920
HD_dataset/HD1080p_GT/Kimono1_1920x1080_24.yuv     1080x1920
HD_dataset/HD1080p_GT/ParkScene_1920x1080_24.yuv   1080x1920
HD_dataset/HD1080p_GT/sunflower_1080p25.yuv        1080x1920
HD_dataset/HD544p_GT/Sintel_Alley2_1280x544.yuv    544x1280
HD_dataset/HD544p_GT/Sintel_Market5_1280x544.yuv   544x1280
HD_dataset/HD544p_GT/Sintel_Temple1_1280x544.yuv   544x1280
HD_dataset/HD544p_GT/Sintel_Temple2_1280x544.yuv   544x1280
```

For the full source loops, each YUV file should contain at least frames `0..100` (101 frames) in YUV420 layout. Shorter files may make the source loop break early or produce non-official averages.

## Safe layout validation

Use the bundled helper from the evaluation sub-skill directory:

```bash
python scripts/check_benchmark_layout.py --repo-root <checkout> --benchmark testtime
python scripts/check_benchmark_layout.py --repo-root <checkout> --benchmark vimeo90k --max-samples 10
python scripts/check_benchmark_layout.py --repo-root <checkout> --benchmark hd --strict
python scripts/check_benchmark_layout.py --repo-root <checkout> --benchmark all --json
```

The helper checks expected files only; it never downloads data, imports PyTorch, or runs benchmark scripts.
