# KAIR Image Testing Workflows

This page distills KAIR image-testing behavior so agents can run or adapt workflows without reopening repository documentation. Commands assume they are executed from a user's KAIR checkout after installing PyTorch plus `requirement.txt` dependencies.

## Choose the script style first

KAIR image testing has two different styles:

- **Argparse scripts**: `main_test_dncnn.py` and `main_test_swinir.py` expose useful CLI arguments. Prefer the bundled dry-run helper to assemble these commands.
- **Hard-coded scripts**: most older image scripts set `model_name`, `testset_name`, `model_pool`, `testsets`, `results`, and task-specific constants inside the script. Do not copy these scripts into a skill. Make a working copy or patch only the constants required for the user's checkout, then run the KAIR entry point.

Safe parser checks before full inference:

```bash
python main_test_dncnn.py --help
python main_test_swinir.py --help
python main_download_pretrained_models.py --help
```

Full inference also needs local images and checkpoint files. Downloads can be networked and large; route checkpoint acquisition through the root model-zoo/download reference or root downloader helper.

## Dry-run command builder

The bundled helper does not import KAIR and never runs downloads or inference. It prints shell commands and notes.

DnCNN example for Set12, sigma 25:

```bash
python sub-skills/image-testing/scripts/build_image_test_command.py dncnn \
  --model-name dncnn_25 \
  --testset-name set12 \
  --noise-level 25 \
  --model-pool model_zoo \
  --testsets testsets \
  --results results
```

Typical output command:

```bash
python main_test_dncnn.py --model_name dncnn_25 --testset_name set12 --noise_level_img 25 --model_pool model_zoo --testsets testsets --results results
```

SwinIR real-world SR example for a custom folder with tiling:

```bash
python sub-skills/image-testing/scripts/build_image_test_command.py swinir \
  --task real_sr \
  --scale 4 \
  --folder-lq testsets/my_real_images \
  --tile 400
```

Typical output command:

```bash
python main_test_swinir.py --task real_sr --scale 4 --model_path model_zoo/swinir/003_realSR_BSRGAN_DFO_s64w8_SwinIR-M_x4_GAN.pth --folder_lq testsets/my_real_images --tile 400
```

Use `python sub-skills/image-testing/scripts/build_image_test_command.py hardcoded --family imdn` to print concise notes for hard-coded scripts such as IMDN, RRDB, USRNet, or face enhancement.

## Argparse workflow: DnCNN denoising

`main_test_dncnn.py` covers DnCNN Gaussian denoising and the DnCNN3 blind model through CLI arguments.

Key arguments:

- `--model_name`: one of `dncnn_15`, `dncnn_25`, `dncnn_50`, `dncnn_gray_blind`, `dncnn_color_blind`, `dncnn3`.
- `--testset_name`: dataset subfolder under `--testsets`, commonly `set12`, `bsd68`, or `cbsd68` if present.
- `--noise_level_img`: noise sigma injected into clean images when `--need_degradation` is true; common values are `15`, `25`, `50`.
- `--model_pool`: checkpoint directory, normally `model_zoo`.
- `--results`: output root, normally `results`.
- `--x8`: self-ensemble flag. The script declares it as `type=bool`; prefer leaving it omitted unless you know how the local Python parses the passed value.

Behavior:

- The script reads images from `testsets/<testset_name>` unless `--testsets` changes the root.
- If low-quality and high-quality paths are identical, it generates additive Gaussian noise with a fixed NumPy seed for reproducibility.
- It writes restored images to `results/<testset_name>_<model_name>/` and logs per-image plus average PSNR/SSIM there.
- Grayscale versus color channel count is selected from the checkpoint name: names containing `color` use 3 channels; the others use 1 channel.

## Argparse workflow: SwinIR

`main_test_swinir.py` supports these tasks:

| Task | Main use | Required image folder argument | Common checkpoint |
|---|---|---|---|
| `classical_sr` | Bicubic single-image SR | `--folder_lq` and `--folder_gt` | `model_zoo/swinir/001_classicalSR_*_SwinIR-M_x{2,3,4,8}.pth` |
| `lightweight_sr` | Smaller SwinIR SR | `--folder_lq` and `--folder_gt` | `model_zoo/swinir/002_lightweightSR_DIV2K_s64w8_SwinIR-S_x{2,3,4}.pth` |
| `real_sr` | Real-world blind SR | `--folder_lq` only | `model_zoo/swinir/003_realSR_BSRGAN_DFO_s64w8_SwinIR-M_x4_GAN.pth` or large-model variant |
| `gray_dn` | Grayscale denoising | `--folder_gt` | `model_zoo/swinir/004_grayDN_DFWB_s128w8_SwinIR-M_noise{15,25,50}.pth` |
| `color_dn` | Color denoising | `--folder_gt` | `model_zoo/swinir/005_colorDN_DFWB_s128w8_SwinIR-M_noise{15,25,50}.pth` |
| `jpeg_car` | JPEG artifact reduction | `--folder_gt` | `model_zoo/swinir/006_CAR_DFWB_s126w7_SwinIR-M_jpeg{10,20,30,40}.pth` |

Important SwinIR details:

- If `--model_path` does not exist, the original script attempts a network download from the SwinIR release URL. Prefer explicit root downloader use when the run must avoid surprise network access.
- `--training_patch_size` is a model-setting selector for classical SR (`48`, `64`, or task default), not a patch-by-patch inference setting.
- `--large_model` is only for the larger real-world SR checkpoint and appends `_large` to the result directory.
- `--tile` enables tiled inference for OOM-prone images. Tile size must be a multiple of the task window size (`8` for most SwinIR tasks, `7` for JPEG CAR). `--tile_overlap` defaults to `32`.
- Result directories are `results/swinir_<task>_x<scale>`, `results/swinir_<task>_noise<noise>`, or `results/swinir_<task>_jpeg<jpeg>` depending on the task. Output filenames end in `_SwinIR.png`.

