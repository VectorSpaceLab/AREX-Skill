# Configuration and persistence

## Default engine configuration

`SnipsNLUEngine(config=None)` defers configuration until `fit(dataset)`. During
fit, the engine reads `dataset["language"]` and uses a packaged default config
when one exists. Packaged defaults include:

- `CONFIG_DE`
- `CONFIG_EN`
- `CONFIG_ES`
- `CONFIG_FR`
- `CONFIG_IT`
- `CONFIG_JA`
- `CONFIG_KO`
- `CONFIG_PT_BR`
- `CONFIG_PT_PT`

Example:

```python
from snips_nlu import SnipsNLUEngine
from snips_nlu.default_configs import CONFIG_EN

engine = SnipsNLUEngine(config=CONFIG_EN, random_state=42)
engine.fit(dataset)
```

If a dataset language has no packaged default config, the engine falls back to
`NLUEngineConfig()`.

## NLUEngineConfig basics

```python
from snips_nlu.pipeline.configs import NLUEngineConfig

config = NLUEngineConfig()
engine = SnipsNLUEngine(config=config)
```

By default, `NLUEngineConfig()` uses two parser stages in order:

1. a deterministic parser for high-precision pattern matches,
2. a probabilistic parser for classification and slot filling.

You can pass parser config objects, parser config dicts, or registered parser
names to `NLUEngineConfig(intent_parsers_configs=...)` when building custom
pipelines:

```python
config = NLUEngineConfig([
    "lookup_intent_parser",
    "probabilistic_intent_parser",
])
engine = SnipsNLUEngine(config=config, random_state=42)
```

For custom processing units, the unit class must be registered under a
`unit_name`, and its configuration must serialize enough state for loading.
This sub-skill covers only engine-level integration; implementation details for
new processing units are outside the normal engine API route.

## Random state and determinism

Use the engine constructor's shared `random_state` keyword for reproducible
training:

```python
engine = SnipsNLUEngine(random_state=42)
engine.fit(dataset)
```

`random_state` may be an integer seed or a NumPy `RandomState`. Keep the seed,
dataset, package/model version, Python/dependency versions, and language
resources fixed. Without a fixed seed, repeated training on the same data can
produce different scores or persisted artifacts.

`NLUEngineConfig` has a `random_seed` constructor parameter, but practical
engine-level reproducibility is driven by the shared `random_state` passed to
`SnipsNLUEngine` and then forwarded to sub-units.

## `force_retrain`

```python
engine.fit(dataset, force_retrain=True)   # default
engine.fit(dataset, force_retrain=False)  # reuse fitted parser sub-units when possible
```

Use `force_retrain=False` only when you intentionally pre-populated
`engine.intent_parsers` with compatible parser objects and want already-fitted
sub-units to be reused. Otherwise prefer the default to avoid stale parser
state.

## Resource loading and persistence

During `fit`, the engine loads the resources required by its configuration for
the dataset language. You may provide resources explicitly with the `resources`
shared keyword to avoid automatic loading:

```python
from snips_nlu.resources import load_resources

resources = load_resources("en")
engine = SnipsNLUEngine(resources=resources)
engine.fit(dataset)
```

When a fitted engine is persisted, the artifact stores the subset of resources
required by the config under the engine directory. Loading with `from_path` can
then use those persisted resources instead of requiring a separate resource
lookup.

If resources are missing during fit, install or link them for the relevant
language. The package's standard resource command is:

```bash
python -m snips_nlu download <language>
```

If a resource directory or resource package is supplied instead of a language
code, it must have the metadata layout expected by Snips NLU.

## Persisting to disk

```python
from pathlib import Path

artifact_dir = Path("nlu_engine_artifact")
engine.persist(artifact_dir)
```

Rules and layout:

- `artifact_dir` must not exist; existing paths raise `PersistingError`.
- The engine writes `nlu_engine.json`, parser subdirectories, entity parser
  subdirectories when present, and a `resources/` subtree when fitted and
  resources are required.
- Persisting an unfitted engine is allowed, but the loaded engine remains
  unfitted and still raises `NotTrained` for parsing methods.
- Duplicate parser unit names are persisted with suffixes such as
  `unit_name_2` while keeping each parser metadata's original unit name.

## Loading from disk

```python
loaded = SnipsNLUEngine.from_path("nlu_engine_artifact")
result = loaded.parse("turn on the kitchen lights")
```

`from_path` requires `nlu_engine.json` and the referenced sub-artifacts. Missing
files raise `LoadingError`.

Persisted engine metadata includes a Snips NLU model version. For this verified
package, the package version is `0.20.2` and the model version is `0.20.0`.
When the persisted model version differs from the importing library's model
version, `from_path` raises `IncompatibleModelError`.

You may bypass the model-version check deliberately:

```python
loaded = SnipsNLUEngine.from_path(
    "nlu_engine_artifact",
    bypass_version_check=True,
)
```

Use bypass only for controlled migration/debugging. It does not guarantee that
old parser or resource files can be loaded correctly.

## Byte-array persistence

```python
payload = engine.to_byte_array()
loaded = SnipsNLUEngine.from_byte_array(payload)
```

The byte-array helpers serialize a temporary zipped processing-unit directory.
They are useful for tests or transport, but disk persistence is easier to
inspect and safer for long-lived artifacts.
