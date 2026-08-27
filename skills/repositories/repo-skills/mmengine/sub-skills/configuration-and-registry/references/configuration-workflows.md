# MMEngine Configuration Workflows

This reference covers safe config reading, editing, override merging, dumping, and inspection for MMEngine `Config` and `ConfigDict` objects.

## Core APIs

| Task | API | Notes |
| --- | --- | --- |
| Load a file | `Config.fromfile(filename, use_predefined_variables=True, import_custom_modules=True, use_environment_variables=True, lazy_import=None, format_python_code=True)` | Supports Python, YAML, JSON. Python configs can execute imports or `custom_imports`; inspect unfamiliar configs first. |
| Load text | `Config.fromstring(cfg_str, file_format)` | `file_format` is `py`, `.py`, `yaml`, `yml`, or `json`; useful for snippets and generated configs. |
| Access/edit | `cfg.key`, `cfg['key']`, `cfg.get('key')`, assignment | Nested dicts become `ConfigDict`, so `cfg.model.backbone.depth = 50` and `cfg['model']['backbone']['depth'] = 50` both work. |
| Merge overrides | `cfg.merge_from_dict(options, allow_list_keys=True)` | `options` uses dotted keys; numeric list keys replace list elements when `allow_list_keys=True`. |
| Dump | `cfg.dump(file=None)` | Returns text when `file=None`; writes Python/YAML/JSON when a filename is passed. Dumped inherited configs are standalone. |
| Convert | `cfg.to_dict()` | Converts nested `ConfigDict` values into built-in containers. |

Import pattern:

```python
from mmengine.config import Config, ConfigDict, DictAction, read_base
```

## Loading Files and Strings

Use `Config.fromfile` for real files:

```python
from mmengine.config import Config

cfg = Config.fromfile('config.py')
print(cfg.model.type)
```

Use `Config.fromstring` for generated or inline config text; pass a dotted suffix such as `.py`, `.yaml`, `.yml`, or `.json`:

```python
cfg = Config.fromstring('model = dict(type="ToyModel", depth=18)', '.py')
```

For YAML/JSON snippets, pass the matching dotted format:

```python
cfg = Config.fromstring('model:\n  type: ToyModel\n  depth: 18\n', '.yaml')
```

## Inheritance and Overrides

Text-style config inheritance uses the reserved `_base_` key:

```python
_base_ = ['base_runtime.py', 'base_model.py']
model = dict(backbone=dict(depth=50))
```

Merge behavior:

- Dict fields merge recursively, so `model = dict(backbone=dict(depth=50))` updates the inherited `model.backbone.depth` while retaining other inherited `model` keys.
- Non-dict values, including lists and strings, are replaced wholesale when redefined.
- Set `_delete_=True` inside a replacement dict to drop inherited keys not present in the new dict:

```python
optimizer = dict(_delete_=True, type='SGD', lr=0.01)
```

Reference a value from a base config in text-style files with `{{_base_.key}}`:

```python
_base_ = ['resnet50.py']
model_copy = {{_base_.model}}
```

For Python-style mutation of base variables, use the `_base_` object in Python configs:

```python
_base_ = ['resnet50.py']
model_copy = _base_.model
model_copy.type = 'MobileNet'
```

## Predefined and Environment Variables

Predefined file variables are substituted before config parsing when `use_predefined_variables=True`:

| Token | Meaning |
| --- | --- |
| `{{fileDirname}}` | Directory of the current config file. |
| `{{fileBasename}}` | Config filename including extension. |
| `{{fileBasenameNoExtension}}` | Config filename without extension. |
| `{{fileExtname}}` | Config extension. |

Example:

```python
work_dir = './work_dirs/{{fileBasenameNoExtension}}'
```

Environment variables are substituted before parsing when `use_environment_variables=True`:

```python
data_root = '{{$DATASET:/data/coco/}}'
dataset = dict(ann_file=data_root + 'train.json')
```

If `DATASET=/tmp/coco/`, both `data_root` and derived `dataset.ann_file` see `/tmp/coco/`. This differs from `merge_from_dict`, which happens after parsing and only changes the targeted keys.

For non-string values in Python config syntax, quote the environment expression inside the placeholder:

```python
model = dict(bbox_head=dict(num_classes={{'$NUM_CLASSES:80'}}))
```

## CLI and Programmatic Overrides

MMEngine training scripts often parse CLI overrides with `DictAction` and then call `merge_from_dict`:

```python
from mmengine.config import Config, DictAction

# argparse option:
# parser.add_argument('--cfg-options', nargs='+', action=DictAction)
cfg = Config.fromfile(args.config)
if args.cfg_options is not None:
    cfg.merge_from_dict(args.cfg_options)
```

Equivalent programmatic overrides:

```python
cfg.merge_from_dict({
    'optimizer.lr': 0.001,
    'model.backbone.depth': 50,
    'train_pipeline.0.type': 'LoadImageFromFile',
})
```

`DictAction` accepts simple scalar/list/tuple values from strings:

```bash
python train.py config.py --cfg-options optimizer.lr=0.001 model.in_channels="[1,1,1]"
```

Rules to remember:

- Dotted keys create or update nested dict entries.
- Numeric path parts update list indices only when `allow_list_keys=True`.
- A list index beyond the current list length raises an error.
- `DictAction` parses strings, integers, floats, booleans, `None`, lists, and tuples; it is not a general Python expression evaluator.

## Dumping and Formatting

`cfg.dump()` returns a string. With a filename, MMEngine picks the output format from the suffix:

```python
text = cfg.dump()
cfg.dump('resolved_config.py')
cfg.dump('resolved_config.yaml')
cfg.dump('resolved_config.json')
```

A dumped config with inherited bases is self-contained and no longer needs its `_base_` files.

## Custom Imports and Lazy Import

`custom_imports` ensures modules are imported before later registry builds:

```python
custom_imports = dict(imports=['my_project.models'], allow_failed_imports=False)
model = dict(type='CustomModel')
```

Use it when the config references registered classes/functions whose module may not otherwise be imported. Keep `allow_failed_imports=False` while debugging so import failures are explicit.

Pure Python-style configs can use `read_base()` and import syntax:

```python
from mmengine.config import read_base

with read_base():
    from ._base_.runtime import *

from torch.optim import SGD
optim_wrapper = dict(optimizer=dict(type=SGD, lr=0.01))
```

Lazy import delays building imported objects during parse. If parsing a config only to inspect values, keep `lazy_import=None` unless you know the file uses pure Python-style imports and optional dependencies. If imported objects stringify unexpectedly in dumps, check whether lazy import is active.

## Cross-Repository Configs

MMEngine text configs can inherit external package configs with `package::relative/path.py` when the downstream package follows MMEngine packaging conventions:

```python
_base_ = ['mmdet::_base_/default_runtime.py']
```

Cross-library config usage often pairs `custom_imports` with scope-qualified type strings or `_scope_`; see `registry-reference.md` for registry routing.

## Bundled Inspection Script

From this sub-skill directory:

```bash
python scripts/inspect_config.py --help
python scripts/inspect_config.py path/to/config.py
python scripts/inspect_config.py path/to/config.py --cfg-options optimizer.lr=0.001 train_pipeline.0.type=LoadImageFromFile
python scripts/inspect_config.py --from-string 'model = dict(type="ToyModel")' --format py
python scripts/inspect_config.py path/to/config.py --dump
```

The script only parses and merges overrides; it does not build registry objects, start training, download data, or write output files.
