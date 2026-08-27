# Engine API troubleshooting

Use this reference for Python API failures around fitting, parsing,
configuration, persistence, and loading.

## Quick diagnosis table

| Symptom / exception | Likely cause | Corrective action |
|---|---|---|
| `NotTrained` | `parse`, `get_intents`, or `get_slots` was called before `fit`, or an unfitted engine was loaded. | Call `engine.fit(dataset)` first, or load a persisted artifact that was created after fitting. |
| `InvalidInputError` | `parse` or `get_slots` received bytes or a non-`str` object. | Decode bytes to Unicode text and pass a Python `str`. |
| `IntentNotFoundError` | `parse(..., intents=...)` or `get_slots(text, intent)` used an intent absent from the fitted dataset metadata. | Check the exact intent names in the dataset. Remember intent names are case-sensitive. |
| `PersistingError` | `engine.persist(path)` was called with an existing path. | Choose a new directory or explicitly remove/archive the old one before persisting. Never overwrite by accident. |
| `LoadingError` | `from_path` cannot find `nlu_engine.json` or referenced parser/entity metadata. | Verify the artifact directory was produced by `engine.persist` and was copied completely. |
| `IncompatibleModelError` | Persisted model version does not match the importing Snips NLU model version. | Reload with the same compatible package/model version, retrain and persist again, or use `bypass_version_check=True` only for controlled migration/debugging. |
| Missing language resource / `MissingResource` / lookup error | Required language resources are not installed, not linked, or incompatible with the package version. | Install/link resources for the dataset language, typically with `python -m snips_nlu download <language>`, then retry fit/load. |
| Different scores or artifacts across runs | Training is nondeterministic by default or dependency/resource versions differ. | Pass `random_state=<seed>` to `SnipsNLUEngine` and keep package, dependencies, resources, dataset, and Python version fixed. |
| Import/install errors on modern Python | Snips NLU 0.20.2 has old dependency pins, especially around scikit-learn. | Prefer a Python 3.8 CPU environment for inspection and runtime. Python 3.11+ is risky for this package. |

## `NotTrained`

Parsing methods require a fitted engine:

```python
engine = SnipsNLUEngine()
engine.parse("hello")  # raises NotTrained
```

Fix:

```python
engine.fit(dataset)
result = engine.parse("hello")
```

Persisting an unfitted engine is allowed, but loading it returns an unfitted
engine. Check `engine.fitted` when debugging.

## `InvalidInputError`

`parse` and `get_slots` require Python `str` input:

```python
engine.parse(b"turn on lights")  # raises InvalidInputError
```

Fix:

```python
text = raw_bytes.decode("utf8")
engine.parse(text)
```

## `IntentNotFoundError`

This exception appears when a provided intent is not in the fitted dataset:

```python
engine.parse("hello", intents="unknownIntent")
engine.get_slots("hello", "unknownIntent")
```

Fixes:

- confirm spelling and case against the dataset's intent names,
- avoid passing stale dialog-state intent names from an old dataset,
- if using `top_n` plus filters, remember filters must still name known intents,
- pass `None` to `get_slots` only when representing the None intent; it returns
  `[]` and does not raise.

## Persisting and loading failures

`engine.persist(path)` refuses existing paths. This is intentional to prevent
silent model overwrite.

Safe pattern:

```python
from pathlib import Path

path = Path("engine_artifact")
if path.exists():
    raise RuntimeError("choose a fresh artifact directory")
engine.persist(path)
```

`SnipsNLUEngine.from_path(path)` expects a complete persisted artifact. If only
`nlu_engine.json` was copied without parser/entity/resource subdirectories, or
if metadata files are missing, loading can fail with `LoadingError`.

## Model-version compatibility

Persisted metadata stores a Snips NLU model version. For this verified package,
`snips-nlu` is `0.20.2` and the model version is `0.20.0`. Loading an artifact
with a different model version raises `IncompatibleModelError`.

Preferred fixes:

1. Load with the same compatible Snips NLU package/model version used for
   training.
2. Retrain and persist the engine with the target package version.
3. Use `bypass_version_check=True` only if you deliberately accept the risk:

```python
engine = SnipsNLUEngine.from_path("engine_artifact", bypass_version_check=True)
```

Bypass suppresses the version check; it does not repair incompatible parser or
resource formats.

## Missing language resources

Typical messages mention that a language resource was not found and suggest a
resource download. Fit can also fail later if a config requires a gazetteer,
word cluster, stems, stop words, or noise resource unavailable in the selected
language resource package.

Fixes:

```bash
python -m snips_nlu download en
```

or provide a compatible resource package/directory and load it explicitly:

```python
from snips_nlu.resources import load_resources

resources = load_resources("en")
engine = SnipsNLUEngine(resources=resources)
engine.fit(dataset)
```

If a persisted engine contains its required resource subtree, `from_path` can
load those resources without a separate language download. If it still fails,
verify the artifact was copied completely and was persisted by a compatible
package/model version.

## Nondeterministic training

By default, training can produce different scores or serialized artifacts on
repeated runs. Use:

```python
engine = SnipsNLUEngine(random_state=42)
engine.fit(dataset)
```

Keep these stable across runs:

- `snips-nlu` package and model version,
- language resources,
- Python and native dependency versions,
- dataset content/order,
- `random_state` seed.

Very old scikit-learn/Python combinations can still affect deterministic
behavior. Prefer the verified Python 3.8 CPU setup for this package.

## Old dependency and Python-version issues

This package is old. Its dependency pins are more compatible with Python 3.8
than with Python 3.11+. Symptoms include import failures, installation resolver
conflicts, scikit-learn build errors, or runtime incompatibilities in
`sklearn_crfsuite`/`sklearn` components.

Recommended approach:

- use a Python 3.8 CPU environment,
- install the package and its pinned dependencies there,
- avoid upgrading scikit-learn independently unless you are validating a new
  compatibility matrix,
- keep runtime guidance free of machine-specific environment prefixes.

## None intent is not an error

A parsed result with `"intentName": null` means the implicit None intent won.
It is expected for unrelated text. It can appear even with intent filters
because filters do not remove the None intent. Slots should be empty for this
case.
