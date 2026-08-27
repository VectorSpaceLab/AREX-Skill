---
name: image-training
description: "Choose, edit, validate, and launch KAIR image training
  configurations for denoising, super-resolution, blind SR, deblocking, PSNR,
  GAN, DataParallel, and DDP workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# KAIR image-training

Use this sub-skill when the task is to train or resume KAIR image restoration models, adapt KAIR training option JSON files, choose a training entry script, or diagnose training configuration failures for image workflows.

This sub-skill covers KAIR image training for DnCNN, FDnCNN, FFDNet, DRUNet, USRNet, SRMD, DPSR, MSRResNet, RRDB/RRDBNet, IMDN, BSRGAN-style blind SR, SwinIR image SR/denoising/JPEG deblocking, PSNR-oriented training, GAN training, DataParallel, and DistributedDataParallel.

Do not use this sub-skill for:

- image inference or metrics; route to `../image-testing/SKILL.md`.
- VRT/RVRT video restoration; route to `../video-restoration/SKILL.md`.
- dataset splitting, LMDB creation, video regrouping, or folder-layout repair; route to `../data-preparation/SKILL.md`.

## Start here

1. Identify the task family and use `references/training-workflows.md` to choose the KAIR command entry point and option JSON template.
2. Edit a copied option JSON using `references/configuration-reference.md`; do not treat the bundled examples as exhaustive source configs.
3. Run `scripts/validate_training_config.py --config <option-json>` before launching training. It is read-only and does not import KAIR.
4. For multi-GPU runs, ensure `gpu_ids`, visible devices, `--nproc_per_node`, and `--dist True` agree before spending training time.
5. For resume or fine-tuning, read the checkpoint behavior in `references/training-workflows.md` before assuming `path.pretrained_netG` is honored directly.
6. If the failure is an option parse, path, selector, DDP, CUDA, checkpoint, or OOM issue, use `references/troubleshooting.md`.

Training commands are intentionally provided as templates to run in the user's own KAIR checkout. Full training is expensive and is not a safe smoke test.
