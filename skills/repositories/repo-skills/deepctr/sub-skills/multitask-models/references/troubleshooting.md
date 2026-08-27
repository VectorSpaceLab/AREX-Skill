# Troubleshooting

## Quick checks

Before debugging a multitask build, verify these first:

- `len(task_names) > 1` for SharedBottom, MMOE, and PLE
- `len(task_types) == len(task_names)`
- `task_names` are in the same order you want to read predictions
- `model.output_names` matches the order you intend to compile against
- multi-output `fit()` receives one target array per output
- string sparse inputs use `use_hash=True` or have already been integer-encoded

## Common failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `ValueError: num_tasks must be greater than 1` | Only one task name was provided | Pass at least two task names |
| `ValueError: num_tasks must be equal to the length of task_types` | `task_types` and `task_names` have different lengths | Make both lists the same length |
| `ValueError: task must be binary or regression, ... is illegal` | SharedBottom, MMOE, or PLE received an unsupported task type | Use `binary` or `regression` only |
| `ValueError: task must be binary in ESMM, ... is illegal` | ESMM received a regression or multiclass task | Keep both ESMM task types binary |
| `ValueError: num_experts must be greater than 1` | MMOE was created with one expert | Set `num_experts` to 2 or more |
| `ValueError: SparseFeat(name='...', dtype='string') requires use_hash=True ...` | A string-valued sparse feature was passed without hashing | Set `use_hash=True` or encode the values to integers first |
| Losses appear attached to the wrong head | List-based losses or targets were passed in the wrong order | Inspect `model.output_names` or switch to dict losses/targets |
| `fit()` complains about the target structure | A multi-output model received a single target array | Pass a list like `[y0, y1]` or a dict keyed by output name |
| `predict()` returns a list instead of one array | This is a multi-output model behaving correctly | Unpack the list in output order |

## Output-order reminders

- SharedBottom, MMOE, and PLE return outputs in `task_names` order.
- ESMM returns `[task_names[0], task_names[1]]`, which is conventionally
  `[ctr, ctcvr]`.
- `predict()` uses the same order as `model.output_names`.

## Data-shape reminders

- target arrays usually work best as shape `(batch, 1)`
- sparse feature arrays should match the feature input dtype
- dense features should be numeric and already scaled or normalized when needed
- for a two-label census-style example, drop the original source label columns
  after deriving the multitask labels so they do not leak into the inputs

## If the model compiles but the metrics look wrong

That usually means the model ran, but the output order or target names are not
what you intended. Rebuild the loss/target packing from `model.output_names`
and try the dict form:

```python
losses = {name: "binary_crossentropy" for name in model.output_names}
targets = {name: y for name, y in zip(model.output_names, [y0, y1])}
```

