# Synthesizer workflows

## `Synthesizer` signature

Inspected signature:

```python
Synthesizer(
    model,
    model_path=None,
    model_kwargs=None,
    metadata=None,
    metadata_path=None,
    data_connector=None,
    data_connector_kwargs=None,
    raw_data_loaders_kwargs=None,
    processed_data_loaders_kwargs=None,
    data_processors=None,
    data_processors_kwargs=None,
)
```

`model` may be a registered name such as `"CTGAN"`, a model class, or a model instance. When `model` or `data_connector` is a string, SDGX uses the corresponding manager and lowercases the name.

## CTGAN from a DataFrame

```python
import pandas as pd
from sdgx.data_connectors.dataframe_connector import DataFrameConnector
from sdgx.models.ml.single_table.ctgan import CTGANSynthesizerModel
from sdgx.synthesizer import Synthesizer

df = pd.DataFrame({"age": [20, 30, 40, 50], "role": ["a", "b", "a", "c"]})
synthesizer = Synthesizer(
    model=CTGANSynthesizerModel(epochs=1, batch_size=10, device="cpu"),
    data_connector=DataFrameConnector(df),
)
synthesizer.fit()
sampled = synthesizer.sample(10)
assert sampled.columns.tolist() == df.columns.tolist()
```

For real training, increase rows and epochs; do not treat a one-epoch smoke test as quality evidence.

## CTGAN from CSV

```python
from sdgx.data_connectors.csv_connector import CsvConnector
from sdgx.models.ml.single_table.ctgan import CTGANSynthesizerModel
from sdgx.synthesizer import Synthesizer

connector = CsvConnector(path="input.csv")
synthesizer = Synthesizer(
    model=CTGANSynthesizerModel(epochs=10, batch_size=500),
    data_connector=connector,
    raw_data_loaders_kwargs={"cacher_kwargs": {"cache_dir": "cache/raw"}},
)
synthesizer.fit()
sampled = synthesizer.sample(1000, chunksize=200)
```

`sample(count, chunksize=None, model_sample_args=None)` returns a DataFrame when `chunksize` is `None`, and yields DataFrame chunks when `chunksize` is set.

## GaussianCopula direct import

```python
from sdgx.data_connectors.dataframe_connector import DataFrameConnector
from sdgx.data_loader import DataLoader
from sdgx.data_models.metadata import Metadata
from sdgx.models.statistics.single_table.copula import GaussianCopulaSynthesizerModel

dataloader = DataLoader(DataFrameConnector(df))
metadata = Metadata.from_dataframe(df)
model = GaussianCopulaSynthesizerModel(metadata=metadata, default_distribution="beta")
model.fit(metadata, dataloader)
sampled = model.sample(100)
```

This model is CPU-friendly and useful for fast shape/round-trip checks. It supports distribution choices such as `norm`, `beta`, `truncnorm`, `uniform`, `gamma`, and `gaussian_kde` for numerical columns.

## Save and load

```python
save_dir = synthesizer.save("model-dir")
loaded = Synthesizer.load(save_dir, model=CTGANSynthesizerModel)
sampled = loaded.sample(100)
```

The save directory contains metadata JSON and a model subdirectory. `Synthesizer.load` requires the model class or registered name because not every model supports generic pickle-only loading.

## Custom metadata and processors

```python
from sdgx.data_models.metadata import Metadata
metadata = Metadata.from_dataframe(df)
metadata.datetime_format = {"event_date": "%Y-%m-%d"}
metadata.update({"specific_combinations": {("education", "educational-num")}})

synthesizer = Synthesizer(
    model="CTGAN",
    model_kwargs={"epochs": 5, "device": "cpu"},
    data_connector=DataFrameConnector(df),
    metadata=metadata,
)
```

Use `data_processors=[...]` only when you need to remove or replace the default processor chain. If you override it, keep column-order and formatter behavior when output column fidelity matters.
