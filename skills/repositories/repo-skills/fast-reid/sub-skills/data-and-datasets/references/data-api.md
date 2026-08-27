# FastReID data API

This reference covers the operating API for FastReID v1.3 dataset registration, base classes, dataloader builders, transforms, and samplers.

## Registry mechanics

FastReID stores datasets in `fastreid.data.datasets.DATASET_REGISTRY`. The key is the registered class name, not a lowercase alias.

```python
from fastreid.data.datasets import DATASET_REGISTRY

DatasetClass = DATASET_REGISTRY.get("Market1501")
dataset = DatasetClass(root="<datasets-root>")
print(len(dataset.train), len(dataset.query), len(dataset.gallery))
```

Importing `fastreid.data` imports the built-in dataset package, which registers the built-ins. For custom datasets, import the module that defines and registers the dataset class before `DATASET_REGISTRY.get(...)`, `build_reid_train_loader(...)`, or `DefaultTrainer.build_train_loader(...)` runs.

## Base classes and item schema

`ImageDataset` represents three logical splits: `train`, `query`, and `gallery`.

```python
from fastreid.data.datasets.bases import ImageDataset

train = [("images/train/0001_c1.jpg", "custom_1", "custom_0")]
query = [("images/query/0001_c1.jpg", 1, 0)]
gallery = [("images/gallery/0001_c2.jpg", 1, 1)]
dataset = ImageDataset(train, query, gallery)
```

Important behavior:

- `ImageDataset` does not read pixels by itself; it stores tuple lists and reports statistics.
- `Dataset.check_before_run(required_files)` raises a runtime error when required files or folders are missing.
- `Dataset.combine_all()` appends query/gallery items into train while skipping junk pids and namespacing appended test ids.
- `parse_data`, `get_num_pids`, and `get_num_cams` count tuple positions `pid` and `camid`.

`CommDataset` is the PyTorch dataset wrapper used by the loader builders:

```python
from fastreid.data.common import CommDataset

comm_dataset = CommDataset(train_items, transform=None, relabel=True)
item = comm_dataset[0]
# item has keys: images, targets, camids, img_paths
```

With `relabel=True`, `pid` and `camid` values are mapped to contiguous integer ids. With `relabel=False`, original ids are preserved for query/gallery evaluation.

## Dataloader builders

Verified signatures:

```python
build_reid_train_loader(train_set, *, sampler=None, total_batch_size, num_workers=0)
build_reid_test_loader(test_set, test_batch_size, num_query, num_workers=4)
```

FastReID decorates these with its `configurable` helper, so normal config-driven calls are also valid:

```python
from fastreid.config import get_cfg
from fastreid.data import build_reid_train_loader, build_reid_test_loader

cfg = get_cfg()
cfg.DATASETS.NAMES = ("Market1501",)
cfg.DATASETS.TESTS = ("Market1501",)

train_loader = build_reid_train_loader(cfg, combineall=cfg.DATASETS.COMBINEALL)
test_loader, num_query = build_reid_test_loader(cfg, dataset_name="Market1501")
```

Config-driven train builder behavior:

1. Builds train transforms with `build_transforms(cfg, is_train=True)`.
2. For each name in `cfg.DATASETS.NAMES`, instantiates `DATASET_REGISTRY.get(name)(root=<FASTREID_DATASETS>, **kwargs)`.
3. Extends one `train_items` list with every dataset's `data.train`.
4. Wraps with `CommDataset(train_items, transforms, relabel=True)`.
5. Selects a sampler from `cfg.DATALOADER.SAMPLER_TRAIN`.
6. Returns a dataloader with global batch size `cfg.SOLVER.IMS_PER_BATCH` and workers `cfg.DATALOADER.NUM_WORKERS`.

Config-driven test builder behavior:

1. Builds test transforms with `build_transforms(cfg, is_train=False)`.
2. Instantiates `DATASET_REGISTRY.get(dataset_name)(root=<FASTREID_DATASETS>, **kwargs)`.
3. Concatenates `data.query + data.gallery`.
4. Wraps with `CommDataset(test_items, transforms, relabel=False)`.
5. Sets `num_query = len(data.query)`.
6. Returns `(test_loader, num_query)` using `cfg.TEST.IMS_PER_BATCH`.

### CUDA prefetch caveat

The built dataloaders use FastReID's `DataLoaderX`, which creates CUDA streams and moves tensor batches to `local_rank`. Treat full loader iteration as a training/evaluation runtime operation that expects a compatible torch/CUDA setup. For CPU-only layout checks, use the bundled validator or instantiate `ImageDataset`/`CommDataset` without iterating a FastReID dataloader.

## Transform decisions

`build_transforms(cfg, is_train=True)` composes transforms from `cfg.INPUT`.

Training order:

