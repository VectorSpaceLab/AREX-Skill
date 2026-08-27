# FastReID data troubleshooting

Use this guide for dataset-root, layout, tuple parsing, query/gallery, sampler, and stale-test problems.

## FastReID cannot find the dataset

Typical error:

```text
RuntimeError: "..." is not found
```

Checklist:

1. Confirm the process environment has the intended root:
   ```bash
   echo "$FASTREID_DATASETS"
   ```
2. If the variable is empty, FastReID uses `datasets` relative to the current working directory. This is easy to get wrong when launching commands from another directory.
3. Set the root to the parent directory that contains built-in dataset folders:
   ```bash
   export FASTREID_DATASETS=<datasets-root>
   ```
4. Run the bundled validator, for example:
   ```bash
   python sub-skills/data-and-datasets/scripts/validate_dataset_layout.py --root <datasets-root> --dataset Market1501
   ```
5. Ensure `cfg.DATASETS.NAMES` and `cfg.DATASETS.TESTS` use registry class names such as `Market1501`, not lowercase folder names such as `market1501`.

## Missing train/query/gallery folders

Common required folders:

- `Market1501`: `Market-1501-v15.09.15/bounding_box_train`, `Market-1501-v15.09.15/query`, `Market-1501-v15.09.15/bounding_box_test`.
- `DukeMTMC`: `DukeMTMC-reID/bounding_box_train`, `DukeMTMC-reID/query`, `DukeMTMC-reID/bounding_box_test`.
- `MSMT17`: either `MSMT17_V2/mask_train_v2` and `MSMT17_V2/mask_test_v2`, or `MSMT17_V1/train` and `MSMT17_V1/test`, plus list files.
- `VeRi`: `veri/image_train`, `veri/image_query`, `veri/image_test`.
- `VehicleID`: `vehicleid/image`, `vehicleid/train_test_split/train_list.txt`, and the selected test list.
- `VeRiWild`: `VERI-Wild/images`, `VERI-Wild/train_test_split/vehicle_info.txt`, train list, query list, and gallery list.

A partial tree is not enough: query and gallery are required for evaluation, and train is required for training.

## Market1501 direct vs nested layout

FastReID prefers:

```text
<datasets-root>/Market-1501-v15.09.15/bounding_box_train
<datasets-root>/Market-1501-v15.09.15/query
<datasets-root>/Market-1501-v15.09.15/bounding_box_test
```

It also accepts a deprecated direct layout:

```text
<datasets-root>/bounding_box_train
<datasets-root>/query
<datasets-root>/bounding_box_test
```

If a validator reports only `bounding_box_train` present, add or restore the missing `query` and `bounding_box_test` folders before evaluation or config-driven loader construction.

## Bad pid/camid parsing

Symptoms:

- `AttributeError` or assertion failure during dataset `process_dir`.
- Train split length is zero despite images existing.
- Camera id assertion fails.
- All samples collapse to the wrong identity or camera.

Dataset-specific parse rules:

- `Market1501` and `DukeMTMC`: names must include `<pid>_c<camera>`, where camera is one digit.
- `VeRi`: names must include `<vehicle-id>_c<three-digit-camera>`.
- `MSMT17`: list row image path must have an underscore-separated camera segment at position 3, and the row must include a pid after a space.
- `VehicleID`: list rows must be `<image-id> <vehicle-id>` and images must exist as `image/<image-id>.jpg`.
- `VeRiWild`: list rows must be `<vehicle-id>/<image-file>` and `vehicle_info.txt` must map image ids to camera ids.

For custom datasets, fail early in `_process_dir` when no parseable rows are found. Silent skipping makes later sampler/evaluator errors harder to diagnose.

## Empty query or gallery

Evaluation requires both query and gallery to be non-empty.

Common causes:

- Missing `query` or `bounding_box_test` / `image_test` folder.
- Images exist but file names do not match the parser regex.
- For `VehicleID`, every vehicle id in the selected test list appears only once; FastReID puts the first sample per id into gallery and later samples into query, so no repeated ids means an empty query.
- For `VeRiWild`, query/gallery list files point to image ids that are missing from `vehicle_info.txt`.

Fix the split files or use a test split with repeated identities before running eval-only commands.

## Sampler batch and `NUM_INSTANCE` failures

Identity samplers need enough identities and compatible batch sizes.

Checks:

- `SOLVER.IMS_PER_BATCH` is global across workers.
- `mini_batch_size = SOLVER.IMS_PER_BATCH // world_size`.
- `mini_batch_size // DATALOADER.NUM_INSTANCE` must be at least 1 for `NaiveIdentitySampler` and `BalancedIdentitySampler`.
- `SOLVER.IMS_PER_BATCH` should be divisible by world size for predictable per-worker minibatches.
- `SetReWeightSampler` additionally requires `batch_size % (sum(DATALOADER.SET_WEIGHT) * DATALOADER.NUM_INSTANCE) == 0` and `batch_size > sum(SET_WEIGHT) * NUM_INSTANCE`.
- If an identity has fewer than `NUM_INSTANCE` images, samplers can sample with replacement, but too few identities can still prevent full batches.

Fallbacks:

- Use `DATALOADER.SAMPLER_TRAIN TrainingSampler` for a simple shuffled stream.
- Lower `DATALOADER.NUM_INSTANCE` or increase `SOLVER.IMS_PER_BATCH` when identity batches cannot be formed.
- Reduce distributed world size or adjust global batch size so per-worker minibatches remain valid.

## Dataloader CUDA stream issues in CPU-only environments

FastReID's dataloader implementation uses CUDA streams for prefetching. A CPU-only environment can still validate layouts and instantiate dataset objects, but full FastReID loader construction/iteration may fail when torch has no CUDA support.

Use the safe validator for layout checks. Treat full dataloader execution as part of training/evaluation and require a compatible runtime backend.

## Stale dataset tests and old imports

Old dataset tests may use imports such as:

```python
from data import get_dataloader
from config import cfg
from data.datasets import init_dataset
```

Those imports are stale for this FastReID API. Use the current package imports instead:

```python
from fastreid.config import get_cfg
from fastreid.data import build_reid_train_loader, build_reid_test_loader
from fastreid.data.datasets import DATASET_REGISTRY
```

Do not use old tests as executable truth when they reference lowercase dataset aliases, debugger hooks, or non-package import paths.

## Custom dataset not registered

Typical error:

```text
KeyError: "No object named 'MyDataset' found in 'DATASET' registry!"
```

Fix:

1. Add `@DATASET_REGISTRY.register()` to the custom dataset class.
2. Ensure the class name exactly matches the config name.
3. Import the module containing the class before loader construction.
4. Print `sorted(DATASET_REGISTRY._obj_map.keys())` during debugging to confirm registration.

## Mixed built-in datasets

When `cfg.DATASETS.NAMES` contains multiple datasets, FastReID concatenates their train tuples and then relabels them in one `CommDataset`. Built-in training tuples prefix pids with dataset names to avoid collisions. Custom datasets should do the same when mixing sources.

Before mixing datasets:

- Verify each dataset independently.
- Make training `pid` and `camid` namespaces unique.
- Avoid mixing incompatible image modalities or radically different filename parsers without an explicit transform/training plan.
