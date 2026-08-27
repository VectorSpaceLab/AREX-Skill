# Troubleshooting

## Unknown dataset spec or source

Symptoms:
- `Unknown dataset specification ...`
- `Unknown dataset name ... for pyg source`
- `Unknown dataset name ... for ogb source`

Checks:
- Verify `--dataset-source` is one of `dgl`, `pyg`, or `ogb` for built-in datasets.
- Verify `--dataset-name` matches one of the supported names exactly.
- For parameterized names, use one colon block with comma-separated pairs.
- Use `+` to join list values such as `label_keys=mu+alpha+homo`.

## Custom module path issues

Symptoms:
- import error for the user dataset module
- module not found when using `--user-data-dir`

Checks:
- Point `--user-data-dir` at a directory, not a single training script.
- The directory must be importable as a Python module path.
- Every visible `.py` file or subpackage under that directory is imported.
- Broken relative imports inside the custom module will fail during import.

## Decorator executes at import time

Symptoms:
- a dataset download starts before any training command is launched
- a module import hangs or raises network or file-system errors

Checks:
- `@register_dataset(...)` stores the dataset dictionary immediately.
- The decorated function is executed during import.
- Keep the registration function lightweight.
- If the function constructs the dataset object itself, that construction must be safe to run at import time.
- The bundled validator avoids this by default; use `--list-only` for capture-only inspection and `--execute-registrations` only when dataset construction is safe.

## Wrong source in a custom dataset dict

Symptoms:
- custom dataset import succeeds, but Graphormer rejects the registry entry

Checks:
- The custom return dictionary must set `source` to `dgl` or `pyg`.
- Do not return `ogb` from the custom registration path.
- OGB belongs to the built-in lookup table path.

## Missing split indices

Symptoms:
- a custom dataset module registers, but the task cannot build the split wrappers

Checks:
- Return `train_idx`, `valid_idx`, and `test_idx`.
- Do not assume Graphormer will infer custom splits for you.
- If the split arrays are empty, re-check the split logic or the dataset size.

## Non-integer features

Symptoms:
- unexpected graph feature shapes
- validation passes but model input quality looks wrong

Checks:
- Graphormer preprocessing keeps integer node and edge features.
- DGL float features are ignored by the Graphormer DGL wrapper.
- Encode categorical node and edge fields as integer IDs.
- Homogeneous graphs are required for the DGL wrapper.

## `max_nodes` filtering

Symptoms:
- fewer samples appear in a batch than expected
- some graphs vanish from a batch

Checks:
- The collator drops graphs whose node count exceeds the batch limit.
- `spatial_pos_max` masks far-away positions with `-inf` rather than resizing the graph.
- `multi_hop_max_dist` truncates the edge history before padding.

## `pyximport` or Cython failures

Symptoms:
- preprocessing import fails before the dataset validator starts
- C-extension build errors mention `pyximport`, `Cython`, or missing NumPy headers

Checks:
- `graphormer.data.wrapper` depends on a compiled `algos` extension.
- Install the build prerequisites before expecting preprocessing to work.
- If imports fail before registry inspection, fix the environment first.
