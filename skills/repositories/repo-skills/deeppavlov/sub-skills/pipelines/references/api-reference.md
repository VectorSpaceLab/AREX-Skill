# API Reference

This reference reflects the verified DeepPavlov 1.7.x public pipeline APIs and
config semantics. Use it when you need exact call signatures or when a config
error points to a specific loader, trainer, or Chainer field.

```text
build_model(config: Union[str, pathlib.Path, dict], mode: str = 'infer', load_trained: bool = False, install: bool = False, download: bool = False) -> Chainer
train_model(config: [str, pathlib.Path, dict], install: bool = False, download: bool = False, recursive: bool = False) -> Chainer
evaluate_model(config: [str, pathlib.Path, dict], install: bool = False, download: bool = False, recursive: bool = False) -> dict
train_evaluate_model_from_config(config: Union[str, pathlib.Path, dict], iterator: Union[DataLearningIterator, DataFittingIterator] = None, *, to_train: bool = True, evaluation_targets: Optional[Iterable[str]] = None, install: bool = False, download: bool = False, start_epoch_num: Optional[int] = None, recursive: bool = False) -> Dict[str, Dict[str, float]]
read_data_by_config(config: dict)
get_iterator_from_config(config: dict, data: dict)
parse_config(config: Union[str, pathlib.Path, dict], overwrite: Optional[dict] = None) -> dict
deep_download(config: Union[str, pathlib.Path, dict]) -> None
```

## Verified Public APIs

| API | Return | What it does | Important notes |
| --- | --- | --- | --- |
| `build_model(config, mode='infer', load_trained=False, install=False, download=False)` | `Chainer` | Parses a config, optionally installs requirements and downloads resources, imports declared modules, then builds the pipeline. | If `load_trained=True`, trainable components get `load_path = save_path` when `save_path` exists. |
| `train_model(config, install=False, download=False, recursive=False)` | `Chainer` | Runs training and then reloads the trained pipeline. | This is the convenience wrapper when you want a trained model object back. |
| `evaluate_model(config, install=False, download=False, recursive=False)` | `dict` | Runs the configured evaluation path without training. | Returns metrics, not a model object. |
| `train_evaluate_model_from_config(config, iterator=None, to_train=True, evaluation_targets=None, install=False, download=False, start_epoch_num=None, recursive=False)` | `Dict[str, Dict[str, float]]` | Shared training/evaluation implementation used by both convenience APIs and CLI modes. | `recursive=True` trains nested `config_path` configs before the outer config. |
| `read_data_by_config(config)` | dataset object | Loads data through `dataset_reader` or the legacy `dataset` shortcut. | The `dataset` shortcut is classification-only in this release. |
| `get_iterator_from_config(config, data)` | iterator | Builds the configured dataset iterator from already-read data. | Config values are resolved before the iterator is constructed. |
| `parse_config(config, overwrite=None)` | `dict` | Resolves aliases, overwrites, requirements, variables, and nested placeholders. | Dot notation in `overwrite` walks nested dicts/lists; numeric segments index lists. |
| `deep_download(config)` | `None` | Downloads resources declared by `metadata.download` and nested configs. | No install happens here; it only downloads resources. |

## Chainer Field Semantics

`chainer` is the core pipeline container.

- `in`: pipeline inputs for inference.
- `out`: values returned from `__call__`.
- `in_y`: additional ground-truth inputs used by training/evaluation.
- `pipe`: ordered component list.
- `id`: stores a component in the local build registry so later steps can reuse it.
- `ref`: reuses a previously initialized component by id.
- `main`: marks the component that should be treated as the pipeline’s main trainable/save target.
- `config_path`: embeds another config as a nested component or sub-pipeline.
- `overwrite`: dot-notation overrides applied to a nested `config_path` before it is built.

Other important behavior from the loader:

- Components may be registered names or fully qualified `module.submodule:ClassName` strings.
- Component constructor kwargs are resolved recursively before instantiation.
- Any string value that starts with `#` can resolve a previously stored component id, for example `#tokenizer` or `#tokenizer.val`.
- If `load_trained=True` is used and a component has `fit_on` or `in_y`, its `load_path` is copied from `save_path` when available.
- `Chainer.save()` uses the main component when one is marked, otherwise it falls back to the last pipeline component.

## Training Config Semantics

A training config normally contains:

- `dataset_reader`
- `dataset_iterator`
- `chainer`
- `train`

The training section commonly controls:

- `class_name`: trainer implementation; default is `torch_trainer`.
- `metrics`: list of metric definitions or names. The first metric is used for early stopping.
- `start_epoch_num`: optional resume point when training is continued.

Trainable component fields:

- `fit_on`: input names for estimator-style components.
- `in_y`: ground-truth names for NN-style components.
- `save_path` / `load_path`: persistence locations.
- `main`: marks the component that should be saved or reloaded as the model’s main output.

The `dataset` shortcut is only for the built-in classification path. For other
workflows, use explicit `dataset_reader` and `dataset_iterator` sections.

## Configuration Variables

`parse_config` applies three layers of substitution:

1. Exact placeholder matches such as `{ROOT_PATH}` or `{CONFIGS_PATH}`.
2. `metadata.variables` entries in the config itself.
3. Environment overrides of the form `DP_<VARIABLE_NAME>`.

Useful facts:

- `DEEPPAVLOV_PATH` is prefilled by the loader and can be overridden through
  `DP_DEEPPAVLOV_PATH`.
- `DP_ROOT_PATH` is commonly used in configs that define a `ROOT_PATH` variable.
- `metadata.requirements` is complemented by requirement files inferred from
  registered components and by nested configs.
- `metadata.imports` is imported before the pipeline components are instantiated.

## CLI-to-API Mapping

- `install` → install only the config’s declared requirement files.
- `download` → run `deep_download` only.
- `train` → `train_evaluate_model_from_config(..., to_train=True)`.
- `evaluate` → `train_evaluate_model_from_config(..., to_train=False)`.
- `interact` → build the model and prompt for inputs in a loop.
- `predict` → stream batch inference from stdin or a file.
- `crossval` → `calc_cv_score(...)` via the CLI wrapper.
- `paramsearch` → grid search over `search_choice` values.

When a CLI mode fails, check whether the config itself is valid before assuming
an execution problem. Most loader errors are config-shape or registry issues,
not trainer bugs.
