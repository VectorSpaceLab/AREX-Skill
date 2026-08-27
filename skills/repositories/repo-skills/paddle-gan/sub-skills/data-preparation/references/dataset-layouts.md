# Dataset layouts and config mapping

Use this reference to line up folders with the dataset classes used by PaddleGAN configs.
Keep the config fields on the same branch as the active split you are preparing.
When a dataset lives outside the default `data/` tree, point the config fields at
that local path explicitly instead of relying on symlinks.

## Core layout map

| Family | Dataset class / config fields | Expected on-disk shape | Notes |
| --- | --- | --- | --- |
| Unpaired image translation | `UnpairedDataset` with `dataroot_a` and `dataroot_b` | `root/trainA`, `root/trainB`, `root/testA`, `root/testB` or equivalent local folders | Files may be nested under each leaf; the loader scans recursively. Training samples A/B independently, so paired filenames are not required. |
| Paired image translation | `PairedDataset` with `dataroot` | `root/train`, `root/val`, `root/test` where each file is a left-right paired image | Each image is split into A/B halves before preprocessing. If a custom dataset has only `train` and `test`, use `test` for evaluation or create a `val` symlink/copy. |
| Single-folder image loading | `SingleDataset` with `dataroot` | Any folder that contains supported images | Each image becomes a single sample under `A_path`. Useful for simple one-domain image sets. |
| DIV2K / classical SR | `SRDataset` or SR configs using `gt_folder` and `lq_folder` | `DIV2K_train_HR`, `DIV2K_train_LR_bicubic/X2`, `X3`, `X4`, plus the processed `*_sub` outputs | The bundled DIV2K helper creates `DIV2K_train_HR_sub` and `DIV2K_train_LR_bicubic/X{2,3,4}_sub`. Patch filenames should match across all output folders. |
| REDS video SR | `VSRREDSDataset` / `VSRREDSMultipleGTDataset` with `lq_folder`, `gt_folder`, `ann_file`, `num_frames` | `REDS/train_sharp/X4`, `REDS/train_sharp_bicubic/X4`, `REDS/REDS4_test_sharp/X4`, `REDS/REDS4_test_sharp_bicubic/X4`, and `meta_info_REDS_GT.txt` | `ann_file` lines refer to clip/frame keys. The REDS dataset classes expect odd `num_frames`. |
| Vimeo90K video SR | `VSRVimeo90KDataset` with `lq_folder`, `gt_folder`, `ann_file` | `vimeo_septuplet/sequences`, `vimeo_septuplet_BD_matlabLRx4/sequences`, and the split list file | Keys are sequence folders such as `00001/0233`. Keep the LQ and GT sequence lengths aligned. |
| Wav2Lip / LRS2 | `Wav2LipDataset` with `dataroot` and `filelists_path` | `lrs2_preprocessed/<video_id>/{*.jpg,audio.wav}` plus `filelists/{train,val,test}.txt` in the working directory | The reader opens `filelists/<split>.txt` relative to the current working directory. The config field alone does not move that lookup. |
| RealSR synthetic degradation | SR configs plus RealSR preprocessing helpers | Explicit generated `HR` and `LR` folders such as `DF2K/generated/tdsr/{HR,LR}` or `DPED/generated/clean/train_tdsr/{HR,LR}` | Keep the generated paths explicit. Do not depend on repo-local `paths.yml` values in runtime guidance. |

## Config path updates

Mirror the active split when updating config fields:

| Field | Typical use | Example |
| --- | --- | --- |
| `dataset.train.dataroot_a` / `dataset.train.dataroot_b` | Unpaired translation training | `.../trainA`, `.../trainB` |
| `dataset.test.dataroot_a` / `dataset.test.dataroot_b` | Unpaired translation evaluation | `.../testA`, `.../testB` |
| `dataset.train.dataroot` | Paired translation or single-folder images | `.../train` |
| `dataset.test.dataroot` | Paired translation evaluation | `.../val` or `.../test` |
| `dataset.train.gt_folder` / `dataset.train.lq_folder` | Super-resolution or paired restoration | `.../DIV2K_train_HR_sub`, `.../DIV2K_train_LR_bicubic/X4_sub` |
| `dataset.test.gt_folder` / `dataset.test.lq_folder` | Validation or benchmark paths | `.../Set14/GTmod12`, `.../Set14/LRbicx4` |
| `dataset.train.dataset.gt_folder` / `dataset.train.dataset.lq_folder` / `dataset.train.dataset.ann_file` | Nested video-SR configs | `.../REDS/train_sharp/X4`, `.../REDS/train_sharp_bicubic/X4`, `.../REDS/meta_info_REDS_GT.txt` |
| `dataset.train.opt.dataroot_H` | SwinIR-style denoising configs | `.../trainH` |
| `dataset.train.dataroot_gt` / `dataset.train.dataroot_lq` | Degradation-based paired restoration | `.../gt`, `.../lq` |
| `dataset.train.filelists_path` | Wav2Lip configs | Keep it aligned with the working directory that holds `filelists/` |

## Practical layout notes

- Unpaired folders can be nested; the loader walks subdirectories and only cares
  about supported image files.
- Pix2Pix folders must contain horizontally concatenated pairs. The checker
  script flags odd widths because they usually mean the pair split is broken.
- REDS and Vimeo90K are sequence datasets, so keep the clip folders intact and
  do not flatten frame files into one directory.
- RealSR preprocessing generates new folders. Treat the generated tree as data
  output, not as a source of runtime configuration truth.
- A tiny nested-image fixture is enough to sanity-check the generic layout
  walker before you point the checker at a full dataset tree.
