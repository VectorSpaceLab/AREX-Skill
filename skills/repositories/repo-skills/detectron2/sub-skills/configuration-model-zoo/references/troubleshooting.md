# Configuration and Model-Zoo Troubleshooting

## Wrong Config Path

Symptoms:

- `RuntimeError: ... not available in Model Zoo!`
- A path works in a source checkout but fails after installation.
- A LazyConfig component loads, but expected model/train keys are missing.

Likely causes and fixes:

- Pass a path relative to the model-zoo config collection, such as `COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_1x.yaml`, not an absolute source checkout path.
- Include the correct extension. `.yaml` and `.py` select different loaders and different config object types.
- For local custom files, use `cfg.merge_from_file(local_yaml)` for Yacs or `LazyConfig.load(local_py)` for LazyConfig instead of `model_zoo.get_config_file()`.
- Some `common/` LazyConfig files are components. Inspect top-level keys before assuming they include `model`, `train`, and `dataloader`.

## Mixing Yacs and LazyConfig Override Syntax

Symptoms:

- `merge_from_list()` rejects override length or fails to decode values.
- `LazyConfig.apply_overrides()` raises parse errors, `ValueError`, or `KeyError`.
- An override silently targets the wrong key casing.

Fix:

| Config type | Correct syntax | Incorrect syntax |
| --- | --- | --- |
| Yacs `CfgNode` | `MODEL.DEVICE cpu` as alternating list entries | `MODEL.DEVICE=cpu` |
| LazyConfig | `model.device='cpu'` as one string | `MODEL.DEVICE cpu` |

Yacs uses uppercase schema keys such as `MODEL.WEIGHTS`. LazyConfig usually uses Python-style nested keys such as `model.device`, `train.init_checkpoint`, and `dataloader.train.total_batch_size`.

## Non-Serializable LazyConfig Save

Symptoms:

- `LazyConfig.save()` writes YAML plus an additional `.pkl` file.
- Logs mention objects that cannot serialize to valid YAML.
- Reloaded YAML differs because callables or lambdas could not be represented cleanly.

Fix:

- Treat `LazyConfig.save()` output as a convenience artifact, not a guarantee for every Python object.
- Replace lambdas, open file handles, or runtime-created objects with importable callables or plain values when the config must round-trip through YAML.
- Use `LazyConfig.to_py()` for human inspection when serialization is only needed for review.

## Unresolved Relative Imports in LazyConfig

Symptoms:

- `ImportError` mentions relative import, directory import, or a missing `.py` file.
- A config works only from one current working directory.

Fix:

- LazyConfig relative imports can only import other config files. They cannot import directories through `from . import package_dir`.
- Keep related config fragments as `.py` files and import symbols from those files.
- Use `LazyConfig.load_rel("relative_file.py")` inside config code when a string filename is clearer than Python import syntax.
- For custom packages, use absolute Python imports and ensure the package is installed or importable in the runtime environment.

## Model-Zoo Checkpoint Download or Network Surprise

Symptoms:

- A simple-looking check tries to fetch `https://dl.fbaipublicfiles.com/detectron2/...`.
- `DefaultPredictor` or `model_zoo.get(..., trained=True)` stalls or fails in an offline environment.
- The user wanted a URL but the code attempted to build a model.

Fix:

- Use `model_zoo.get_checkpoint_url(config_path)` to print a URL without downloading.
- Use `model_zoo.get_config(config_path, trained=False)` for static inspection.
- Do not call `model_zoo.get()`, `DefaultPredictor`, or `DetectionCheckpointer.load()` during config-only validation.
- If offline inference is required, set an explicit local `MODEL.WEIGHTS` or `train.init_checkpoint` and leave file existence/compatibility checks to the inference workflow.

## Mismatched `MODEL.WEIGHTS` or `train.init_checkpoint`

Symptoms:

- Checkpoint loading reports missing or unexpected keys.
- A config points to ImageNet pretraining when the user expected final detector weights.
- A LazyConfig has no `train.init_checkpoint` field.

Fix:

- Distinguish initialization weights from trained detector weights. `trained=False` keeps the config's original weight setting; this may be an ImageNet backbone initializer.
- `trained=True` injects the official final checkpoint URL only when the model-zoo mapping supports the config.
- For Yacs configs, set `cfg.MODEL.WEIGHTS` explicitly.
- For LazyConfigs, inspect `LazyConfig.to_py(cfg)` and set `cfg.train.init_checkpoint` only when that field exists and is part of the config's training/build convention.

## Stale `_BASE_` Inheritance

Symptoms:

- Changing a base YAML does not appear in a derived config.
- A derived YAML overrides a value that the user expected to come from its base.
- A copied YAML fails because its relative `_BASE_` path no longer resolves.

Fix:

- `_BASE_` is resolved relative to the YAML file that declares it.
- Child configs override base values when the same key appears in both.
- When copying config files, copy the needed base files too or rewrite `_BASE_` to a valid relative location.
- Dump the merged config with `cfg.dump()` to confirm the effective value, not just the source YAML text.

## CPU/GPU Device Override Confusion

Symptoms:

- CPU-only machines fail with CUDA device errors.
- A Yacs override appears accepted but LazyConfig model construction still targets CUDA.
- `model_zoo.get()` changes behavior depending on CUDA availability.

Fix:

- For Yacs, set `MODEL.DEVICE cpu` or `cfg.MODEL.DEVICE = "cpu"` before building predictors/models.
- For LazyConfig, inspect for `cfg.model.device`; if present, set `model.device='cpu'` or `cfg.model.device = "cpu"`.
- `model_zoo.get(config_path, device="cpu")` can force CPU when intentionally building a model, but it is not a static inspection call.
- Do not assume `MODEL.DEVICE` exists in LazyConfig objects; inspect top-level keys first.