1. Optional `AUTOAUG` random apply.
2. Resize to `INPUT.SIZE_TRAIN` when positive.
3. Optional random resized crop from `INPUT.CROP`.
4. Optional padding then random crop from `INPUT.PADDING`.
5. Optional random horizontal flip from `INPUT.FLIP`.
6. Optional color jitter from `INPUT.CJ`.
7. Optional random affine from `INPUT.AFFINE`.
8. Optional AugMix from `INPUT.AUGMIX`.
9. Convert image to tensor.
10. Optional random erasing from `INPUT.REA`.
11. Optional random patch from `INPUT.RPT`.

Test order:

1. Resize to `INPUT.SIZE_TEST` when positive.
2. Optional center crop from `INPUT.CROP`.
3. Convert image to tensor.

Defaults include `SIZE_TRAIN=[256, 128]`, `SIZE_TEST=[256, 128]`, and most stochastic augmentations disabled until a recipe enables them.

## Sampler decisions

`cfg.DATALOADER.SAMPLER_TRAIN` supports these core values:

- `TrainingSampler`: infinite shuffled stream over all training indices; safest baseline and default.
- `NaiveIdentitySampler`: samples `N` identities and `K=NUM_INSTANCE` images per identity; batch size must support integer `N = mini_batch_size // NUM_INSTANCE`.
- `BalancedIdentitySampler`: identity sampler that also tries to vary camera ids within identity batches.
- `SetReWeightSampler`: samples according to per-camera/set weights from `DATALOADER.SET_WEIGHT`; batch size must be divisible by `sum(SET_WEIGHT) * NUM_INSTANCE` and larger than that product.
- `ImbalancedDatasetSampler`: weights samples inversely by identity frequency.

Batch terminology:

- `SOLVER.IMS_PER_BATCH` is the global train batch size across all workers.
- `mini_batch_size = SOLVER.IMS_PER_BATCH // world_size`.
- Identity samplers depend on `mini_batch_size // DATALOADER.NUM_INSTANCE` being at least 1.
- Inference uses `InferenceSampler`, which shards the exact query+gallery set across workers.

## Custom dataset registration pattern

Use a custom dataset when a layout differs from the built-ins. Register the class and import it before building loaders.

```python
import glob
import os
import re
from fastreid.data.datasets import DATASET_REGISTRY
from fastreid.data.datasets.bases import ImageDataset

@DATASET_REGISTRY.register()
class MyReIDDataset(ImageDataset):
    dataset_name = "myreid"

    def __init__(self, root="datasets", **kwargs):
        base = os.path.join(root, "myreid")
        train_dir = os.path.join(base, "train")
        query_dir = os.path.join(base, "query")
        gallery_dir = os.path.join(base, "gallery")
        self.check_before_run([train_dir, query_dir, gallery_dir])
        train = self._process_dir(train_dir, is_train=True)
        query = self._process_dir(query_dir, is_train=False)
        gallery = self._process_dir(gallery_dir, is_train=False)
        super().__init__(train, query, gallery, **kwargs)

    def _process_dir(self, directory, is_train=True):
        pattern = re.compile(r"([0-9]+)_c([0-9]+)")
        rows = []
        for path in glob.glob(os.path.join(directory, "*.jpg")):
            match = pattern.search(os.path.basename(path))
            if not match:
                continue
            pid = int(match.group(1))
            camid = int(match.group(2)) - 1
            if is_train:
                pid = f"{self.dataset_name}_{pid}"
                camid = f"{self.dataset_name}_{camid}"
            rows.append((path, pid, camid))
        if not rows:
            raise RuntimeError(f"No parseable images found in {directory}")
        return rows
```

Then make the registration visible before the config-driven builder runs:

```python
# Import the module containing MyReIDDataset before loader construction.
import my_project.my_reid_dataset  # noqa: F401

from fastreid.config import get_cfg
from fastreid.data import build_reid_train_loader

cfg = get_cfg()
cfg.DATASETS.NAMES = ("MyReIDDataset",)
train_loader = build_reid_train_loader(cfg, combineall=cfg.DATASETS.COMBINEALL)
```

If the dataset is only for a project extension, route the project packaging/import path details to the deployment-and-projects sub-skill, then return here for the shared `DATASET_REGISTRY` pattern.

## Safe preflight checklist

Before train/eval:

- Confirm `FASTREID_DATASETS` resolves to the intended parent directory.
- Confirm `cfg.DATASETS.NAMES` and `cfg.DATASETS.TESTS` use registered class names.
- Run `validate_dataset_layout.py` for supported built-ins.
- For custom datasets, instantiate the class and check `len(train)`, `len(query)`, `len(gallery)` before building a full loader.
- Confirm query and gallery are both non-empty for evaluation.
- Confirm identity-sampler batch constraints before using `NaiveIdentitySampler`, `BalancedIdentitySampler`, or `SetReWeightSampler`.
