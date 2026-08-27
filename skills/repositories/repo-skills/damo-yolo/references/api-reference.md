# DAMO-YOLO API reference

This reference lists the verified installed-package surfaces that the generated skill uses. It is not a full source API manual.

## Package identity

- Distribution/import package: `damo`
- Observed version: `0.1.0`
- Minimal import check:

```bash
python - <<'PY'
import damo
print(damo.__version__)
PY
```

## Config APIs

```python
from damo.config.base import parse_config, get_config_by_file, Config
```

Verified signatures:

- `parse_config(config_file)` -> imports a Python config file and returns its `Config()` instance.
- `get_config_by_file(config_file)` -> appends the config file's directory to `sys.path`, imports the module by basename, and instantiates a class named `Config`.
- `Config()` -> base class with `model`, `train`, `test`, `dataset`, and `miscs` EasyDict sections.
- `Config.get_data(name)` -> resolves names containing `coco` through `DatasetCatalog.DATA_DIR` and `DatasetCatalog.DATASETS`; otherwise raises COCO-only errors.
- `Config.merge(cfg_list)` -> only replaces existing top-level attributes, not nested dotted keys.
- `Config.read_structure(path)` -> reads TinyNAS structure text from a path resolved by the current working directory unless the config makes it absolute.

## Model APIs

```python
from damo.detectors.detector import Detector, build_local_model, build_ddp_model
```

Verified signatures:

- `Detector(config)` -> builds `backbone`, `neck`, and `head` from config sections.
- `build_local_model(config, device)` -> constructs `Detector`, initializes it, and moves it to `device`.
- `build_ddp_model(model, local_rank)` -> wraps model with `DistributedDataParallel` on a CUDA rank.

Important runtime behavior:

- `Detector.forward(x, targets=None, tea=False, stu=False)` converts tensors into `ImageList`, runs backbone/neck/head, returns head outputs, teacher FPN features, or `(outputs, fpn_outs)` for student distillation.
- `Detector.load_pretrain_detector(path)` expects checkpoint dictionaries with a `model` key and preserves current head weights while loading body weights.
- `RepConv` layers are switched to deploy form before eval/export in the source workflows.

## Dataset/data-loader APIs

```python
from damo.dataset import build_dataset, build_dataloader
```

Verified signatures:

- `build_dataset(cfg, ann_files, is_train=True, mosaic_mixup=None)` -> builds one or more dataset objects from config dataset names.
- `build_dataloader(datasets, augment, batch_size=128, start_epoch=None, total_epochs=None, no_aug_epochs=0, is_train=True, num_workers=8, size_div=32)` -> builds distributed data loaders; asserts `batch_size % get_world_size() == 0`.

`COCODataset` requires `class_names`, remaps COCO category ids through annotation category names, and returns `(image, target, idx)` where `target` is a `BoxList`.

## Training/evaluation APIs

```python
from damo.apis import Trainer
from damo.apis.detector_inference import inference
```

Verified signatures:

- `Trainer(cfg, args, tea_cfg=None, is_train=True)` -> builds model, optional teacher, optimizer, data loaders, scheduler, EMA, and checkpoints.
- `inference(model, data_loader, dataset_name, iou_types=('bbox',), box_only=False, device='cuda', expected_results=(), expected_results_sigma_tol=4, output_folder=None, multi_gpu_infer=True)` -> distributed dataset inference and COCO evaluation.

## Demo/export surfaces

The generated inference and deployment helpers adapt source demo/converter behavior by importing installed `damo` modules directly:

- `damo.utils.demo_utils.transform_img(...)`
- `damo.utils.boxes.postprocess(...)`
- `damo.utils.visualize.vis(...)`
- `damo.base_models.core.end2end.End2End(...)`
- `damo.utils.model_utils.replace_module(...)`
- `damo.utils.model_utils.get_model_info(...)`

Use sub-skills for complete workflows: training, inference, and deployment.
