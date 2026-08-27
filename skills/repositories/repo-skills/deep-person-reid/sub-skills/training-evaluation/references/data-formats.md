# Data formats and dataset layout

Torchreid data managers expect a dataset root directory plus registered dataset keys. Built-in datasets may try to download or organize data when missing, but future agents should not rely on network access; check local files first.

## Built-in dataset keys

### Image ReID keys

`market1501`, `cuhk03`, `dukemtmcreid`, `msmt17`, `viper`, `grid`, `cuhk01`, `ilids`, `sensereid`, `prid`, `cuhk02`, `university1652`, `cuhksysu`

Common high-use keys:

| Key | Dataset | Typical use |
| --- | --- | --- |
| `market1501` | Market1501 | Same-domain and baseline image ReID. Fixed split; usually `split_id=0`. |
| `dukemtmcreid` | DukeMTMC-reID | Same-domain or source/target transfer with Market1501. Fixed split. |
| `msmt17` | MSMT17 | Larger image ReID benchmark. Fixed split. |
| `cuhk03` | CUHK03 | New 767/700 split by default; optional classic 20 splits and labeled/detected modes. |
| `viper`, `grid`, `cuhk01`, `ilids`, `prid` | Smaller classic image datasets | Split-sensitive evaluation; often average multiple splits. |
| `sensereid` | SenseReID | Evaluation-only; no training images. |

### Video ReID keys

`mars`, `ilidsvid`, `prid2011`, `dukemtmcvidreid`

| Key | Dataset | Split notes |
| --- | --- | --- |
| `mars` | MARS | Fixed single split; usually `split_id=0`. |
| `dukemtmcvidreid` | DukeMTMC-VideoReID | Fixed single split. |
| `ilidsvid` | iLIDS-VID | 10 predefined splits; vary `split_id` 0-9 for full protocol. |
| `prid2011` | PRID2011 video | 10 predefined splits; vary `split_id` 0-9 for full protocol. |

## Expected root layouts

Set `data.root`/`root` to the parent directory containing these folders, not to the dataset subfolder itself.

```text
reid-data/
  market1501/
    Market-1501-v15.09.15/
      query/
      bounding_box_train/
      bounding_box_test/
```

Optional Market1501 500K distractors live under `market1501/Market-1501-v15.09.15` after extracting the distractor archive, then set `market1501.use_500k_distractors True`.

```text
reid-data/
  dukemtmc-reid/
    DukeMTMC-reID/
      query/
      bounding_box_train/
      bounding_box_test/
```

```text
reid-data/
  msmt17/
    MSMT17_V1/        # or MSMT17_V2
      train/
      test/
      list_train.txt
      list_query.txt
      list_gallery.txt
      list_val.txt
```

```text
reid-data/
  cuhk03/
    cuhk03_release/
    cuhk03_new_protocol_config_detected.mat
    cuhk03_new_protocol_config_labeled.mat
```

CUHK03 notes:

- Default mode uses the new 767/700 split and detected images.
- Set `cuhk03.labeled_images True` for labeled images.
- Set `cuhk03.classic_split True` for original 20 classic splits.
- Pair classic-split reporting with `cuhk03.use_metric_cuhk03 True` only when the old single-gallery-shot metric is needed; do not report mAP for old classic protocol comparisons that omit it.
- Generated CUHK03 JSON split/cache files can contain old absolute parent paths. If a dataset tree is moved and loading fails, delete those generated split/cache JSON files so Torchreid can regenerate them.

```text
reid-data/
  mars/
    bbox_train/
    bbox_test/
    info/
```

```text
reid-data/
  ilids-vid/
    i-LIDS-VID/
    train-test people splits/
```

```text
reid-data/
  prid2011/
    splits_prid2011.json
    prid_2011/
      single_shot/
      multi_shot/
```

```text
reid-data/
  dukemtmc-vidreid/
    DukeMTMC-VideoReID/
      train/
      query/
      gallery/
```

## Image dataset object contract

All image dataset classes should subclass `torchreid.data.ImageDataset` and build three lists:

```python
train = [(img_path, pid, camid), ...]
query = [(img_path, pid, camid), ...]
gallery = [(img_path, pid, camid), ...]
super(NewDataset, self).__init__(train, query, gallery, **kwargs)
```

Rules:

- `img_path` is an existing image path string.
- `pid` and `camid` are integers and should be **zero-based**.
- Query and gallery share the same person-ID scope: `pid=0` in query means the same person as `pid=0` in gallery.
- Train/query/gallery share the same camera-ID scope: `camid=0` means the same camera across subsets.
- The base `Dataset` extends each tuple to `(img_path, pid, camid, dsetid)` internally.
- `ImageDataset.__getitem__` returns a dict with keys `img`, `pid`, `camid`, `impath`, and `dsetid`; image batches have shape `(batch_size, channels, height, width)`.

