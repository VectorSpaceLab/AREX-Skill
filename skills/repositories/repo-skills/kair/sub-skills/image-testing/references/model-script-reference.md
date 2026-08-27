# KAIR Image Model and Script Reference

Use this table to choose an image-testing entry point, expected checkpoints, and default data route. Checkpoint acquisition is handled by the root model-zoo/download guidance; this sub-skill only maps what image scripts expect.

## Script and checkpoint map

| Family / task | Entry point | CLI style | Expected checkpoint names | Default or common data route | Notes |
|---|---|---:|---|---|---|
| DnCNN Gaussian denoising | `main_test_dncnn.py` | argparse | `dncnn_15.pth`, `dncnn_25.pth`, `dncnn_50.pth`, `dncnn_gray_blind.pth`, `dncnn_color_blind.pth`, `dncnn3.pth` | `testsets/set12`, `testsets/bsd68`, optionally `testsets/cbsd68` | Generates noisy input from clean images when degradation is enabled. Color models use 3 channels; other names use grayscale. |
| FDnCNN denoising | `main_test_fdncnn.py` | hard-coded | `fdncnn_gray.pth`, `fdncnn_color.pth`, `fdncnn_gray_clip.pth`, `fdncnn_color_clip.pth` | `testsets/bsd68`, `testsets/cbsd68`, `testsets/set12` | Patch `model_name`, `testset_name`, `noise_level_img`, and `noise_level_model`. Adds a noise-level map as an input channel. |
| FFDNet denoising | `main_test_ffdnet.py` | hard-coded | `ffdnet_gray.pth`, `ffdnet_color.pth`, `ffdnet_gray_clip.pth`, `ffdnet_color_clip.pth` | `testsets/bsd68`, `testsets/cbsd68`, `testsets/set12` | Patch noise constants and channel/model choice. Passes sigma tensor to the network. |
| IRCNN denoising | `main_test_ircnn_denoiser.py` | hard-coded | `ircnn_gray.pth`, `ircnn_color.pth` | `testsets/set12`, `testsets/bsd68` | Patch `noise_level_img`; internal denoiser index is derived from sigma. |
| DnCNN3 deblocking / blind restoration | `main_test_dncnn3_deblocking.py` | hard-coded | `dncnn3.pth` | `testsets/bsd68` or a folder of low-quality JPEG images | Patch `n_channels` for grayscale versus color. The script processes already degraded JPEG/LQ images rather than creating a `--jpeg` CLI. |
| SRMD / SRMDNF SR | `main_test_srmd.py` | hard-coded | `srmdnf_x2.pth`, `srmdnf_x3.pth`, `srmdnf_x4.pth`, `srmd_x2.pth`, `srmd_x3.pth`, `srmd_x4.pth` | `testsets/set5`, `testsets/srbsd68` | Scale factor is parsed from checkpoint name. Synthetic LR and optional noise are generated from HR when paths match. |
| DPSR SR | `main_test_dpsr.py` | hard-coded | `dpsr_x2.pth`, `dpsr_x3.pth`, `dpsr_x4.pth`, `dpsr_x4_gan.pth` | `testsets/set5`, `testsets/srbsd68` | Patch `model_name` and noise constants. `*_gan` is perceptual-quality oriented. |
| MSRResNet / SRResNet SR | `main_test_msrresnet.py` | hard-coded | `msrresnet_x4_psnr.pth`, `msrresnet_x4_gan.pth` | `testsets/set5`, `testsets/srbsd68` | x4 only in this script. PSNR versus GAN checkpoint changes restoration objective. |
| RRDB / ESRGAN-style SR | `main_test_rrdb.py` | hard-coded | Script expects `rrdb_x4_psnr.pth` or `rrdb_x4_esrgan.pth`; model zoo material may also use legacy names such as `RRDB.pth` or `ESRGAN.pth` | `testsets/set5`, `testsets/srbsd68` | Verify filename compatibility before running. If a downloader gives a legacy name, rename/symlink deliberately rather than silently changing the script. |
| IMDN x4 SR | `main_test_imdn.py` | hard-coded | `imdn_x4.pth` | `testsets/set5`, `testsets/srbsd68` | Lightweight SR model. Also usable in challenge profiling with `model_id = 1`. |
| USRNet / USRGAN blind SR | `main_test_usrnet.py` | hard-coded | `usrnet.pth`, `usrgan.pth`, `usrnet_tiny.pth`, `usrgan_tiny.pth` | `testsets/set5`, `testsets/srbsd68`, plus `kernels/kernels_12.mat` | Uses blur kernels and loops across scales/kernels. `usrnet` usually tests scales 2/3/4; GAN variants are x4-oriented. |
| SwinIR classical SR | `main_test_swinir.py` | argparse | `model_zoo/swinir/001_classicalSR_DIV2K_s48w8_SwinIR-M_x{2,3,4,8}.pth`; `model_zoo/swinir/001_classicalSR_DF2K_s64w8_SwinIR-M_x{2,3,4,8}.pth` | Paired `--folder_lq` and `--folder_gt`, e.g. `testsets/set5/LR_bicubic/X4` and `testsets/set5/HR` | `--training_patch_size` selects matching checkpoint family (`48` or `64`). |
| SwinIR lightweight SR | `main_test_swinir.py` | argparse | `model_zoo/swinir/002_lightweightSR_DIV2K_s64w8_SwinIR-S_x{2,3,4}.pth` | Paired LR/GT folders | Smaller SwinIR-S model; pass task `lightweight_sr`. |
| SwinIR real-world SR | `main_test_swinir.py` | argparse | `model_zoo/swinir/003_realSR_BSRGAN_DFO_s64w8_SwinIR-M_x4_GAN.pth`; large-model variant `003_realSR_BSRGAN_DFOWMFC_s64w8_SwinIR-L_x4_GAN.pth` | LQ-only `--folder_lq`, e.g. `testsets/RealSRSet+5images` or custom images | Use `--tile 400` or another multiple of 8 if OOM. Add `--large_model` only for the large checkpoint. |
| SwinIR grayscale denoising | `main_test_swinir.py` | argparse | `model_zoo/swinir/004_grayDN_DFWB_s128w8_SwinIR-M_noise{15,25,50}.pth` | Clean GT folder via `--folder_gt`, e.g. `testsets/set12` | Script generates noisy grayscale input using `--noise`. |
| SwinIR color denoising | `main_test_swinir.py` | argparse | `model_zoo/swinir/005_colorDN_DFWB_s128w8_SwinIR-M_noise{15,25,50}.pth` | Clean GT folder via `--folder_gt`, e.g. `testsets/McMaster` | Script generates noisy color input using `--noise`. |
| SwinIR JPEG CAR | `main_test_swinir.py` | argparse | `model_zoo/swinir/006_CAR_DFWB_s126w7_SwinIR-M_jpeg{10,20,30,40}.pth` | Clean GT folder via `--folder_gt`, e.g. `testsets/classic5` | Uses window size 7; tile must be a multiple of 7. Reports PSNR-B in addition to PSNR/SSIM. |
| GPEN face enhancement | `main_test_face_enhancement.py` | hard-coded | `model_zoo/RetinaFace-R50.pth` and `model_zoo/GPEN-BFR-512.pth` (older comments also mention `GPEN-512.pth`) | Input `testsets/real_faces`; output `testsets/real_faces_results` | Requires face-enhancer custom op import to find `models/op`; CUDA is strongly recommended. |
| Challenge profiling | `main_challenge_sr.py` | hard-coded | `model_zoo/msrresnet_x4_psnr.pth` or `model_zoo/imdn_x4.pth` | `testsets/set12`, `DIV2K_valid_LR`, or patched folder | Reference-only. Designed for FLOPs/activations/params/runtime/max-memory reporting, not normal benchmark evaluation. CUDA required for runtime/memory timing. |

