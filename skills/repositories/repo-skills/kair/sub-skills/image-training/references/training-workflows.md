# KAIR image training workflows

Use these workflows from the root of a KAIR checkout after installing PyTorch plus KAIR's `requirement.txt` dependencies. KAIR is a source-script repository, not an installable package, so training entry points are Python scripts in the checkout.

Full training can run for many hours or days. Treat commands below as launch templates, not smoke tests. For a safe pre-launch check, run `../scripts/validate_training_config.py --config <config>` from this sub-skill.

## Entry-point routing

| User intent | Typical option template | Entry script | Notes |
| --- | --- | --- | --- |
| DnCNN fixed-noise denoising | `options/train_dncnn.json` | `python main_train_dncnn.py -opt <config>` | Uses one-dash `-opt`; no distributed flags in this script. |
| FDnCNN / FFDNet-style denoising configs | `options/train_fdncnn.json`, `options/train_ffdnet.json` | `python main_train_dncnn.py -opt <config>` | Same denoising training loop; config selects `dataset_type`, `model`, and `netG.net_type`. |
| DRUNet denoising | `options/train_drunet.json` | `python main_train_drunet.py --opt <config>` | Supports `--dist True` with the source DDP launcher pattern. |
| USRNet super-resolution | `options/train_usrnet.json` | `python main_train_usrnet.py -opt <config>` | Uses `model: plain4` and dataset inputs `L`, `k`, `sf`, `sigma`; no distributed flags in this script. |
| PSNR SISR / restoration | `options/train_msrresnet_psnr.json`, `options/train_rrdb_psnr.json`, `options/train_imdn.json`, `options/train_srmd.json`, `options/train_dpsr.json`, `options/train_bsrgan_x4_psnr.json` | `python main_train_psnr.py --opt <config>` | General image PSNR loop; config selects dataset and generator network. |
| GAN SISR / blind SR | `options/train_msrresnet_gan.json`, `options/train_bsrgan_x4_gan.json` | `python main_train_gan.py --opt <config>` | Config must use `model: gan` and include `netD` plus GAN/perceptual loss keys. |
| SwinIR classical/lightweight SR | `options/swinir/train_swinir_sr_classical.json`, `options/swinir/train_swinir_sr_lightweight.json` | `python main_train_psnr.py --opt <config>` | Source SwinIR docs use DDP by default and DataParallel as the slower fallback. |
| SwinIR real-world SR | `options/swinir/train_swinir_sr_realworld_x4_psnr.json`, `options/swinir/train_swinir_sr_realworld_x4_gan.json` | `python main_train_psnr.py --opt <config>` | The GAN config still works through model selection because `model: gan`; prepare the PSNR-oriented checkpoint before GAN fine-tuning. |
| SwinIR denoising / JPEG deblocking | `options/swinir/train_swinir_denoising_gray.json`, `options/swinir/train_swinir_denoising_color.json`, `options/swinir/train_swinir_car_jpeg.json` | `python main_train_psnr.py --opt <config>` | Adjust noise level, JPEG quality, patch size, and dataset roots in JSON. |

Training entry scripts are reference-only command targets. They are not bundled in this skill because they launch long training, import KAIR source modules, and require the user's full checkout, data, and hardware.

## DataParallel launch templates

DataParallel is selected when the command omits `--dist True`. KAIR wraps the model in `torch.nn.DataParallel` when `dist` is false. `utils_option.parse` sets `CUDA_VISIBLE_DEVICES` from the JSON `gpu_ids` list.

```bash
# PSNR-style image SR/restoration
python main_train_psnr.py --opt options/train_msrresnet_psnr.json

# GAN training
python main_train_gan.py --opt options/train_msrresnet_gan.json

# DRUNet
python main_train_drunet.py --opt options/train_drunet.json

# DnCNN-style scripts use one dash for -opt
python main_train_dncnn.py -opt options/train_dncnn.json

# USRNet also uses one dash for -opt
python main_train_usrnet.py -opt options/train_usrnet.json
```

For multi-GPU DataParallel, edit `gpu_ids` in the JSON, for example `[0, 1, 2, 3]`. DataParallel is often slower than DDP for large SwinIR/GAN runs, but it avoids distributed launcher setup.

## DistributedDataParallel launch templates

Use DDP only with entry scripts that parse `--dist`: `main_train_psnr.py`, `main_train_gan.py`, and `main_train_drunet.py`. The source-documented launch style is:

```bash
python -m torch.distributed.launch \
  --nproc_per_node=4 \
  --master_port=1234 \
  main_train_psnr.py \
  --opt options/train_msrresnet_psnr.json \
  --dist True
```

GAN variant:

```bash
python -m torch.distributed.launch \
  --nproc_per_node=4 \
  --master_port=1234 \
  main_train_gan.py \
  --opt options/train_msrresnet_gan.json \
  --dist True
```

DRUNet variant:

```bash
python -m torch.distributed.launch \
  --nproc_per_node=4 \
  --master_port=1234 \
  main_train_drunet.py \
  --opt options/train_drunet.json \
  --dist True
```

For SwinIR, source docs use 8 GPUs. Reduce both JSON and launch count if fewer GPUs are available:

```bash
python -m torch.distributed.launch \
  --nproc_per_node=8 \
  --master_port=1234 \
  main_train_psnr.py \
  --opt options/swinir/train_swinir_sr_classical.json \
  --dist True
```

Modern `torchrun` can be used only if the user's PyTorch version and KAIR checkout accept the same distributed environment. The source-compatible command remains `python -m torch.distributed.launch`.

## Converting a single-GPU option to 4-GPU DDP

Example: adapt `train_msrresnet_psnr.json` to a new high-quality dataset root and 4 GPUs.

1. Copy the JSON to a new file, for example `options/train_msrresnet_psnr_custom4g.json`.
2. Set a new experiment name so old checkpoints do not auto-resume:
   - `task`: `msrresnet_psnr_custom4g`
   - optionally `path.root`: keep `superresolution` or choose another public experiment folder.
3. Set visible GPUs in the JSON:
   - `gpu_ids`: `[0, 1, 2, 3]`
   - `dist`: `true` for clarity, though the script also sets `opt['dist']` from `--dist`.
4. Set the dataset roots:
   - `datasets.train.dataroot_H`: path to HR training images.
   - `datasets.train.dataroot_L`: paired LR root only if you already have LR images; otherwise keep `null` for KAIR's on-the-fly bicubic LR behavior for `dataset_type: sr`.
   - update `datasets.test.dataroot_H` and `datasets.test.dataroot_L` or route dataset preparation to `../data-preparation/SKILL.md`.
5. Review total batch/workers. In DDP, KAIR divides `dataloader_batch_size` and `dataloader_num_workers` by `num_gpu`, so a value of `32` becomes `8` samples per rank across 4 GPUs.
6. Launch with matching process count:

```bash
python -m torch.distributed.launch \
  --nproc_per_node=4 \
  --master_port=1234 \
  main_train_psnr.py \
  --opt options/train_msrresnet_psnr_custom4g.json \
  --dist True
```

If `CUDA_VISIBLE_DEVICES` is already set by the shell, use JSON `gpu_ids` as local visible IDs (for example `[0, 1, 2, 3]` inside the masked device set), not necessarily physical GPU ordinals.

## PSNR versus GAN training

PSNR-oriented training uses `model: plain`, `plain2`, or `plain4` and optimizes a generator loss such as `l1`, `l2`, `l2sum`, `ssim`, or `charbonnier` depending on the model wrapper.

GAN training uses `model: gan` and adds:

- `netD` discriminator settings.
- perceptual loss keys such as `F_lossfn_type`, `F_lossfn_weight`, `F_feature_layer`, and `F_weights`.
- adversarial loss keys such as `gan_type` and `D_lossfn_weight`.
- separate `G_*` and `D_*` optimizer/scheduler keys.

For real-world SR, a common route is PSNR pretraining first, then GAN fine-tuning. In KAIR's SwinIR notes, the GAN phase expects a PSNR-oriented model to be available before the GAN run. Because KAIR's entry scripts auto-discover checkpoints in the derived models folder, read the next section before deciding how to provide that checkpoint.

## Checkpoint and resume behavior

At startup, KAIR's training scripts parse the option JSON, derive the experiment folders, then call `find_last_checkpoint` in the derived `path.models` directory. The derived models directory is:

```text
<path.root>/<task>/models
```

The scripts then overwrite `path.pretrained_netG`, `path.pretrained_netE`, `path.pretrained_netD`, and optimizer preload keys with the discovered latest files. The highest numeric checkpoint matching these patterns wins:

```text
<iteration>_G.pth
<iteration>_E.pth
<iteration>_D.pth
<iteration>_optimizerG.pth
<iteration>_optimizerD.pth
```

Current training step is initialized from the maximum discovered iteration among the relevant model and optimizer files. This is why a resumed run can start at a nonzero iteration even if the JSON `pretrained_*` fields are `null`.

Practical rules:

- To resume: keep `task` and `path.root` unchanged and leave the numbered checkpoint files in `<path.root>/<task>/models`.
- To start fresh: use a new `task`, new `path.root`, or an empty models directory.
- To fine-tune from a checkpoint without resuming the old iteration: do not rely on only setting `path.pretrained_netG` in JSON, because the entry scripts overwrite it. Use a new experiment directory and place a deliberately named initial checkpoint in its `models` folder, or make a conscious local script change that preserves the JSON pretrained path.
- Optimizer state is loaded only when an optimizer checkpoint is discovered and the relevant `G_optimizer_reuse` or `D_optimizer_reuse` key is true. Several SwinIR/BSRGAN templates set `G_optimizer_reuse: true`.
- `latest_G.pth` style names are not the numeric pattern expected by `find_last_checkpoint`; prefer numeric prefixes such as `0_G.pth`, `5000_G.pth`, or `100000_G.pth`.

## Source scripts copied, adapted, or excluded

- Training entry scripts are reference-only command templates because they import the full KAIR source tree and start long-running training.
- `utils_option.parse` behavior is distilled into `configuration-reference.md` and the bundled validator.
- JSON-with-line-comments parsing is adapted into `scripts/validate_training_config.py` so future agents can check configs without importing KAIR or launching training.