Minimal custom image dataset registration:

```python
import os
import os.path as osp
import torchreid
from torchreid.data import ImageDataset

class NewDataset(ImageDataset):
    dataset_dir = "new_dataset"

    def __init__(self, root="", **kwargs):
        root = osp.abspath(osp.expanduser(root))
        dataset_dir = osp.join(root, self.dataset_dir)

        # Replace with real parsing and explicit file existence checks.
        train = [
            (osp.join(dataset_dir, "train", "person0_cam0.jpg"), 0, 0),
            (osp.join(dataset_dir, "train", "person0_cam1.jpg"), 0, 1),
        ]
        query = [(osp.join(dataset_dir, "query", "person0_cam0.jpg"), 0, 0)]
        gallery = [(osp.join(dataset_dir, "gallery", "person0_cam1.jpg"), 0, 1)]

        for path, _pid, _camid in train + query + gallery:
            if not osp.isfile(path):
                raise FileNotFoundError(path)

        super(NewDataset, self).__init__(train, query, gallery, **kwargs)

torchreid.data.register_image_dataset("new_dataset", NewDataset)

datamanager = torchreid.data.ImageDataManager(
    root="/path/to/reid-data",
    sources=["new_dataset", "dukemtmcreid"],
    targets="market1501",
    height=256,
    width=128,
)
```

Registration constraints:

- `register_image_dataset(name, dataset_class)` raises if `name` already exists.
- Register in the same Python process before constructing the data manager.
- For a custom dataset combined with built-ins, Torchreid offsets train pids/camids/dataset IDs when summing datasets. Keep each dataset internally zero-based.

## Video dataset object contract

Video dataset classes subclass `torchreid.data.VideoDataset` and use tracklet tuples:

```python
train = [([img_path_0, img_path_1, ...], pid, camid), ...]
query = [([img_path_0, img_path_1, ...], pid, camid), ...]
gallery = [([img_path_0, img_path_1, ...], pid, camid), ...]
super(NewVideoDataset, self).__init__(train, query, gallery, seq_len=15, sample_method="evenly", **kwargs)
```

`VideoDataset.__getitem__` returns `{'img': imgs, 'pid': pid, 'camid': camid, 'dsetid': dsetid}` where `imgs` has shape `(seq_len, channels, height, width)`. Video batches have shape `(batch_size, seq_len, channels, height, width)`.

Sampling methods:

- `evenly`: sample `seq_len` frames at roughly even intervals; pads by repeating the last frame when a tracklet is short.
- `random`: sample `seq_len` frames randomly and sort selected indices to keep temporal order.
- `all`: use all frames; set batch size to 1.

## Data manager construction notes

`ImageDataManager` and `VideoDataManager` both build:

- `train_loader` for source training data.
- `test_loader[target]['query']` and `test_loader[target]['gallery']` for each target.
- `test_dataset[target]['query']` and `test_dataset[target]['gallery']` as raw tuples for ranked-result visualization.
- `num_train_pids` and `num_train_cams` properties.

Image-only `load_train_targets=True` builds `train_loader_t` for target train data, but sources and targets must not overlap.

`combineall=True` adds query and gallery identities into the training set for datasets that support it. The base dataset ignores junk pids and relabels gallery/query pids after the original train pids. Do not use it when you need a strict train/test separation.

## Transforms and normalization

Training transforms are composed in this order:

1. Resize to `height x width`.
2. Optional `random_flip`.
3. Optional `random_crop` using enlarged random 2D translation.
4. Optional `random_patch`.
5. Optional `color_jitter`.
6. Convert to tensor in `[0, 1]`.
7. Normalize with `norm_mean`/`norm_std`.
8. Optional `random_erase`.

Test transforms are resize + tensor + normalization only.

Default normalization is ImageNet mean/std `[0.485, 0.456, 0.406]` / `[0.229, 0.224, 0.225]`. Use the bundled mean/std helper for dataset-specific normalization only after confirming local training data.

## Evaluation split reminders

- Market1501, DukeMTMC-reID, CUHK03 new split, MSMT17, MARS, and DukeMTMC-VideoReID use fixed split `split_id=0`.
- CUHK03 classic split has 20 splits: `split_id=0` to `19`.
- VIPeR and CUHK01 generate paired camera splits; full evaluation varies across split IDs and often averages results.
- GRID, image iLIDS, and PRID image use 10 random splits.
- iLIDS-VID and PRID2011 video use 10 predefined splits.
- SenseReID is evaluation-only; do not train from it as a source dataset.
