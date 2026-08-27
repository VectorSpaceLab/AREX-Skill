# VRT/RVRT task reference

Use this table to choose KAIR video restoration task IDs, checkpoints, training
configs, and common test arguments. The checkpoint name is always the full task
string plus `.pth` under `model_zoo/vrt/` or `model_zoo/rvrt/`.

## VRT tasks (`main_test_vrt.py`, IDs `001`-`009`)

| ID | Full `--task` value | Purpose | Common datasets | Checkpoint path | Training config | Common test args |
|---|---|---|---|---|---|---|
| `001` | `001_VRT_videosr_bi_REDS_6frames` | Video SR, bicubic x4, REDS-trained 6-frame VRT | Train REDS sharp/sharp_bicubic; test REDS4 | `model_zoo/vrt/001_VRT_videosr_bi_REDS_6frames.pth` | `options/vrt/001_train_vrt_videosr_bi_reds_6frames.json` | `--folder_lq testsets/REDS4/sharp_bicubic --folder_gt testsets/REDS4/GT --tile 40 128 128 --tile_overlap 2 20 20` |
| `002` | `002_VRT_videosr_bi_REDS_16frames` | Video SR, bicubic x4, REDS-trained 16-frame VRT | Train REDS sharp/sharp_bicubic; test REDS4 | `model_zoo/vrt/002_VRT_videosr_bi_REDS_16frames.pth` | `options/vrt/002_train_vrt_videosr_bi_reds_16frames.json` | `--folder_lq testsets/REDS4/sharp_bicubic --folder_gt testsets/REDS4/GT --tile 40 128 128 --tile_overlap 2 20 20` |
| `003` | `003_VRT_videosr_bi_Vimeo_7frames` | Video SR, bicubic x4, Vimeo-trained 7-frame VRT | Train Vimeo90K; test Vid4 or Vimeo90K-T | `model_zoo/vrt/003_VRT_videosr_bi_Vimeo_7frames.pth` | `options/vrt/003_train_vrt_videosr_bi_vimeo_7frames.json` | Vid4: `--folder_lq testsets/Vid4/BIx4 --folder_gt testsets/Vid4/GT --tile 32 128 128 --tile_overlap 2 20 20`; Vimeo: `--folder_lq testsets/vimeo90k/vimeo_septuplet_matlabLRx4/sequences --folder_gt testsets/vimeo90k/vimeo_septuplet/sequences --tile 8 0 0 --tile_overlap 0 20 20` |
| `004` | `004_VRT_videosr_bd_Vimeo_7frames` | Video SR, blur-downsampling x4, Vimeo-trained 7-frame VRT | Train Vimeo90K BD; test Vid4, UDM10, or Vimeo90K-T | `model_zoo/vrt/004_VRT_videosr_bd_Vimeo_7frames.pth` | `options/vrt/004_train_vrt_videosr_bd_vimeo_7frames.json` | Vid4: `--folder_lq testsets/Vid4/BDx4 --folder_gt testsets/Vid4/GT --tile 32 128 128 --tile_overlap 2 20 20`; UDM10 uses `testsets/UDM10/BDx4` and `testsets/UDM10/GT`; Vimeo uses `vimeo_septuplet_BDLRx4/sequences` and `--tile 8 0 0 --tile_overlap 0 20 20` |
| `005` | `005_VRT_videodeblurring_DVD` | Video deblurring, DVD motion blur | Train DVD; test DVD10 | `model_zoo/vrt/005_VRT_videodeblurring_DVD.pth` | `options/vrt/005_train_vrt_videodeblurring_dvd.json` | `--folder_lq testsets/DVD10/test_GT_blurred --folder_gt testsets/DVD10/test_GT --tile 12 256 256 --tile_overlap 2 20 20` |
| `006` | `006_VRT_videodeblurring_GoPro` | Video deblurring, GoPro motion blur | Train GoPro; test GoPro11 | `model_zoo/vrt/006_VRT_videodeblurring_GoPro.pth` | `options/vrt/006_train_vrt_videodeblurring_gopro.json` | `--folder_lq testsets/GoPro11/test_GT_blurred --folder_gt testsets/GoPro11/test_GT --tile 18 192 192 --tile_overlap 2 20 20` |
| `007` | `007_VRT_videodeblurring_REDS` | Video deblurring, REDS blur | Train REDS sharp/blur; test REDS4 | `model_zoo/vrt/007_VRT_videodeblurring_REDS.pth` | `options/vrt/007_train_vrt_videodeblurring_reds.json` | `--folder_lq testsets/REDS4/blur --folder_gt testsets/REDS4/GT --tile 12 256 256 --tile_overlap 2 20 20` |
| `008` | `008_VRT_videodenoising_DAVIS` | Non-blind video denoising, sigma 0-50 | Train DAVIS; test Set8 or DAVIS-test | `model_zoo/vrt/008_VRT_videodenoising_DAVIS.pth` | `options/vrt/008_train_vrt_videodenoising_davis.json` | `--sigma 10 --folder_lq testsets/Set8 --folder_gt testsets/Set8 --tile 12 256 256 --tile_overlap 2 20 20`; DAVIS-test uses `testsets/DAVIS-test` for both folders |
| `009` | `009_VRT_videofi_Vimeo_4frames` | Video frame interpolation, Vimeo-trained single-frame interpolation | Train Vimeo90K; test Vimeo90K-T, UCF101, DAVIS-train, or Vid4-style data | `model_zoo/vrt/009_VRT_videofi_Vimeo_4frames.pth` | `options/vrt/009_train_vrt_videofi_vimeo_4frames.json` | Vimeo: `--folder_lq testsets/vimeo90k/vimeo_septuplet/sequences --folder_gt testsets/vimeo90k/vimeo_septuplet/sequences --tile 0 0 0 --tile_overlap 0 0 0`; UCF101 similar with `testsets/UCF101`; DAVIS-train uses `--tile 0 256 256 --tile_overlap 0 20 20` |

