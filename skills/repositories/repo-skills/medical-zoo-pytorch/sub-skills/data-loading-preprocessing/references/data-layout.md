# Data Layout

This route records only the on-disk facts that the data and preprocessing code expects.
It does not describe model training or loss selection.

## Common rules

- The loaders inspect folders with `glob` or plain text manifests.
- Nothing here downloads data for you.
- When a loader caches generated patches, it writes them under a dataset-local `generated/` folder and stores a pickled list file beside the source data.
- `load=True` usually means "reuse the cached list file and `.npy` patches" instead of regenerating them.

## 3D segmentation datasets

| Dataset key | Expected folder root | Files matched by the loader | Notes |
| --- | --- | --- | --- |
| `iseg2017` | `iseg_2017/iSeg-2017-Training/` and `iseg_2017/iSeg-2017-Testing/` | `*T1.img`, `*T2.img`, `*label.img` | Train and validation split from the training folder. Testing uses the testing folder. Labels are remapped from `{0,10,150,250}` to class ids `0..3`. |
| `iseg2019` | `iseg_2019/iSeg-2019-Training/` and `iseg_2019/iSeg-2019-Validation/` | `*T1.img`, `*T2.img`, `*label.img` | Train and validation split from the training folder. Validation volumes are also used to build full-volume visualization tensors. |
| `brats2018` | `MICCAI_BraTS_2018_Data_Training/` | `*GG/*/*t1.nii.gz`, `*GG/*/*t1ce.nii.gz`, `*GG/*/*t2.nii.gz`, `*GG/*/*_flair.nii.gz`, `*GG/*/*_seg.nii.gz` | Five aligned volumes per subject. The loader slices the first `split_idx` subjects for train and the remainder for val. |
| `brats2019` | `brats2019/MICCAI_BraTS_2019_Data_Training/` and `brats2019/MICCAI_BraTS_2019_Data_Validation/` | Same BraTS 2018 file set, still under `*GG/*/*...` | The loader shuffles before splitting. Validation subjects are read from the validation tree. |
| `brats2020` | `brats2020/MICCAI_BraTS_2020_Data_Training/` and `brats2020/MICCAI_BraTS_2020_Data_Validation/` | Same BraTS 2018 file set, but the 2020 loader uses `*/*...` glob patterns | The folder nesting differs from 2018/2019. Keep the 2020 tree separate from the older BraTS trees. |
| `mrbrains4` / `mrbrains9` | `mrbrains_2018/training/` | `*/pr*/*g_T1.nii.gz`, `*/pr*/*g_IR.nii.gz`, `*/pr*/*AIR.nii.gz`, `*/*egm.nii.gz` | The loader works subject-by-subject, not as a fixed train/val folder pair. The `classes` argument selects the target class collapse. |
| `ixi` | `ixi/T1/` and `ixi/T2/` | `*T1.nii.gz`, `*T2.nii.gz` | No labels. The loader is used for cross-dataset preprocessing and returns the affine separately. |
| `miccai2019` | `MICCAI_2019_pathology_challenge/Train Imgs/Train Imgs/` and `MICCAI_2019_pathology_challenge/Labels/` | `*.jpg` images, `*.png` labels | The loader builds 2D crops and writes them under a generated 2D patch folder. It also exposes helper functions for majority-vote label maps. |

## 2D COVID datasets

### COVID CT

| Item | Expected layout |
| --- | --- |
| Root | `CT_COVID/` and `CT_NonCOVID/` under the `root_dir` passed to the loader |
| Split files | One text file per class and split: `trainCT_COVID.txt`, `trainCT_NonCOVID.txt`, `valCT_COVID.txt`, `valCT_NonCOVID.txt`, `testCT_COVID.txt`, `testCT_NonCOVID.txt` |
| Text format | One image filename per line, no label column |
| Label mapping | `CT_COVID -> 0`, `CT_NonCOVID -> 1` |

### COVIDx

| Item | Expected layout |
| --- | --- |
| Root | Images are loaded from `dataset_path/<mode>/...` where `mode` is `train` or `val` |
| Split files | `train_split_v2.txt` and `test_split_v2.txt` |
| Text format | `subject_id relative/path label` separated by spaces |
| Label mapping | `pneumonia -> 0`, `normal -> 1`, `COVID-19 -> 2` |

## Generated cache folders

The loaders save cropped patches or cached sample lists beside the source data. Typical paths are:

- `iseg_2017/generated/<mode>_vol_<DxHxW>/`
- `iseg_2019/generated/<mode>_vol_<DxHxW>/`
- `MICCAI_BraTS_2018_Data_Training/generated/<mode>_vol_<DxHxW>/`
- `brats2019/MICCAI_BraTS_2019_Data_Training/generated/<mode>_vol_<DxHxW>/`
- `brats2020/generated/<mode>_vol_<DxHxW>/`
- `mrbrains_2018/generated/<mode>_vol_<DxHxW>/`
- `ixi/generated/_vol_<vx>x<vy>x<vz>/`
- `MICCAI_2019_pathology_challenge/generated/<mode>_2dgrid_<HxW>/`

Each loader also stores a pickled list file such as `*-list-<mode>-samples-*.txt` so the generated patch list can be reused later.

## Layout sanity checks

Before you call a loader, confirm:

1. The folder names match the dataset key exactly.
2. The file extensions match the loader's glob pattern.
3. The split files list relative paths, not absolute paths, when the code expects relative paths.
4. The generated cache folder is writable.
5. The dataset root contains all modalities for a subject before you enable patch generation.