### SwinIR examples

Classical SR x4 with paired LR/GT folders:

```bash
python main_test_swinir.py \
  --task classical_sr \
  --scale 4 \
  --training_patch_size 64 \
  --model_path model_zoo/swinir/001_classicalSR_DF2K_s64w8_SwinIR-M_x4.pth \
  --folder_lq testsets/set5/LR_bicubic/X4 \
  --folder_gt testsets/set5/HR
```

Real-world SR x4 on a custom folder, tiled to reduce peak memory:

```bash
python main_test_swinir.py \
  --task real_sr \
  --scale 4 \
  --model_path model_zoo/swinir/003_realSR_BSRGAN_DFO_s64w8_SwinIR-M_x4_GAN.pth \
  --folder_lq testsets/my_real_images \
  --tile 400
```

Large real-world SR model:

```bash
python main_test_swinir.py \
  --task real_sr \
  --scale 4 \
  --large_model \
  --model_path model_zoo/swinir/003_realSR_BSRGAN_DFOWMFC_s64w8_SwinIR-L_x4_GAN.pth \
  --folder_lq testsets/my_real_images \
  --tile 400
```

Color denoising sigma 25:

```bash
python main_test_swinir.py \
  --task color_dn \
  --noise 25 \
  --model_path model_zoo/swinir/005_colorDN_DFWB_s128w8_SwinIR-M_noise25.pth \
  --folder_gt testsets/McMaster
```

JPEG artifact reduction quality 30:

```bash
python main_test_swinir.py \
  --task jpeg_car \
  --jpeg 30 \
  --model_path model_zoo/swinir/006_CAR_DFWB_s126w7_SwinIR-M_jpeg30.pth \
  --folder_gt testsets/classic5
```

## Hard-coded image test scripts

For the following scripts, edit constants in a local working copy instead of expecting command-line arguments:

- Denoising/deblocking: `main_test_fdncnn.py`, `main_test_ffdnet.py`, `main_test_ircnn_denoiser.py`, `main_test_dncnn3_deblocking.py`.
- Super-resolution/blind SR: `main_test_srmd.py`, `main_test_dpsr.py`, `main_test_msrresnet.py`, `main_test_rrdb.py`, `main_test_imdn.py`, `main_test_usrnet.py`.
- Face enhancement: `main_test_face_enhancement.py`.
- Challenge profiling: `main_challenge_sr.py`.

Constants usually to patch:

```text
model_name      # checkpoint stem without .pth for most scripts
testset_name    # subfolder under testsets
model_pool      # checkpoint root, normally model_zoo
testsets        # image dataset root, normally testsets
results         # result root, normally results
noise_level_img # denoising or synthetic LR noise, if present
show_img        # keep False for headless runs
x8              # self-ensemble where present
sf/test_sf      # scale factor where not inferred from model_name
```

Guidelines:

- Patch only the constants needed for the user's checkout and keep an audit trail of the diff or command used.
- Do not treat these scripts as side-effect-free verification: they load checkpoints and process all images in the selected folder.
- Most SR scripts generate LR inputs from HR images when `L_path == H_path` and `need_degradation` is true; this is useful for benchmark evaluation but not the same as running on an externally prepared LR folder.
- USRNet additionally expects blur kernels such as `kernels/kernels_12.mat` and loops over scale/kernel combinations.

## Outputs and metrics

Common older scripts:

- Use `utils_image.get_image_paths`, which asserts the folder exists and contains at least one recognized image.
- Save outputs to a result folder named from `<testset_name>_<model_name>`.
- Compute PSNR/SSIM on `[0,255]` images. SR scripts also report Y-channel PSNR/SSIM after RGB-to-Y conversion.
- Use border cropping for SR (`border = scale`) and no border for denoising/deblocking unless a script-specific constant overrides it.

SwinIR:

- Saves `*_SwinIR.png` images.
- Computes RGB PSNR/SSIM when GT is available.
- Computes Y-channel metrics for RGB GT images.
- Computes PSNR-B for `jpeg_car`.
- Does not compute metrics for `real_sr` because it accepts LQ-only folders.

## Face enhancement flow

`main_test_face_enhancement.py` is a hard-coded GPEN workflow:

1. Place `RetinaFace-R50.pth` and `GPEN-BFR-512.pth` under `model_zoo/`.
2. Ensure `ninja`, PyTorch, CUDA-capable runtime, and the KAIR `models/` path for the face-enhancer `op` import are available.
3. Put input images under `testsets/real_faces` or patch `inputdir` in a working copy.
4. Run `python main_test_face_enhancement.py`.
5. Review outputs under `testsets/real_faces_results`: full comparison image, enhanced image, and per-face before/after crops when face detection is enabled.

The script uses RetinaFace detection/alignment by default. If `need_face_detection` is false, it enhances the whole input as one aligned face crop, which is only appropriate when images are already cropped/aligned.

## Challenge profiling caveat

`main_challenge_sr.py` is reference-only. It is hard-coded for `msrresnet` or `imdn`, x4 SR, `testsets/set12`/DIV2K-style folders, and logs FLOPs, activations, parameter count, runtime, and optional output images. Runtime and maximum-memory measurement require CUDA events and therefore a working CUDA device. For profiling IMDN FLOPs, patch `model_id = 1`, keep `print_modelsummary = True`, ensure `model_zoo/imdn_x4.pth` and images exist, and expect CUDA-side runtime code if measuring speed or memory.
