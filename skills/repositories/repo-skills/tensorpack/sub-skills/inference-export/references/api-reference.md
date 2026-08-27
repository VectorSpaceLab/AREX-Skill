# API reference

Verified against the installed API inspection facts for Tensorpack 0.11.

## Predictor construction

| Object | Signature | Notes |
| --- | --- | --- |
| `PredictConfig` | `(model=None, tower_func=None, input_signature=None, input_names=None, output_names=None, session_creator=None, session_init=None, return_input=False, create_graph=True)` | Build from a `ModelDesc`, a plain tower function plus `input_signature`, or an already wrapped `TowerFunc`. `output_names` is required. `input_names` defaults to the `input_signature` names. |
| `OfflinePredictor` | `(config)` | Builds a fresh graph and session from `PredictConfig`, then accepts numpy inputs and returns numpy outputs. |
| `OnlinePredictor` | `(input_tensors, output_tensors, return_input=False, sess=None)` | Wraps an existing session and explicit tensors. Useful when the graph is already built elsewhere. |
| `FeedfreePredictor` | `(config, input_source)` | Runs inference from an `InputSource` rather than from feed dicts. `return_input` is not supported. |
| `MultiTowerOfflinePredictor` | `(config, towers)` | Builds one predictor per tower and shares a session. Mostly useful for multi-GPU inference. |
| `DataParallelOfflinePredictor` | `(config, towers)` | Builds one predictor that uses multiple towers in a data-parallel layout. Inputs and outputs are not split automatically. |

## Session initializers

| Object | Signature | Notes |
| --- | --- | --- |
| `SmartInit` | `(obj, *, ignore_mismatch=False)` | Accepts a TF checkpoint, a dict of numpy arrays, a `.npz` file, an empty string / `None`, or a list of those. Chooses `SaverRestore`, `DictRestore`, `ChainInit`, or no-op heuristically. |
| `SaverRestore` | `(model_path, prefix=None, ignore=())` | Restores a TensorFlow checkpoint saved by `tf.train.Saver` or `ModelSaver`. Exact variable-name match is required. |
| `SaverRestoreRelaxed` | `(model_path, prefix=None, ignore=())` | Like `SaverRestore`, but can tolerate some cast / reshape mismatches. Use only when the value layout is truly compatible. |
| `DictRestore` | `(variable_dict, ignore_mismatch=False)` | Restores from a dictionary of `{name: value}` numpy arrays. Exact-name matching still applies. |
| `ChainInit` | `(sess_inits)` | Runs a list of session initializers sequentially. |
| `JustCurrentSession` | no arguments | No-op initializer used when nothing needs to be restored. |

## Export

| Object | Signature | Notes |
| --- | --- | --- |
| `ModelExporter` | `(config)` | Uses the same `PredictConfig` as the predictor path. |
| `ModelExporter.export_serving` | `(filename, tags=None, signature_name='prediction_pipeline')` | Exports a SavedModel directory with variables and a single prediction signature. |
| `ModelExporter.export_compact` | `(filename, optimize=True, toco_compatible=False)` | Exports a frozen / pruned `GraphDef` `.pb`. The optimization step can fail on some graphs. |

## Checkpoint and variable helpers

| Helper | Signature | Notes |
| --- | --- | --- |
| `load_checkpoint_vars` | `(path)` | Loads every variable from a checkpoint into a `{name: value}` dict. |
| `save_checkpoint_vars` | `(dic, path)` | Saves a dict to `.npz` or to a TF checkpoint depending on the file extension. |
| `load_chkpt_vars` | alias of `load_checkpoint_vars` | Backward-compatible alias used by older scripts. |
| `save_chkpt_vars` | alias of `save_checkpoint_vars` | Backward-compatible alias used by older scripts. |
| `dump_session_params` | `(path)` | Dumps TRAINABLE + MODEL variables from the current session to `.npz`. |
| `get_checkpoint_path` | `(path)` | Normalizes user input such as `checkpoint`, `.index`, or `.data-*` handles into a reader-friendly checkpoint prefix. |
| `get_all_checkpoints` | `(dir: str, prefix: str = 'model')` | Returns a sorted list of `(checkpoint_name, step)` pairs. |

## Name helpers

| Helper | Signature | Notes |
| --- | --- | --- |
| `get_op_tensor_name` | `(name)` | Converts an op or tensor name into `(op_name, tensor_name)`. Use it when normalizing names from checkpoints, signatures, or graph lookups. |
| `get_tensors_by_names` | `(names)` | Resolves a list of tensor names from the default graph. Useful inside predictor construction and export helpers. |

## Practical notes

- `PredictConfig` + `OfflinePredictor` is the standard path for simple inference from numpy arrays.
- `OnlinePredictor` is for existing sessions and explicit tensor handles.
- `SmartInit` is the preferred entry point for loading checkpoints, `.npz` model-zoo files, dicts, or chained initializers.
- Exact variable-name matching is the default rule everywhere. Shape mismatches must be fixed or explicitly relaxed.
- `ModelExporter` uses the same tower function as inference, so the clean graph you build for prediction is the one that gets exported.
