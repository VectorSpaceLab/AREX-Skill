# Workflows

## 1) API-first export

Use this when the fitted estimator already lives in Python memory.

1. Confirm the fitted object is from a supported family.
2. Choose the matching exporter function for the target language.
3. Pass only the naming arguments that the exporter supports.
4. Capture the returned string and write it to a file if needed.

Example:

```python
from pathlib import Path
import m2cgen as m2c

code = m2c.export_to_java(
    model,
    package_name="demo.models",
    class_name="TinyModel",
    function_name="predict",
)
Path("TinyModel.java").write_text(code, encoding="utf-8")
```

## 2) CLI export from a serialized model

Use this when the model is already serialized or when shell composition is easier.

1. Make sure the model class is importable in the unpickling environment.
2. Choose `pickle` or `joblib` as the serialization format.
3. Pick a target language and the matching naming flags.
4. Feed the file path or pipe the bytes through stdin.
5. Redirect stdout to the desired output file.

Examples:

```bash
python -m m2cgen model.pkl --language java --package_name demo.models --class_name TinyModel > TinyModel.java
cat model.pkl | m2cgen --language python > model.py
```

## 3) Choose naming flags by target

- Java: `--package_name`, `--class_name`
- C#: `--namespace`, `--class_name`
- Visual Basic, Haskell, Elixir: `--module_name`
- All targets: `--function_name`

## 4) Handle large ensembles

If export fails with recursion depth errors:

1. Reduce ensemble size or depth if possible.
2. Increase `--recursion-limit` for the CLI.
3. Re-run the export.

## 5) Smoke-check the skill tree

Run the helper from the `model-export` directory:

```bash
python scripts/smoke_export.py
```

The default command creates a fixed local `LinearRegression` model, calls each public exporter, and executes the **Python** scorer to compare one prediction. For all other languages it checks only for an expected source-code shape; it does not compile or execute those outputs, test a user model, or replace repository e2e coverage.

### Safety and filesystem boundary

- The script uses `exec()` only for Python source returned by `m2cgen.export_to_python()` for the tiny model it creates itself. Do not treat it as safe for untrusted generated source, a modified script, or an untrusted exporter/model object.
- The default path does not spawn a subprocess or create serialized files. With `--cli`, the script launches `sys.executable -m m2cgen` without a shell and feeds it only a pickle it created in memory. It captures child stdout/stderr rather than writing generated output files.
- `--cli` creates an `m2cgen-smoke-*` `TemporaryDirectory` for its pickle (and, if selected, joblib) file. The context manager removes that directory when the CLI check exits, including when a check raises; copy any diagnostic artifact you need before then. No temp directory exists on the default path.
- `--joblib` and `--console-script` require `--cli`; passing either without it is rejected rather than silently reported as a successful partial run. `--joblib` additionally requires `joblib`. `--console-script` resolves `m2cgen` through `PATH`, so enable it only when that PATH is trusted; the default and plain `--cli` paths do not use that executable.

For example, use `python scripts/smoke_export.py --cli --joblib` only when you intend to exercise the optional joblib path. A successful smoke check is limited to the paths named above and is not evidence that legacy e2e expected values, foreign toolchains, or arbitrary serialized models have been validated.

## 6) Route unsupported models

If the model is conceptually close but not directly supported:

1. Prefer the nearest supported estimator from the same family.
2. For meta-estimators such as RANSAC, make sure the base estimator is supported.
3. For XGBoost and LightGBM, choose a supported booster or objective variant.