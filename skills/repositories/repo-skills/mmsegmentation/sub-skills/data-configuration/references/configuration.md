# MMSegmentation Configuration

MMSegmentation uses MMEngine `Config` files. A config normally composes model, dataset, schedule, and runtime pieces through `_base_`, then overrides only the fields that differ for the experiment.

## Config Shape

Common top-level fields are:

- `_base_`: a string or list of inherited config files.
- `model`: segmentor, data preprocessor, decode head, auxiliary head, train/test settings, and class-count-sensitive head options.
- `train_pipeline`, `test_pipeline`, `tta_pipeline`: ordered transform dictionaries.
- `train_dataloader`, `val_dataloader`, `test_dataloader`: sampler, worker, batch, and nested dataset configs.
- `val_evaluator`, `test_evaluator`: usually `IoUMetric` for semantic segmentation.
- `default_scope`, `env_cfg`, `default_hooks`, `log_processor`, `load_from`, `resume`: runtime fields from the default runtime base.

Base configs are commonly grouped by component type:

- model bases define the segmentor, backbone, decode head, losses, and `SegDataPreProcessor`.
- dataset bases define `dataset_type`, `data_root`, pipelines, dataloaders, and evaluators.
- schedule bases define optimizer wrappers, schedulers, loops, and hooks.
- runtime bases define default scope, environment config, logging, checkpoint, and visualization hooks.

## Inheritance Rules

- Prefer inheriting an existing complete method config when modifying an existing architecture.
- Prefer a primitive config that combines one model base, one dataset base, one schedule base, and one runtime base when creating a new method family.
- Keep inheritance shallow. The repository convention recommends one primitive config per method folder and other configs inheriting from that primitive.
- If `Config.fromfile()` fails with a missing `_base_`, check that the path is relative to the config file that declares it, not relative to the shell working directory.
- When replacing nested lists or dictionaries, inspect the expanded config first so the edit targets the field that actually reaches the runner.

## Config Names

MMSegmentation config filenames typically encode:

```text
{algorithm}_{model-components}_{training-settings}_{train-dataset-and-resolution}_{optional-test-dataset}
```

Useful examples of name parts:

- `8xb2` means eight GPUs times batch size two per GPU in the reference recipe.
- `40k`, `80k`, or `160k` means iteration-based schedule length.
- `cityscapes-512x1024` or `ade20k-512x512` identifies dataset and crop/resize recipe.
- component names such as `r50-d8`, `mit-b0`, `upernet`, or `deeplabv3` summarize model structure; detailed implementation belongs in the model sub-skill.

Treat the filename as documentation, not enforcement. The actual behavior is in the expanded config.

## Inspect Configs Safely

Use the bundled script instead of relying on a source-checkout utility that writes fixed files by default:

```shell
python sub-skills/data-configuration/scripts/inspect_mmseg_config.py \
  --config PATH/TO/MMSEG_CONFIG.py \
  --show-keys train_dataloader.dataset train_pipeline val_evaluator
```

Print the fully expanded config:

```shell
python sub-skills/data-configuration/scripts/inspect_mmseg_config.py \
  --config PATH/TO/MMSEG_CONFIG.py
```

Apply overrides before printing or dumping:

```shell
python sub-skills/data-configuration/scripts/inspect_mmseg_config.py \
  --config PATH/TO/MMSEG_CONFIG.py \
  --cfg-options train_dataloader.batch_size=1 train_dataloader.num_workers=2 \
  --show-keys train_dataloader
```

Dump only when explicitly requested:

```shell
python sub-skills/data-configuration/scripts/inspect_mmseg_config.py \
  --config PATH/TO/MMSEG_CONFIG.py \
  --cfg-options work_dir=work_dirs/debug \
  --dump expanded_debug_config.py
```

## Override Syntax

`--cfg-options` receives key-value pairs in `key=value` format and merges them into the config before use.

- Use dotted keys for nested fields: `train_dataloader.batch_size=1`.
- Quote tuple/list values in shells: `model.backbone.strides="(1, 2, 1, 1)"`.
- For comma-separated lists without brackets, avoid spaces: `model.backbone.out_indices=0,1,2,3`.
- For strings that look like Python literals, quote intentionally if a string is required.
- Do not pass both deprecated `--options` and `--cfg-options`; use `--cfg-options` only.

## Dataset Fields In Configs

A typical dataset base defines:

```python
dataset_type = 'CityscapesDataset'
data_root = 'data/cityscapes/'
train_dataloader = dict(
    batch_size=2,
    sampler=dict(type='InfiniteSampler', shuffle=True),
    dataset=dict(
        type=dataset_type,
        data_root=data_root,
        data_prefix=dict(img_path='leftImg8bit/train', seg_map_path='gtFine/train'),
        pipeline=train_pipeline))
```

For dataset edits, inspect all three layers:

- `dataset_type` and class metadata: controls built-in class names, palette, suffix defaults, and custom loader behavior.
- `data_root`, `data_prefix`, `ann_file`, `img_suffix`, `seg_map_suffix`: controls file discovery.
- `pipeline`: controls loading, augmentation, label remapping, and packing.

## Packaged Indexes

- `model-index.yml` imports metafiles for model families and is useful for discovering available config families and pretrained recipe names.
- `dataset-index.yml` maps dataset aliases to packaged download roots and expected `data_root` values for supported datasets.
- Index files are catalogs; the active run behavior still comes from the selected config after inheritance and overrides.
