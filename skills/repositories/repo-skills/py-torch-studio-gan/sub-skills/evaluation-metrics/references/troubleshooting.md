# Evaluation metric troubleshooting

## Input and cache assertions

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `dset1 should be specified!` | Neither `--dset1_feats` nor `--dset1_moments` was supplied, and `--dset1` is missing. | Pass a real/reference ImageFolder as `--dset1`, or supply both cache files if you intentionally avoid loading the real folder. |
| `Either dset1 or dset1_moments should be given to compute FID.` | `fid` was requested, but there is no real folder and no moment cache. | Add `--dset1 /path/to/real_imagefolder` or `--dset1_moments /path/to/reference_moments.npz`. |
| `Either dset1 or dset1_feats should be given to compute PRDC.` | `prdc` was requested, but there is no real folder and no feature cache. | Add `--dset1 /path/to/real_imagefolder` or `--dset1_feats /path/to/reference_feats.npz`. |
| User has `--dset1_feats` but requests `fid prdc` without `--dset1_moments` | Features satisfy PRDC only; FID needs moments. | Add `--dset1_moments`, pass `--dset1`, or drop `fid`. |
| User has `--dset1_moments` but requests `fid prdc` without `--dset1_feats` | Moments satisfy FID only; PRDC needs features. | Add `--dset1_feats`, pass `--dset1`, or drop `prdc`. |
| ImageFolder error about classes or no images | `--dset1` or `--dset2` does not contain class subdirectories with images. | Restructure as `root/class_name/image.png`. For generated samples with no labels, use one class directory such as `generated/`. |
| Cache key error such as missing `mu`, `sigma`, or `real_feats` | Wrong file type, stale cache, or plain `.npy` array used where StudioGAN expects `.npz` keys. | Use StudioGAN-created `.npz` caches or rebuild caches with matching backbone/resizer/dataset protocol. |

## CUDA and device failures

StudioGAN's current standalone evaluator is GPU-oriented. It queries CUDA state before evaluation and passes integer device IDs into model/tensor placement. Common failures:

- `torch.cuda.current_device` error or no CUDA device: use a CUDA-capable PyTorch environment and set `CUDA_VISIBLE_DEVICES`, or do not run metrics in this checkout.
- Out-of-memory during feature extraction: reduce `--batch_size`, use fewer visible GPUs, lower DataLoader workers, or evaluate in metric subsets.
- DDP issues: ensure `CUDA_VISIBLE_DEVICES` lists all intended GPUs, set `MASTER_ADDR` and `MASTER_PORT`, use a batch size divisible by world size, and prefer `--backend nccl` for CUDA.
- DDP with only one visible GPU adds complexity without benefit; use single-process evaluation unless multi-GPU throughput is needed.

## Pretrained weights, network, and cache failures

Backbone initialization can fail before metrics start.

| Backbone family | Failure surface | Fix |
| --- | --- | --- |
| `InceptionV3_tf` | PyTorch FID Inception weight URL/cache unavailable. | Pre-populate the PyTorch model cache, allow the download, or choose an already-cached backbone. |
| `InceptionV3_torch`, `ResNet50_torch`, `SwAV_torch` | `torch.hub.load` cannot reach hub source, branch/tag, or cached repo; SwAV also needs a linear classifier checkpoint. | Pre-cache hub repositories/weights or run in a network-enabled environment. |
| `DINO_torch` | Teacher or linear DINO weight download unavailable. | Pre-cache DINO weights or choose a cached/default backbone. |
| `Swin-T_torch` | Swin checkpoint URL/cache unavailable. | Pre-cache the checkpoint or use another backbone. |

When a user requests architecture-friendly metrics with SwAV, DINO, or Swin and hits a download/cache failure, explain that the metric protocol intentionally changes the feature extractor and therefore cannot reuse Inception-only caches.

## Resizer and protocol mismatches

- `legacy`, `clean`, and `friendly` are different metric protocols. A lower FID under one protocol is not directly comparable to another.
- `friendly` changes the PIL filter by backbone. Always report both `--post_resizer friendly` and the exact `--eval_backbone`.
- Do not reuse `--dset1_moments` or `--dset1_feats` generated with a different post-resizer, backbone, real split, or preprocessing path.
- Training `--pre_resizer` and metric `--post_resizer` are separate. If the generated images were saved after one preprocessing convention and evaluated with another, document the mismatch.

## Small data and smoke-test traps

- FID covariance estimates can be singular, unstable, or meaningless for tiny datasets. A tiny fixture can validate the command path but not metric quality.
- PRDC pairwise distance computation can be expensive in memory for large feature sets; reduce scope or batch the surrounding feature extraction, but the final PRDC computation still scales with feature count.
- IS without enough diverse generated images is not interpretable.

## Legacy TensorFlow 1.x script

The repository contains a TensorFlow 1.3-era inception-score script as a legacy reference. It is separate from the current PyTorch metric path, was not part of the verified runtime environment, may require obsolete dependencies, and should not be used unless the user explicitly asks for legacy reproduction and accepts a separate environment.
