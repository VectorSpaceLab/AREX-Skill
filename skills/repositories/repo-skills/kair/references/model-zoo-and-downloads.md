# KAIR model zoo and downloads

KAIR native test scripts often assume checkpoints live under `model_zoo/`. Some scripts attempt automatic downloads when a checkpoint is missing. Prefer an explicit dry run and user-approved download before launching expensive inference.

## Download helper

Dry-run selected checkpoints from the KAIR root:

```bash
python skills/disco/kair/scripts/kair_download_models.py --models "dncnn_25.pth 003_realSR_BSRGAN_DFO_s64w8_SwinIR-M_x4_GAN.pth"
```

Download after reviewing paths and network/disk budget:

```bash
python skills/disco/kair/scripts/kair_download_models.py --models "DnCNN" --execute
```

Avoid downloading everything unless the user explicitly confirms storage and network budget:

```bash
python skills/disco/kair/scripts/kair_download_models.py --models all --allow-all --execute
```

## Destination conventions

| Checkpoint family | Destination root | URL family |
| --- | --- | --- |
| DnCNN, FFDNet, SRMD, DPSR, USRNet, DPIR, BSRGAN, IRCNN, MSRResNet/RRDB/IMDN/RealSR/FSSR | `model_zoo/<file>.pth` | KAIR GitHub release `v1.0` |
| SwinIR | `model_zoo/swinir/<file>.pth` | SwinIR GitHub release `v0.0` |
| VRT | `model_zoo/vrt/<file>.pth` | VRT GitHub release `v0.0` |
| RVRT | `model_zoo/rvrt/<file>.pth` | RVRT GitHub release `v0.0` |

## Common image checkpoint groups

| Group | Typical use | Included names in helper |
| --- | --- | --- |
| `DnCNN` | grayscale/color fixed/blind denoising and deblocking | `dncnn_15.pth`, `dncnn_25.pth`, `dncnn_50.pth`, `dncnn3.pth`, `dncnn_color_blind.pth`, `dncnn_gray_blind.pth` |
| `FFDNet` | flexible grayscale/color denoising | `ffdnet_color.pth`, `ffdnet_gray.pth`, clip variants |
| `SRMD` | degradation-aware SISR | `srmdnf_x2/x3/x4.pth`, `srmd_x2/x3/x4.pth` |
| `DPSR` | plug-and-play/degradation-aware SR | `dpsr_x2/x3/x4.pth`, `dpsr_x4_gan.pth` |
| `USRNet` | unfolding SR | `usrnet.pth`, `usrnet_tiny.pth`, `usrgan.pth`, `usrgan_tiny.pth` |
| `DPIR` | DRUNet denoising/deblocking | `drunet_gray.pth`, `drunet_color.pth`, deblocking variants |
| `BSRGAN` | blind/real-world SR | `BSRGAN.pth`, `BSRNet.pth`, `BSRGANx2.pth` |
| `IRCNN` | classic denoising prior | `ircnn_color.pth`, `ircnn_gray.pth` |
| `others` | hard-coded legacy image scripts | `msrresnet_x4_psnr.pth`, `msrresnet_x4_gan.pth`, `imdn_x4.pth`, `RRDB.pth`, `ESRGAN.pth`, `FSSR_*.pth`, `RealSR_*.pth` |

## SwinIR checkpoints

Use `../sub-skills/image-testing/` for command selection. Important names include:

- Classical SR: `001_classicalSR_DF2K_s64w8_SwinIR-M_x2/x3/x4/x8.pth` and DIV2K variants.
- Lightweight SR: `002_lightweightSR_DIV2K_s64w8_SwinIR-S_x2/x3/x4.pth`.
- Real-world SR: `003_realSR_BSRGAN_DFO_s64w8_SwinIR-M_x4_GAN.pth` and PSNR variant.
- Grayscale denoising: `004_grayDN_DFWB_s128w8_SwinIR-M_noise15/25/50.pth`.
- Color denoising: `005_colorDN_DFWB_s128w8_SwinIR-M_noise15/25/50.pth`.
- JPEG artifact reduction: `006_CAR_DFWB_s126w7_SwinIR-M_jpeg10/20/30/40.pth`.

## VRT/RVRT checkpoints

Use `../sub-skills/video-restoration/` for full task IDs, dataset folders, and tiling. The helper includes all public VRT task checkpoints `001`-`009` and all RVRT task checkpoints `001`-`006`.

## Auto-download caveats

- `main_test_swinir.py`, `main_test_vrt.py`, and `main_test_rvrt.py` can download missing checkpoints or some testsets during normal execution. This is convenient but makes runs non-hermetic.
- Download failures can leave partial files. Remove incomplete files or use the root downloader helper, which writes `.part` then renames after success.
- Checkpoints are large; VRT/RVRT groups in particular can consume substantial storage.
- Downloaded checkpoints are runtime data, not skill artifacts. Do not commit them into the generated skill tree.
