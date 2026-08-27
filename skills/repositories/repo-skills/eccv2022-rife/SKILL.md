---
name: eccv2022-rife
description: "Operate ECCV2022-RIFE video frame interpolation, benchmark
  evaluation, and training workflows from a source checkout."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ECCV2022-RIFE repo skill

Use this skill when the task names ECCV2022-RIFE, RIFE, Real-Time Intermediate Flow Estimation, video frame interpolation, slow-motion generation, image-pair interpolation, RIFE benchmarks, or RIFE training/reproduction from this source checkout.

The repository is a source-script project rather than an installable Python distribution. Future agents should reason from the checkout scripts and bundled skill references, not from a package console entry point.

## First checks

1. Check the source state against [references/repo-provenance.md](references/repo-provenance.md) when exact behavior matters or the checkout looks newer than the skill.
2. Confirm dependencies. Base inference needs PyTorch, TorchVision, NumPy, OpenCV, scikit-video, MoviePy, tqdm, and an `ffmpeg` executable for video/audio work. Training also needs TensorBoard; HD benchmarks need scikit-image.
3. Confirm external assets. Pretrained checkpoints and benchmark/training datasets are not bundled with the source checkout or this skill.
4. Run a safe import/backend smoke before long work when the environment is uncertain:

   ```bash
   python scripts/smoke_model_api.py --repo-root <checkout> --device auto --size 32
   ```

   This smoke uses random weights. It proves source imports, torch backend, and `Model.inference` shape behavior only; it does not prove interpolation quality or official benchmark metrics.

## Route map

| User intent | Read |
| --- | --- |
| Interpolate two images, use `--ratio`, make 2X/4X/16X frames, process a video or numbered PNG directory, tune `--scale`/`--fps`/`--fp16`, understand output paths or audio transfer | [sub-skills/interpolation/SKILL.md](sub-skills/interpolation/SKILL.md) |
| Select or validate UCF101, Vimeo90K, MiddleBury, ATD12K, HD, HD 4X, or `testtime.py` evaluations; classify safe native verification cases; interpret PSNR/SSIM/IE | [sub-skills/evaluation/SKILL.md](sub-skills/evaluation/SKILL.md) |
| Prepare Vimeo triplet data, plan `train.py` distributed CUDA/NCCL launch, check TensorBoard/checkpoints, reason about world size, batch size, OOM, or long-running training | [sub-skills/training/SKILL.md](sub-skills/training/SKILL.md) |
| Inspect `model.RIFE.Model`, checkpoint loading, tensor shapes, device selection, or `VimeoDataset` signatures | [references/model-api.md](references/model-api.md) |
| Diagnose install/import, checkpoint, CUDA/CPU, dataset, ffmpeg/audio, or output side-effect issues shared across workflows | [references/troubleshooting.md](references/troubleshooting.md) |

## Operating boundaries

- Do not download checkpoints or datasets, run full benchmarks, launch training, or start long video inference without explicit user approval and a time/storage/GPU budget.
- Do not treat CPU importability as proof of CUDA-only training or HD benchmark behavior. `train.py`, `benchmark/HD.py`, and `benchmark/HD_multi_4X.py` require CUDA paths.
- Do not claim README-reported paper or official metrics are reproduced unless the matching external data, checkpoints, backend, and commands were actually run in the current session.
- Do not promise verified HD model variants from the default checkout. The inference scripts try HD import paths before falling back to `model.RIFE`, but the active `model.RIFE_HD*` paths are absent in this source snapshot.
- Prefer bundled validators/builders before mutating work:
  - [sub-skills/interpolation/scripts/interpolation_command_builder.py](sub-skills/interpolation/scripts/interpolation_command_builder.py)
  - [sub-skills/evaluation/scripts/check_benchmark_layout.py](sub-skills/evaluation/scripts/check_benchmark_layout.py)
  - [sub-skills/training/scripts/check_vimeo_triplet_layout.py](sub-skills/training/scripts/check_vimeo_triplet_layout.py)

## Common source commands

These command shapes are documented in the sub-skill references; validate assets first.

```bash
python inference_img.py --img img0.png img1.png --exp 4 --model train_log
python inference_img.py --img img0.png img1.png --ratio 0.25 --model train_log
python inference_video.py --video input.mp4 --exp 1 --scale 0.5 --model train_log
python inference_video.py --img frames --exp 2 --png --model train_log
python benchmark/testtime.py
python -m torch.distributed.launch --nproc_per_node=4 train.py --world_size=4
```

## Self-contained skill assets

- [references/repo-provenance.md](references/repo-provenance.md) records the source commit, dirty-state caveat, evidence paths, and refresh triggers.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) provides structured router metadata for managed repo-skill import tooling.
- [references/model-api.md](references/model-api.md) records verified signatures and tensor/device contracts.
- [references/troubleshooting.md](references/troubleshooting.md) covers cross-cutting operational failures.
- [scripts/smoke_model_api.py](scripts/smoke_model_api.py) is the shared safe API/backend smoke helper.
