# Repo provenance

## Source snapshot

- Repository: ECCV2022-RIFE — Real-Time Intermediate Flow Estimation for Video Frame Interpolation.
- Public remote: `https://github.com/hzwer/ECCV2022-RIFE.git`.
- Commit: `5d8adbdd40e12c2c8f91930eff838aebe561c086`.
- Branch: `main`.
- Exact tag: none found at this commit.
- Working tree state during skill creation: dirty because the untracked `skills/` production area existed.
- Package/distribution version: not available. This checkout has no Python packaging metadata and is operated as a source-script repository.

## Evidence paths used

Runtime and API evidence:

- `README.md`
- `requirements.txt`
- `model/RIFE.py`
- `model/IFNet.py`
- `model/IFNet_m.py`
- `model/loss.py`
- `model/laplacian.py`
- `model/refine.py`
- `model/warplayer.py`
- `model/pytorch_msssim/__init__.py`
- `model/oldmodel/IFNet_HD.py`
- `model/oldmodel/IFNet_HDv2.py`
- `model/oldmodel/RIFE_HD.py`
- `model/oldmodel/RIFE_HDv2.py`

Workflow evidence:

- `inference_img.py`
- `inference_video.py`
- `train.py`
- `dataset.py`
- `benchmark/testtime.py`
- `benchmark/UCF101.py`
- `benchmark/Vimeo90K.py`
- `benchmark/MiddleBury_Other.py`
- `benchmark/ATD12K.py`
- `benchmark/HD.py`
- `benchmark/HD_multi_4X.py`
- `benchmark/yuv_frame_io.py`
- `docker/Dockerfile`
- `docker/inference_img`
- `docker/inference_video`
- `Colab_demo.ipynb` as tutorial evidence only

## Evidence intentionally not embedded as runtime dependencies

- Static demo media under `demo/`.
- External checkpoints expected under directories such as `train_log/` or `RIFE_m_train_log/`; these are not present in the checkout and must be supplied by users.
- External datasets expected under `vimeo_triplet/`, `vimeo_interp_test/`, `UCF101/`, `other-data/`, `other-gt-interp/`, `HD_dataset/`, and `datasets/test_2k_540p/`; these are not present in the checkout.
- Existing/generated `skills/` production logs and review artifacts.

## Verified runtime facts at creation time

- The repository is not pip-installable as a distribution from this checkout.
- A private Python 3.11 inspection environment successfully imported `model.RIFE`, `dataset`, and `train` after installing runtime dependencies.
- Verified signatures:
  - `Model(local_rank=-1, arbitrary=False)`
  - `Model.inference(self, img0, img1, scale=1, scale_list=None, TTA=False, timestep=0.5)`
  - `Model.update(self, imgs, gt, learning_rate=0, mul=1, training=True, flow_gt=None)`
  - `VimeoDataset(dataset_name, batch_size=32)`
- CPU and CUDA random-tensor `Model.inference` smokes passed without loading checkpoints. These smokes validate imports/backend/API only, not official interpolation quality.
- `inference_img.py --help` and `inference_video.py --help` passed without checkpoints.
- Training requires TensorBoard even though it is not listed in `requirements.txt`.
- HD benchmark scripts require `scikit-image` even though it is not listed in `requirements.txt`.

## Refresh guidance

Refresh this repo skill if a later checkout changes any of these surfaces:

- inference CLI flags, output directories, model import fallback order, or checkpoint loading;
- `model.RIFE.Model` signatures or device-selection behavior;
- benchmark script paths, dataset layouts, metrics, or CUDA-only assumptions;
- `train.py`, `dataset.py`, TensorBoard/checkpoint paths, or distributed launch behavior;
- packaging metadata appears or the project gains installable console entry points;
- requirements or documented model/dataset download locations change.
