# Data layout

## What is shipped in the repo

The small configuration assets under `train.configs/` are used by the losses and geometry helpers. The important bundled files are:

- `keypoints_sim.npy`
- `w_shp_sim.npy`
- `w_exp_sim.npy`
- `param_whitening.pkl`
- `u_shp.npy`
- `u_exp.npy`
- `Model_PAF.pkl`
- `pncc_code.npy`

These files feed `utils/params.py`, `wpdc_loss.py`, `vdc_loss.py`, and the inference helpers.

## Training dataset layout

The training recipes expect three things to line up by sample order:

1. A cropped-image root directory.
2. A train filelist and a validation filelist.
3. A train parameter file and a validation parameter file.

The loader behavior is positional:

- `DDFADataset` reads the filelist line by line.
- Each line is joined with `--root` using `osp.join(root, line)`.
- The target parameter at index `i` comes from the `i`th entry of the loaded param file.

That means the filelists and the param arrays must have the same length and the same sample order.

### Practical training tree

A typical layout looks like this:

```text
repo root/
  train.configs/
    keypoints_sim.npy
    w_shp_sim.npy
    w_exp_sim.npy
    param_whitening.pkl
    u_shp.npy
    u_exp.npy
    Model_PAF.pkl
    pncc_code.npy
    param_all_norm.pkl
    param_all_norm_val.pkl
    train_aug_120x120.list.train
    train_aug_120x120.list.val
  train_aug_120x120/
    <cropped images>
```

`param_all_norm.pkl`, `param_all_norm_val.pkl`, and `train_aug_120x120/` are external training artifacts; a fresh checkout may not include them until you download or generate them.

## Benchmark data layout

`benchmark.py` expects the cropped test sets to live under `test.data/`.

```text
repo root/
  test.data/
    AFLW_GT_crop/
    AFLW_GT_crop.list
    AFLW2000-3D_crop/
    AFLW2000-3D_crop.list
```

The helper metric scripts also use the checked-in arrays under `test.configs/`:

- AFLW: `AFLW_GT_crop_yaws.npy`, `AFLW_GT_crop_roi_box.npy`, `AFLW_GT_pts68.npy`, `AFLW_GT_pts21.npy`
- AFLW2000-3D: `AFLW2000-3D.pose.npy` or `AFLW2000-3D-new.pose.npy`, `AFLW2000-3D.pts68.npy`, `AFLW2000-3D-Reannotated.pts68.npy`, `AFLW2000-3D_crop.roi_box.npy`

## Shape and width expectations

- The training model outputs 62 whitened parameters.
- That matches the loader, the losses, and the benchmark reconstruction path.
- If you change the sample encoding, you must change the model head and the loss code together.

## Layout rules that matter most

- Keep filelist entries relative to `--root` when possible.
- Keep train and validation filelists aligned with their param files.
- Keep benchmark crops under `test.data/`, not alongside raw images.
- Keep the `test.configs/` arrays in place if you want to use the shipped metric helpers.
