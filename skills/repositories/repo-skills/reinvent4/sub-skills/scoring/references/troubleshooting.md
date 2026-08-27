# Scoring Troubleshooting

## Fast Triage

1. Run `reinvent --help` to confirm the console script is importable. If help fails during plotting imports, ensure `scipy` is installed because the CLI imports `scipy.stats.gaussian_kde` through plotting utilities in some environments.
2. Run `scripts/validate_scoring_config.py CONFIG.toml --show-params` to verify the config has a scoring block and component/endpoint structure.
3. Run `scripts/list_scoring_components.py --verbose` to verify the expected component class is registered.
4. If a standalone scoring run fails, reduce to one SMILES and one component, then add filters, transforms, and external components back incrementally.

## Config Shape Errors

### Wrong Run Type

Use `run_type = "scoring"` for scoring-only runs. Other valid run types such as `sampling`, `transfer_learning`, `staged_learning`, and `enumeration` have different outer sections; only the scoring block is shared.

### Missing Scoring Block

A standalone scoring config needs `[scoring]` with `type` and `[[scoring.component]]` entries. Stage component files loaded by `filename` may contain only `[[component]]` entries; those are fragments, not full scoring-only configs.

### Endpoint Attached to the Wrong Table

The endpoint table must repeat the same component key:

```toml
[[scoring.component]]
[scoring.component.MolecularWeight]
[[scoring.component.MolecularWeight.endpoint]]
name = "MW"
```

A typo in the endpoint table can create a different nested table and leave the real component without endpoints.

### Unknown Component

The registry normalizes names by lowercasing and removing hyphens/underscores. If `TanimotoSimilarity`, `tanimoto_similarity`, and `tanimotosimilarity` all fail, the module probably did not import or the class was not tagged.

## Plugin Discovery Failures

Symptoms:

- `Unknown scoring component: MyComponent`.
- `scripts/list_scoring_components.py` does not list your class.
- REINVENT logs that a component module could not be imported.

Checks:

- The module file is named `comp_mycomponent.py`; files without the `comp_` prefix are ignored.
- The module is under an importable `reinvent_plugins/components/` namespace path or a scanned subdirectory.
- The plugin path is on `PYTHONPATH` or installed in the active environment.
- The top-level namespace is not accidentally blocked by an incompatible `__init__.py` in `reinvent_plugins` or `components`.
- The component class has `@add_tag("__component")`, `@add_tag("__component", "filter")`, or `@add_tag("__component", "penalty")`.
- The parameter dataclass, if present, has `@add_tag("__parameters")` and is a dataclass.
- Imports at module top level do not fail. Optional dependencies should be guarded or installed before discovery.
- `__all__` is not required for discovery, but keep it accurate for manual imports and readability.

For custom `NitrogenCount`-style plugins, first verify direct import:

```python
from reinvent_plugins.components import comp_nitrogen_count
```

Then verify discovery with the bundled listing helper.

## Optional Dependency Failures

### OpenEye ROCS

`ROCSSimilarity` requires OpenEye toolkits and a valid license. Installation alone is insufficient if the license cannot be read. Verify the license in the same environment and shell where REINVENT runs. Also check `rocs_input`, `similarity_measure`, conformer settings, and custom color force field paths.

### Chemprop v1/v2

`ChemProp` supports Chemprop v1 only. `ChemProp2` supports Chemprop v2 only. The optional extras conflict intentionally, so do not install both into the same environment unless the package manager explicitly supports a compatible isolated setup. For multitask models, configure `target_column` and ensure it is unique per endpoint.

### iSIM

The `isim` extra is installed from a Git source in package metadata. Expect network or credential restrictions in locked-down environments; scoring configs should not assume iSIM-dependent functionality is available unless the environment was prepared with that extra.

### External Tool Components

Docking, Maize, Icolos, Qptuna, SynthSense/CAZP, LillyMol, Lilly medchem, MolScore, and Mordred-style contributed components depend on external executables, model files, environment variables, services, or large data files. Keep absolute paths and credentials out of reusable skill content; document them as user-supplied local inputs in the working project config.

## ExternalProcess Failures

Common causes:

- `params.executable` is not found or is not executable.
- `params.args` cannot be split as intended; quote arguments carefully.
- The child process writes logs before JSON on stdout.
- The child process returns JSON without a top-level `payload` object.
- `params.property` is not present in `payload`.
- The returned score list length does not match the number of SMILES.
- Multiple endpoints in one `ExternalProcess` block try to use different executable/args; split into multiple blocks.

Expected stdout shape:

```json
{"version": 1, "payload": {"predictions": [0.5, 0.6]}}
```

Debug by running the external program manually with a two-line SMILES stdin payload before embedding it in REINVENT.

## REST Failures

Common causes:

- Service not running or wrong `server_url`/`server_port`/`server_endpoint`.
- Header format differs from the service expectation.
- `predictor_id` or `predictor_version` rejected.
- Response status is non-200.
- Response body does not contain parseable successes and numeric outputs.
- Timeout or load-shedding under parallel scoring.

Validate a small request outside REINVENT first. For production runs, decide whether retries, circuit breakers, or service-side batching are needed; REINVENT's generic component expects a healthy service.

## Transform and Aggregation Surprises

- QED already returns 0-1; adding an unnecessary transform can distort it.
- Raw molecular weight, LogP, docking, and SAScore values are not naturally 0-1; transform them before aggregation.
- `geometric_mean` is intentionally harsh: a zero-like endpoint dominates the total.
- `arithmetic_mean` allows compensation and can hide a failing objective.
- Negative weights are rejected.
- Zero weights effectively remove endpoints from weighted influence but still leave component computation overhead.
- `custom_alerts` is a filter, not a weighted objective.
- `MatchingSubstructure` is a penalty, not a filter; confirm whether multiplication after aggregation is the desired semantics.
- `value_mapping` emits `NaN` for unmapped categories, so map every emitted label exactly.
- `parallel` is capped by config validation and internal worker limits; higher values may not improve external/service components.

## Filtering Semantics

Filters run before ordinary scorers and update the valid mask. A molecule that fails a filter can appear with reported filter component output, but its total score becomes zero. This differs from treating a SMARTS check as a low-weight soft component. If the molecule should remain optimizable but discouraged, use a scorer or penalty instead of a filter.

## Safe Validation Commands

- `python scripts/validate_scoring_config.py scoring.toml --show-params`: parse and summarize without running scoring.
- `python scripts/list_scoring_components.py --verbose`: discover registered component classes without scoring molecules.
- `reinvent --help`: confirm CLI availability and installed-package imports.
- `reinvent scoring.toml --log-level debug`: run an actual scoring job only after paths, external services, and optional dependencies are ready.
