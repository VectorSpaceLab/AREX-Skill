# KAIR image-training troubleshooting

Use this reference when KAIR image training fails before useful iterations begin, resumes from an unexpected checkpoint, or runs with the wrong data/GPU behavior.

## Option JSON parse failures

Symptoms:

- `json.decoder.JSONDecodeError` or a failure in `utils_option.parse`.
- A config copied from KAIR seems valid in the repo but a generic JSON parser rejects it.

Facts and fixes:

- KAIR option files are JSON with `//` line comments. KAIR strips comments before `json.loads`.
- Do not remove comments by deleting arbitrary text inside strings. Use the bundled validator first:

  ```bash
  python sub-skills/image-training/scripts/validate_training_config.py --config options/train_msrresnet_psnr.json
  ```

- Trailing commas are still invalid; KAIR only strips `//` comments.
- Keep string paths quoted. JSON booleans are lowercase `true` and `false`, not Python `True`/`False`.

## `Dataset [...] is not found`

Likely causes:

- `datasets.<phase>.dataset_type` is misspelled.
- A video dataset type was placed in an image-training config.
- The chosen entry script is wrong for the config family.

Common image `dataset_type` values:

- Denoising: `dncnn`, `dnpatch`, `fdncnn`, `ffdnet`.
- Super-resolution: `sr`, `srmd`, `dpsr`, `usrnet`, `usrgan`, `blindsr`, `bsrgan`, `bsrnet`.
- JPEG deblocking: `jpeg`.
- Generic: `plain`, `plainpatch`, `l`, `low-quality`, `input-only`.

Route video dataset types such as `VideoRecurrentTrainDataset` to `../video-restoration/SKILL.md` and data layout checks to `../data-preparation/SKILL.md`.

## `netG [...] is not found` or wrong model wrapper

Likely causes:

- `netG.net_type` is not one of KAIR's selector names.
- `model` does not match the selected wrapper.
- A GAN config is launched through the PSNR script or a USRNet config is launched through the wrong entry point.

Common `netG.net_type` values:

```text
dncnn, fdncnn, ffdnet, srmd, dpsr, msrresnet0, msrresnet1,
rrdb, rrdbnet, imdn, usrnet, drunet, swinir, vrt, rvrt
```

Script routing reminders:

- `model: gan` → `main_train_gan.py`.
- `netG.net_type: drunet` → `main_train_drunet.py`.
- `netG.net_type: usrnet` or `model: plain4` → `main_train_usrnet.py`.
- `netG.net_type` in `dncnn`, `fdncnn`, `ffdnet` → usually `main_train_dncnn.py` for image denoising templates.
- SwinIR image configs use `main_train_psnr.py` for PSNR-style configs and the matching GAN path only when `model: gan`.
- VRT/RVRT configs are owned by `../video-restoration/SKILL.md`.

## Data root is missing or empty

Symptoms:

- Dataset length is zero.
- File-not-found around `dataroot_H`, `dataroot_L`, `dataroot_gt`, or `meta_info_file`.
- Training starts but immediately fails in a `DataLoader` worker.

Fixes:

1. Confirm paths are relative to the current KAIR checkout or absolute paths intentionally chosen by the user.
2. For image training, check `dataroot_H` and `dataroot_L` with the data-preparation checker:

   ```bash
   python sub-skills/data-preparation/scripts/check_dataset_layout.py image --root trainsets/trainH
   ```

3. For paired SR, ensure LQ/GT naming follows the selected dataset class. Some test scripts tolerate `x4` suffixes; training is safer with aligned stems.
4. For video or LMDB roots, use `../data-preparation/SKILL.md` instead of guessing.

## `gpu_ids`, `CUDA_VISIBLE_DEVICES`, and DDP mismatch

Facts:

- `utils_option.parse` sets `CUDA_VISIBLE_DEVICES` from the JSON `gpu_ids` list.
- DDP scripts then divide `dataloader_batch_size` and `dataloader_num_workers` by `num_gpu`.
- `main_train_dncnn.py` and `main_train_usrnet.py` do not parse `--dist`; use DataParallel for those templates unless you modify the source.

Fixes:

1. Make JSON `gpu_ids` length match launcher `--nproc_per_node` for DDP.
2. If a shell already masks devices with `CUDA_VISIBLE_DEVICES`, treat JSON ids as local visible ids.
3. Use a unique `--master_port` if another distributed job is running.
4. If one rank fails with data or checkpoint errors, read the first rank's stderr; DDP often reports secondary failures after the real one.

## Unexpected resume or ignored `pretrained_netG`

Symptoms:

- Training starts from a nonzero iteration.
- A JSON `path.pretrained_netG` appears to be ignored.
- A run intended to start fresh loads an old model or optimizer.

Facts:

- KAIR derives `<path.root>/<task>/models` and scans it for numbered checkpoint files.
- The latest numeric files overwrite `path.pretrained_netG`, `path.pretrained_netE`, discriminator, and optimizer preload keys in memory.
- Current step is the maximum discovered iteration among relevant model/optimizer files.

Fixes:

- To resume: keep the same `task` and `path.root` and retain numbered checkpoint files.
- To start fresh: choose a new `task`, a new `path.root`, or an empty models directory.
- To fine-tune without inheriting optimizer/iteration state: use a new experiment directory and deliberately stage only the intended initial model, or make a local script change that preserves the JSON pretrained path.
- Avoid `latest_G.pth` if the helper expects numeric names such as `5000_G.pth`.

## GAN multi-GPU training is slow or not using all GPUs

The KAIR README notes that one historical GAN training path disabled `DataParallel` in `models/model_gan.py`. If a GAN run uses only one GPU despite multiple visible GPUs:

1. Confirm the chosen checkout still has that behavior.
2. Prefer DDP with `main_train_gan.py --dist True` when possible.
3. If using DataParallel, inspect the local `model_gan` wrapper and make a deliberate local patch only after preserving the original file.

## Out of memory

Common fixes:

- Reduce `datasets.train.dataloader_batch_size`.
- Reduce patch size such as `H_size`, `gt_size`, or SwinIR image size where the config supports it.
- Reduce DDP per-rank batch by lowering total batch or process count.
- Disable x8/self-ensemble in testing workflows; this sub-skill is for training, but users often confuse the flags.
- For VRT/RVRT, route to `../video-restoration/SKILL.md` and adjust temporal/spatial tile settings.

## Dependency or CUDA import errors before training

Symptoms:

- `ModuleNotFoundError` for `cv2`, `lmdb`, `timm`, `einops`, `hdf5storage`, or `torchvision`.
- Custom CUDA extension build errors for VRT/RVRT or face enhancement.

Fixes:

- Install PyTorch plus KAIR `requirement.txt` dependencies.
- For image-only training, most configs do not need custom CUDA extension builds beyond PyTorch itself.
- For VRT/RVRT and custom ops, route to `../video-restoration/SKILL.md` and ensure CUDA, `ninja`, and a compatible compiler/toolkit are available.

## Validation before expensive launch

Run the read-only validator before a long run:

```bash
python sub-skills/image-training/scripts/validate_training_config.py --config <option-json>
```

Treat a clean validator result as a structural preflight only. It does not prove the data, checkpoints, CUDA runtime, or full training loop will succeed.
