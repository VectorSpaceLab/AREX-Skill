# Checkpoints and `.npz` files

Tensorpack uses two common weight formats in this sub-skill:

- TensorFlow checkpoints: a prefix plus `.index` and `.data-*` files, usually saved by `ModelSaver`.
- `.npz` dictionaries: model-zoo style parameter files that map variable names to numpy arrays.

## Loading choices

| Input type | Best loader | Why |
| --- | --- | --- |
| TF checkpoint prefix | `SmartInit(path)` or `SaverRestore(path)` | Restores variables by exact name from the checkpoint. |
| `.npz` file | `SmartInit(path)` or `DictRestore(dict(np.load(path)))` | Loads a plain name-to-array dictionary. |
| Python dict of arrays | `SmartInit(dict_obj)` or `DictRestore(dict_obj)` | Useful when a script already transformed variable names. |
| List of the above | `SmartInit([a, b, c])` or `ChainInit([...])` | Loads several sources in sequence. |

## Exact-name matching

Tensorpack restores values by exact variable name match.

- Unmatched names are reported as warnings.
- Variables with the same name but incompatible shapes fail by default.
- Use `ignore_mismatch=True` only when the value can be safely cast or reshaped.
- If a checkpoint was saved under a scope prefix, pass `prefix=` or rename the graph variables to match.

Recommended rule: fix names first, then consider relaxing mismatch behavior only for deliberate transfer-learning cases.

## Common helpers

- `load_checkpoint_vars(path)` returns a `{name: value}` dictionary from a checkpoint or `.npz` file.
- `save_checkpoint_vars(dic, path)` writes the same dictionary back to `.npz` or to a checkpoint prefix.
- `dump_session_params(path)` writes the current session's TRAINABLE + MODEL variables to `.npz`.
- `get_all_checkpoints(dir, prefix='model')` returns the sorted checkpoint handles inside a log directory.
- `get_checkpoint_path(path)` normalizes user input such as `checkpoint`, `.index`, or `.data-*` file handles.

## Recommended restore flow

### For inference

```python
pred_config = PredictConfig(
    model=InferenceModel(),
    session_init=SmartInit("/path/to/model-or.npz"),
    input_names=["input_img"],
    output_names=["prediction_img"],
)
```

### For transfer learning

1. Build the new graph with the desired variable names.
2. Load the source parameters with `SmartInit`.
3. Use `ignore_mismatch=True` only if you expect a limited, controlled shape difference.
4. Check the warnings for skipped or unused names before trusting the result.

## Resume notes

- A checkpoint only saves TensorFlow variables.
- Python-side training state is not resumed automatically.
- `AutoResumeTrainConfig` can help training-side resume workflows by finding the latest checkpoint and epoch, but that is a training concern rather than an inference concern.

## Metagraph caution

Do not import a training metagraph for inference.

Why:

- It contains training-only nodes, queues, summaries, and replication machinery.
- It can clash with an already populated graph.
- It is awkward to modify when you only want a clean inference layout.

Instead, rebuild the inference graph directly and restore only the needed weights.

## Helpful inspection flow

1. Run `scripts/inspect_checkpoint.py` on the checkpoint or `.npz` file.
2. Compare the printed variable names with the names exposed by your inference graph.
3. Only then choose `SmartInit`, `SaverRestore`, `DictRestore`, or a name-mapping transform.
4. If the path is a checkpoint directory, `get_all_checkpoints()` can help you choose the latest file without guessing.
