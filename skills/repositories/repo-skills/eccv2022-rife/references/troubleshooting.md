# ECCV2022-RIFE cross-cutting troubleshooting

Use this reference for issues that affect more than one workflow. For workflow-specific failures, follow the nearest sub-skill troubleshooting file.

## Source-only repository, not an installed package

Symptoms:

- `ModuleNotFoundError: No module named 'model'`
- `python -m pip install -e .` fails because no packaging metadata exists
- Imported modules differ depending on the current working directory

Likely cause and recovery:

- ECCV2022-RIFE is a source-script repository with no `pyproject.toml`, `setup.py`, or `setup.cfg` in this checkout.
- Run source scripts from the checkout root, or add the checkout root to `PYTHONPATH` before importing `model.RIFE`.
- For safe import/backend checks, use `scripts/smoke_model_api.py --repo-root <checkout>`.

## Dependency gaps beyond `requirements.txt`

The base requirements cover inference dependencies: `numpy`, `tqdm`, `sk-video`, `torch`, `opencv-python`, `moviepy`, and `torchvision`. Several selected workflows need additional public tools or packages:

| Surface | Extra dependency | Evidence / symptom |
| --- | --- | --- |
| Video/audio workflows | `ffmpeg` executable | `inference_video.py` invokes `ffmpeg` for audio extraction/muxing; Dockerfile installs it. |
| Training | `tensorboard` | `train.py` imports `torch.utils.tensorboard.SummaryWriter`; PyTorch raises `ModuleNotFoundError: No module named 'tensorboard'` if absent. |
| HD benchmarks | `scikit-image` | `benchmark/HD.py` and `benchmark/HD_multi_4X.py` import `skimage.color.rgb2yuv`. |
| Dataset benchmarks | external images/YUV files and checkpoints | Benchmark scripts use hard-coded dataset roots and checkpoint directories. |

Do not install broad development extras just to solve one missing import. Install the narrow dependency that the selected workflow requires.

## Checkpoint and model-family failures

Symptoms:

- `FileNotFoundError` for `train_log/flownet.pkl`
- `RuntimeError` from `load_state_dict`
- The CLI prints `Loaded ArXiv-RIFE model` when the user expected an HD model
- `ModuleNotFoundError` for `model.RIFE_HDv2` or `model.RIFE_HD`

Likely cause and recovery:

- Pretrained weights are external and are not bundled in this checkout.
- The default inference/evaluation checkpoint directory is `train_log`; pass `--model <checkpoint-dir>` for inference when using a different directory.
- The fallback `model.RIFE.Model.load_model` expects a `flownet.pkl` state dict. The source converter is oriented to DDP checkpoints with `module.` prefixes.
- The current inference scripts attempt `model.RIFE_HDv2`, `train_log.RIFE_HDv3`, and `model.RIFE_HD` before falling back to `model.RIFE`, but those active HD import paths are absent in this checkout. Treat HD support as unverified unless the user supplies compatible model Python files and checkpoints and a smoke run passes.
- For RIFE_m HD 4X evaluation, the source expects `RIFE_m_train_log/flownet.pkl` and `Model(arbitrary=True)`.

## CPU, CUDA, and backend gates

Inference:

- `inference_img.py`, `inference_video.py`, `benchmark/testtime.py`, and most PSNR/SSIM benchmark scripts choose `cuda` when available and otherwise run on CPU.
- CPU is functionally valid for small checks but can be very slow for real videos or full datasets.
- `--fp16` should be used only on suitable CUDA devices; it is not a CPU optimization.

Training and HD benchmarks:

- `train.py` is CUDA-only in this checkout: it uses `torch.device("cuda")`, NCCL process-group initialization, and per-rank CUDA device selection.
- `benchmark/HD.py` and `benchmark/HD_multi_4X.py` contain explicit `.cuda()` calls and have no CPU substitute.
- A CPU import does not verify these CUDA-required workflows. If CUDA is unavailable, narrow the task, mark the workflow blocked, or ask the user for compatible hardware.

## External datasets and long-running jobs

Symptoms:

- `FileNotFoundError` for `vimeo_triplet`, `vimeo_interp_test`, `UCF101`, `other-data`, `HD_dataset`, or `datasets/test_2k_540p`
- `cv2.imread` returns `None`, followed by `.transpose` or shape errors
- YUV benchmark stops early or reports unexpected averages

Likely cause and recovery:

- Evaluation and training datasets are not part of the source checkout.
- Use sub-skill validators before running expensive commands:
  - `sub-skills/evaluation/scripts/check_benchmark_layout.py`
  - `sub-skills/training/scripts/check_vimeo_triplet_layout.py`
- Do not download datasets or launch full benchmarks/training without explicit user approval, time budget, and storage/GPU availability.

## Output directories and side effects

- Image inference writes `output/img*.png` or `output/img*.exr` relative to the current working directory.
- Video PNG mode writes `vid_out/*.png` relative to the current working directory.
- Video output without `--output` derives a new video filename from the input name, factor, FPS, and extension.
- Training overwrites `train_log/flownet.pkl` after epochs and writes TensorBoard event files under `train/` and `validate/`.
- Benchmark scripts stream metrics to stdout and may read many files; they generally do not write results, but they can consume substantial GPU/CPU time.

Always warn before running commands that create or overwrite these paths.

## Refresh/staleness checks

Read `references/repo-provenance.md` before applying this skill to a different checkout. If the current checkout has changed substantially in model files, inference scripts, benchmark paths, requirements, or training code, refresh the repo skill before relying on exact commands or backend classifications.