## Model-zoo groups relevant to image testing

The original downloader recognizes both groups and individual filenames. Root integration owns the dry-run/execute downloader implementation; use these group names for lookup:

| Group | Included image checkpoints |
|---|---|
| `DnCNN` | `dncnn_15.pth`, `dncnn_25.pth`, `dncnn_50.pth`, `dncnn3.pth`, `dncnn_color_blind.pth`, `dncnn_gray_blind.pth` |
| `FFDNet` | `ffdnet_color.pth`, `ffdnet_gray.pth`, `ffdnet_color_clip.pth`, `ffdnet_gray_clip.pth` |
| `IRCNN` | `ircnn_color.pth`, `ircnn_gray.pth` |
| `SRMD` | `srmdnf_x2.pth`, `srmdnf_x3.pth`, `srmdnf_x4.pth`, `srmd_x2.pth`, `srmd_x3.pth`, `srmd_x4.pth` |
| `DPSR` | `dpsr_x2.pth`, `dpsr_x3.pth`, `dpsr_x4.pth`, `dpsr_x4_gan.pth` |
| `USRNet` | `usrgan.pth`, `usrgan_tiny.pth`, `usrnet.pth`, `usrnet_tiny.pth` |
| `SwinIR` | All `001_*` through `006_*` SwinIR image checkpoints; stored under `model_zoo/swinir/` |
| `BSRGAN` | `BSRGAN.pth`, `BSRNet.pth`, `BSRGANx2.pth`; useful for related real-SR model-zoo lookup even when the chosen image entry point is SwinIR/other SR |
| `DPIR` | `drunet_gray.pth`, `drunet_color.pth`, `drunet_deblocking_color.pth`, `drunet_deblocking_grayscale.pth`; model-zoo lookup only for this sub-skill unless a matching entry point is explicitly added in a local checkout |
| `others` | `msrresnet_x4_psnr.pth`, `msrresnet_x4_gan.pth`, `imdn_x4.pth`, `RRDB.pth`, `ESRGAN.pth`, `FSSR_DPED.pth`, `FSSR_JPEG.pth`, `RealSR_DPED.pth`, `RealSR_JPEG.pth` |

## Default result naming

- Older hard-coded image scripts generally write to `results/<testset_name>_<model_name>/` and create a log file with the same stem.
- `main_test_dncnn.py` follows the same pattern but lets `--results` and `--testset_name` change it.
- SwinIR writes to task-derived directories such as `results/swinir_real_sr_x4`, `results/swinir_color_dn_noise25`, or `results/swinir_jpeg_car_jpeg30` and saves images as `<image>_SwinIR.png`.
- Face enhancement writes under `testsets/real_faces_results` by default rather than `results/`.
