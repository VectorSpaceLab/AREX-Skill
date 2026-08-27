# Extension registration patterns

SDGX managers use pluggy entry points. Extension packages define a subclass, import the correct `hookimpl`, and register a name with the manager.

## Entry point groups

| Component | Hook module | Entry point group | Manager list command |
| --- | --- | --- | --- |
| Model | `sdgx.models.extension` | `sdgx.model` | `sdgx list-models` |
| Data connector | `sdgx.data_connectors.extension` | `sdgx.data_connector` | `sdgx list-data-connectors` |
| Data processor | `sdgx.data_processors.extension` | `sdgx.data_processor` | `sdgx list-data-processors` |
| Data exporter | `sdgx.data_exporters.extension` | `sdgx.data_exporter` | `sdgx list-data-exporters` |
| Cacher | `sdgx.cachers.extension` | `sdgx.cacher` | `sdgx list-cachers` |
| Metadata inspector | `sdgx.data_models.inspectors.extension` | `sdgx.metadata.inspector` | inspect with `InspectorManager` |

## Minimal model extension

`pyproject.toml`:

```toml
[project]
name = "my-sdgx-model"
dependencies = ["sdgx"]

[project.entry-points."sdgx.model"]
my_model = "my_sdgx_model.model"
```

`my_sdgx_model/model.py`:

```python
from sdgx.models.base import SynthesizerModel
from sdgx.models.extension import hookimpl

class MyModel(SynthesizerModel):
    def fit(self, metadata, dataloader, *args, **kwargs):
        ...
    def sample(self, count, *args, **kwargs):
        ...
    def save(self, save_dir):
        ...
    @classmethod
    def load(cls, save_dir, **kwargs):
        ...

@hookimpl
def register(manager):
    manager.register("MyModel", MyModel)
```

## General notes

- Subclass the corresponding base class: `DataConnector`, `DataProcessor`, `DataExporter`, `Cacher`, or `Inspector`.
- Register human-readable names; managers normalize to lowercase.
- For connectors, implement `_read`, `_columns`, and `_iter` where practical.
- For processors, implement `fit`, `convert`, and `reverse_convert` with metadata-aware behavior.
- For inspectors, implement `fit` and `inspect`; set `pii=True` and `inspect_level` when the type should override broad inspectors.
- For cachers, implement `load`, `iter`, `is_cached`, and cache cleanup/invalidation.