### VRT notes

- VRT space-time video SR is not exposed as a separate task ID. Use the Vimeo SR
  task (`003`) and frame interpolation task (`009`) as the building blocks.
- VRT denoising task `008` is non-blind: pass `--sigma` and use the DAVIS/Set8
  denoising command patterns. With GT, KAIR injects noise internally and
  computes metrics against clean frames.
- VRT training configs all use `main_train_vrt.py`; the filename prefix
  (`001_train_vrt_...`) is not the same string as the inference `--task` value.

## RVRT tasks (`main_test_rvrt.py`, IDs `001`-`006`)

| ID | Full `--task` value | Purpose | Common datasets | Checkpoint path | Training config | Common test args |
|---|---|---|---|---|---|---|
| `001` | `001_RVRT_videosr_bi_REDS_30frames` | Video SR, bicubic x4, REDS-trained recurrent 30-frame RVRT | Train REDS sharp/sharp_bicubic; test REDS4 | `model_zoo/rvrt/001_RVRT_videosr_bi_REDS_30frames.pth` | `options/rvrt/001_train_rvrt_videosr_bi_reds_30frames.json` | `--folder_lq testsets/REDS4/sharp_bicubic --folder_gt testsets/REDS4/GT --tile 100 128 128 --tile_overlap 2 20 20` |
| `002` | `002_RVRT_videosr_bi_Vimeo_14frames` | Video SR, bicubic x4, Vimeo-trained 14-frame RVRT | Train Vimeo90K; test Vid4 or Vimeo90K-T | `model_zoo/rvrt/002_RVRT_videosr_bi_Vimeo_14frames.pth` | `options/rvrt/002_train_rvrt_videosr_bi_vimeo_14frames.json` | Vid4: `--folder_lq testsets/Vid4/BIx4 --folder_gt testsets/Vid4/GT --tile 0 0 0 --tile_overlap 2 20 20`; Vimeo: `--folder_lq testsets/vimeo90k/vimeo_septuplet_matlabLRx4/sequences --folder_gt testsets/vimeo90k/vimeo_septuplet/sequences --tile 0 0 0 --tile_overlap 0 20 20` |
| `003` | `003_RVRT_videosr_bd_Vimeo_14frames` | Video SR, blur-downsampling x4, Vimeo-trained 14-frame RVRT | Train Vimeo90K BD; test Vid4, UDM10, or Vimeo90K-T | `model_zoo/rvrt/003_RVRT_videosr_bd_Vimeo_14frames.pth` | `options/rvrt/003_train_rvrt_videosr_bd_vimeo_14frames.json` | Vid4: `--folder_lq testsets/Vid4/BDx4 --folder_gt testsets/Vid4/GT --tile 0 0 0 --tile_overlap 2 20 20`; UDM10 uses `testsets/UDM10/BDx4` and `testsets/UDM10/GT`; Vimeo uses `vimeo_septuplet_BDLRx4/sequences` and `--tile_overlap 0 20 20` |
| `004` | `004_RVRT_videodeblurring_DVD_16frames` | Video deblurring, DVD motion blur, 16-frame RVRT | Train DVD; test DVD10 | `model_zoo/rvrt/004_RVRT_videodeblurring_DVD_16frames.pth` | `options/rvrt/004_train_rvrt_videodeblurring_dvd.json` | `--folder_lq testsets/DVD10/test_GT_blurred --folder_gt testsets/DVD10/test_GT --tile 0 256 256 --tile_overlap 2 20 20` |
| `005` | `005_RVRT_videodeblurring_GoPro_16frames` | Video deblurring, GoPro motion blur, 16-frame RVRT | Train GoPro; test GoPro11 | `model_zoo/rvrt/005_RVRT_videodeblurring_GoPro_16frames.pth` | `options/rvrt/005_train_rvrt_videodeblurring_gopro.json` | `--folder_lq testsets/GoPro11/test_GT_blurred --folder_gt testsets/GoPro11/test_GT --tile 0 256 256 --tile_overlap 2 20 20` |
| `006` | `006_RVRT_videodenoising_DAVIS_16frames` | Non-blind video denoising, sigma 0-50, 16-frame RVRT | Train DAVIS; test Set8 or DAVIS-test | `model_zoo/rvrt/006_RVRT_videodenoising_DAVIS_16frames.pth` | `options/rvrt/006_train_rvrt_videodenoising_davis.json` | `--sigma 50 --folder_lq testsets/Set8 --folder_gt testsets/Set8 --tile 0 256 256 --tile_overlap 2 20 20`; DAVIS-test uses `testsets/DAVIS-test` for both folders |

### RVRT notes

- RVRT imports the guided deformable attention custom CUDA extension. Parser
  help may be safe once the extension has been built, but full RVRT workflows
  should be treated as CUDA/nvcc/ninja dependent.
- RVRT task IDs are only `001`-`006`; VRT's frame interpolation task `009` has no
  RVRT equivalent in KAIR's RVRT test script.
- RVRT commonly uses larger temporal coverage and lower memory than VRT for some
  comparable tasks, but its custom extension can be the first point of failure.

## Training config quick map

| Family | IDs | Config directory | Shared training entry point | Typical dataset backend |
|---|---|---|---|---|
| VRT | `001`-`009` | `options/vrt/` | `main_train_vrt.py` | LMDB for training configs, disk folders for validation/test |
| RVRT | `001`-`006` | `options/rvrt/` | `main_train_vrt.py` | LMDB for training configs, disk folders for validation/test |

Training command pattern:

```bash
python -m torch.distributed.launch --nproc_per_node=8 --master_port=1234 \
  main_train_vrt.py --opt <config-path> --dist True
```

For a local non-distributed smoke, omit `--dist` entirely:

```bash
python main_train_vrt.py --opt <config-path>
```
