# Rosie CLI and Workflows

## Native CLI surface

Rosie exposes two top-level actions. Run these commands from the Rosie source directory in a checkout—the directory containing `rosie.py` and the `rosie/` package—unless a container image sets that working directory for you:

```console
python rosie.py run (chamber_of_deputies|federal_senate) [--output=<directory>]
python rosie.py test [chamber_of_deputies|federal_senate|core]
```

`--output` defaults to `/tmp/serenata-data`. The selected output directory is used for downloaded/intermediate datasets, classifier `.pkl` model caches, and the final `suspicions.xz` compressed CSV.

### Run examples

```console
python rosie.py run chamber_of_deputies --output /tmp/serenata-data
python rosie.py run federal_senate --output /tmp/serenata-data
```

The native `run` command calls the selected module's `main(target_directory)`, which constructs an adapter for that directory, constructs `Core(settings, adapter)`, and calls the core pipeline. Accessing the adapter dataset triggers the adapter's update/download methods.

### Test examples

```console
python rosie.py test
python rosie.py test core
python rosie.py test chamber_of_deputies
python rosie.py test federal_senate
```

`test` uses Python `unittest` discovery below the requested Rosie module. A failing test run exits nonzero.

## Safe smoke helper

Use the bundled helper when you need a deterministic import/Core/classifier check before downloading data:

```bash
python scripts/rosie_smoke.py --repo-root <checkout> --smoke invalid-cnpj-cpf
```

`--repo-root` may point to a repository checkout root; the helper adds both that root and its `rosie/` source directory before importing. It creates a synthetic dataframe for the invalid CNPJ/CPF classifier and performs no downloads, model-cache writes, service starts, or dataset updates.

## Core pipeline contract

`Core(settings, adapter)` is the generic suspicion pipeline.

The adapter must provide:

- `dataset`: a pandas dataframe already containing the columns required by the selected classifiers.
- `path`: the directory where model caches and `suspicions.xz` are read or written.

The settings module is expected by the core documentation to provide:

- `CLASSIFIERS`: an ordered mapping from suspicion-column name to classifier class.
- `UNIQUE_IDS`: identifier column name(s), or `None`.
- `VALUE`: the transaction value column name. Current Rosie code documents this constant but does not read it during execution; existing Chamber and Federal settings define `CLASSIFIERS` and `UNIQUE_IDS` only.

Initialization copies either `dataset[UNIQUE_IDS]` when `UNIQUE_IDS` is truthy, or the whole dataset when it is `None`. Classifier output columns are appended to this `suspicions` dataframe.

## Classifier execution and model cache

For each `(name, classifier_class)` in `settings.CLASSIFIERS`:

1. `Core.load_trained_model(classifier_class)` builds the cache filename from the lowercase class name plus `.pkl`, in the adapter output directory.
2. If the `.pkl` exists, the cached model is loaded with joblib.
3. If no cache exists, the classifier is instantiated, fitted on the complete adapter dataset, and dumped to the `.pkl` file.
4. `MonthlySubquotaLimitClassifier` is a special case: it is fitted every run and is not dumped/loaded because the native code treats its cached model as too large for joblib.
5. `Core.predict(model, name)` calls `model.transform(dataset)` and then `model.predict(dataset)`.
6. Predictions are written to the suspicion column named by the `CLASSIFIERS` key.

Prediction arrays with integer dtype use the scikit-learn anomaly convention `1` for inlier and `-1` for outlier. The core converts those values to booleans: `False` for `1`, `True` for `-1`. Classifiers that already return booleans are copied as booleans.

## Safe offline adaptation pattern

The native adapters download or refresh datasets. For deterministic or no-network work, bypass the native `run` command and provide a local adapter:

```python
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from rosie.core import Core
from rosie.core.classifiers import InvalidCnpjCpfClassifier

class StaticAdapter:
    def __init__(self, dataframe, output_dir):
        self.dataset = dataframe
        self.path = output_dir

dataframe = pd.DataFrame({
    "recipient_id": ["22472225000183"],
    "document_type": ["bill_of_sale"],
    "net_value": [10.0],
})
output_dir = Path("/tmp/serenata-data")
output_dir.mkdir(parents=True, exist_ok=True)
settings = SimpleNamespace(
    CLASSIFIERS={"invalid_cnpj_cpf": InvalidCnpjCpfClassifier},
    UNIQUE_IDS=None,
    VALUE="net_value",
)
Core(settings, StaticAdapter(dataframe, str(output_dir)))()
```

Only use this pattern when the dataframe has all columns required by the classifier catalog you selected. If you need Jarbas-ready data loading or database work, route to `deployment-and-data-ops` instead of extending this pipeline.

## When adapting settings

- Keep `CLASSIFIERS` keys stable if downstream consumers expect those suspicion-column names.
- Include only classifiers whose required columns are present after adapter normalization.
- Use `UNIQUE_IDS` when the output should contain only row identifiers plus suspicion booleans. Use `None` when the output should retain the full normalized dataframe plus suspicion columns.
- If adding a custom setting object, include `VALUE` for compatibility with the documented contract even though the current core implementation does not read it.

## Native verification candidates

Use these only when the environment is prepared for the required dependencies or services:

| Candidate | Safety and expected signal |
| --- | --- |
| `python rosie.py --help` | Help-only; usage lists `run`, `test`, the data modules, and `--output`. |
| `python rosie.py test core` | Safe CPU native unit check for Core and invalid CNPJ/CPF behavior. |
| `python rosie.py test chamber_of_deputies` | Candidate when Rosie dependencies and local fixtures are ready; may reveal Pandas/sklearn/adapter regressions. |
| `python rosie.py test federal_senate` | Candidate when Senate fixture/toolbox imports are ready; keep network disabled unless explicitly approved. |
| `python rosie.py run federal_senate` | Networked end-to-end candidate; skip by default unless the user approves downloads. |
