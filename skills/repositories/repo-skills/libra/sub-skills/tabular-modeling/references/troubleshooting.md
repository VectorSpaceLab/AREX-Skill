# Tabular troubleshooting

## Target column is wrong

**Symptom**: the model trains on the wrong column or the prompt seems to match a nearby field instead of the intended target.

**Cause**: Libra extracts target words from the instruction and then uses similarity matching against the dataset columns.

**Fix**:
- Rewrite the instruction so it looks closer to the actual target column name.
- Drop confusing leakage columns before training.
- For text-heavy tabular data, pass `text=[...]` or the explicit parameter the workflow supports.

## `analyze(model=...)` or `model(...)` looks wrong

**Symptom**: `analyze()` raises a `NameError`, or `model()`/`info()` returns unexpected keys.

**Cause**: the key must match an existing entry in `client.models`.

**Fix**:
- Call `print(c.models.keys())` first.
- Use `latest_model` if you just ran one query.
- After a second query, the latest key may have changed.

## Classification ANN refuses to train

**Symptom**: the ANN classification path errors out with a class-count complaint.

**Cause**: the target column needs at least two unique classes.

**Fix**:
- Check the target values.
- Use a different target column or clean the labels.

## Regression ANN save fails on modern Keras

**Symptom**: `regression_query_ann('...', epochs=...)` trains, then fails while saving with a Keras serialization error such as `Layer ModuleWrapper ... must override get_config()`.

**Cause**: `regression_query_ann` defaults `save_model=True`, and modern Keras may not serialize the legacy model graph that Libra builds.

**Fix**:
- For smoke tests and ordinary model inspection, call `regression_query_ann(..., save_model=False)`.
- Save only when you have a compatible legacy Keras stack or have tested serialization in the active environment.
- Always provide an existing writable `save_path` when saving is required.

## Save path or plot path problems

**Symptom**: saving a model or plots fails.

**Cause**: the directory does not exist or is not writable, or the active Keras version cannot serialize a legacy model.

**Fix**:
- Create the directory first.
- Use a temporary output directory during smoke tests.
- Disable saving with `save_model=False` when saving is not the task.

## Dashboard launch is not portable

**Symptom**: `dashboard()` tries to start Streamlit but cannot find the expected dashboard file.

**Cause**: the source dashboard helper uses a hardcoded source-layout path.

**Fix**:
- Treat the dashboard as a source-layout-sensitive helper.
- Use the root troubleshooting notes if you need to adapt the launch command in another environment.

## Imports fail on modern pandas

If the package import fails with `SettingWithCopyWarning` or `FutureWarning` issues, use the root compatibility helper before importing Libra. When running a snippet directly, add the root `scripts/` directory to `PYTHONPATH` first:

```bash
PYTHONPATH=skills/disco/libra/scripts python - <<'PY'
from libra_compat import apply
apply()
from libra import client
apply()
PY
```

If you need a stricter unmodified environment, use the legacy stack described in the root compatibility notes.
