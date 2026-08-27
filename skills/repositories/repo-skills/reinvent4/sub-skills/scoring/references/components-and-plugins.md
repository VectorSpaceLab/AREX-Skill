# Components and Plugins

## Scoring-Only Config Skeleton

A scoring-only job evaluates an existing SMILES file and writes a CSV; it does not sample, train, or update a model.

```toml
run_type = "scoring"

[parameters]
smiles_file = "molecules.smi"
output_csv = "scores.csv"

[scoring]
type = "geometric_mean"
parallel = 4

[[scoring.component]]
[scoring.component.QED]
[[scoring.component.QED.endpoint]]
name = "QED"
weight = 1.0
```

The same component list shape appears under `[stage.scoring]` inside staged learning configs. Stage component files may also contain only `[[component]]` blocks when loaded through `filename`/`filetype`; adapt those into the enclosing `[scoring]` or `[stage.scoring]` context when creating a standalone config.

## Component Block Grammar

Each component block contains exactly one component key and an endpoint list:

```toml
[[scoring.component]]
[scoring.component.MolecularWeight]

[[scoring.component.MolecularWeight.endpoint]]
name = "MW"
weight = 1.0
transform.type = "double_sigmoid"
transform.low = 200.0
transform.high = 500.0
transform.coef_div = 500.0
transform.coef_si = 20.0
transform.coef_se = 20.0
```

Rules that matter in practice:

- Component keys are case-insensitive and hyphen/underscore-insensitive: `TanimotoSimilarity`, `tanimoto_similarity`, and `tanimotosimilarity` resolve to the same registered class.
- Every endpoint gets a display `name`; if omitted, REINVENT uses the component key.
- `weight` defaults to `1.0` and must be non-negative. Filters ignore weights for aggregation behavior.
- Component-level `params` may be shared across endpoints; endpoint `params` override component-level values.
- Component parameter classes receive lists internally, one value per endpoint. In TOML, write ordinary endpoint values under `params.*`; the framework collects them into lists.
- Multi-endpoint components repeat `[[...endpoint]]` under one component block. Each endpoint can have a different name, weight, params, and transform.

## Common Built-In Components

### RDKit Physicochemical

- `QED`/`Qed`: drug-likeness, already 0-1.
- `MolecularWeight`: RDKit molecular weight.
- `SlogP`: Crippen LogP.
- `TPSA`: topological polar surface area; optional `params.includeSandP`.
- `HBondAcceptors`, `HBondDonors`, `NumRotBond`, `Csp3`, `NumHeavyAtoms`, `NumHeteroAtoms`, `NumRings`, `NumAromaticRings`, `NumAliphaticRings`, `NumAtomStereoCenters`, `GraphLength`, `LargestRingSize`, `numsp`, `numsp2`, `numsp3`.
- `PMI`: 3D shape descriptors with `params.property = "npr1"` or `"npr2"`; use two endpoints to score both.
- `MolVolume`: 3D molecular volume; requires RDKit conformer generation.
- `RDKitDescriptors`: arbitrary descriptor by `params.descriptor`.
- `SAScore`: synthetic accessibility; raw lower-is-better range is approximately 1-10, so usually apply `reverse_sigmoid`.

### Similarity, SMARTS, and MMP

```toml
[[scoring.component]]
[scoring.component.TanimotoSimilarity]
[[scoring.component.TanimotoSimilarity.endpoint]]
name = "Similarity to reference"
weight = 1.0
params.smiles = ["CC(=O)OC1=CC=CC=C1C(=O)O"]
params.radius = 3
params.use_counts = true
params.use_features = true
transform.type = "sigmoid"
transform.low = 0.2
transform.high = 0.7
transform.k = 0.5
```

- Prefer `TanimotoSimilarity`; `TanimotoDistance` remains accepted for backward compatibility but emits a deprecation warning in the implementation.
- `GroupCount` counts SMARTS matches and can be shaped with a transform.
- `custom_alerts` is a filter: any matching SMARTS sets the total score to zero before ordinary aggregation.
- `MatchingSubstructure` is tagged as a penalty; use it when a SMARTS should multiply/penalize the total score rather than remove a molecule before aggregation.
- `MMP` returns categorical strings such as `"MMP"` or `"No MMP"`; combine it with `value_mapping`.
- `RingPrecedence` reads a precomputed ring database JSON and supports `params.nll_method` and `params.make_generic`.

### External and Optional Components

- `ExternalProcess` executes one local program for all endpoints in the component. It sends SMILES on stdin and expects JSON on stdout with `payload` keys matching endpoint `params.property` values.
- `REST` posts to a service endpoint and extracts numeric prediction output. Keep service URL, port, endpoint, predictor id/version, and headers explicit per endpoint.
- `ChemProp` requires Chemprop v1 (`reinvent[chemprop1]`) and reads `checkpoint_dir`, `features`, and `target_column`.
- `ChemProp2` requires Chemprop v2 (`reinvent[chemprop2]`) and reads `model_path`, optional featurizer settings, and `target_column` for multitask models.
- `Qptuna` reads a serialized Qptuna model file.
- `ROCSSimilarity`/`rocssimilarity` requires OpenEye toolkits and a valid license; configure `rocs_input`, `color_weight`, `shape_weight`, `similarity_measure`, conformer limits, and optional color force field.
- `DockStream`, `Icolos`, `Maize`, `SynthSense`/`CAZP`, and contributed Lilly/MolScore/Mordred-style components require external tools, model files, environment variables, or services. Treat their examples as patterns and verify the external runtime separately.

## ExternalProcess Contract

```toml
[[scoring.component]]
[scoring.component.ExternalProcess]
params.executable = "python"
params.args = "score_model.py --model model.pkl"

[[scoring.component.ExternalProcess.endpoint]]
name = "affinity"
weight = 1.0
params.property = "affinity"
transform.type = "reverse_sigmoid"
transform.low = -12.0
transform.high = -6.0
transform.k = 0.5
```

The external command must print JSON similar to:

```json
{"version": 1, "payload": {"affinity": [-8.4, -6.2]}}
```

When one `ExternalProcess` block has multiple endpoints, all endpoints must use the same executable and args. Split the config into separate component blocks if different commands are required.

## REST Contract

`REST` expects a live service and parses the service response into one score array per endpoint. In configs, include `params.server_url`, `params.server_port`, `params.server_endpoint`, `params.predictor_id`, `params.predictor_version`, and optionally `params.header`. Validate service response shape with a small request before using it inside REINVENT because scoring failures propagate as component errors.

## Custom Plugin Discovery

REINVENT discovers scoring plugins through the `reinvent_plugins.components` namespace package.

Checklist for a new plugin:

1. Put the plugin on `PYTHONPATH` or install it so Python can import `reinvent_plugins.components` as a native namespace package.
2. Use the namespace directory shape `reinvent_plugins/components/` and avoid `__init__.py` in the top-level namespace directories unless the installed package intentionally owns a normal package subtree. A normal package at the namespace root can hide other namespace contributors.
3. Name plugin modules `comp_<name>.py`. Files not starting with `comp_` are ignored. Subdirectories are scanned recursively.
4. Export one or more component classes tagged with `@add_tag("__component")` from `reinvent_plugins.components.add_tag` or the equivalent local import.
5. Tag a Pydantic dataclass with `@add_tag("__parameters")` when parameters are needed. The fields must be list-typed because endpoint params are collected across endpoints.
6. Return `ComponentResults` from `__call__`, usually with one NumPy array per endpoint.
7. Use `@add_tag("__component", "filter")` only for global pre-aggregation filters and `@add_tag("__component", "penalty")` only for score multipliers.
8. Use `np.nan` for molecules that fail to score rather than silently returning 0, unless the scientific meaning is truly zero.

Minimal no-parameter component pattern:

```python
__all__ = ["NitrogenCount"]
from typing import List
import numpy as np
from pydantic.dataclasses import dataclass
from rdkit import Chem
from reinvent_plugins.components.add_tag import add_tag
from reinvent_plugins.components.component_results import ComponentResults
from reinvent_plugins.mol_cache import molcache

@add_tag("__parameters")
@dataclass
class Parameters:
    pass

@add_tag("__component")
class NitrogenCount:
    def __init__(self, params: Parameters):
        pass

    @molcache
    def __call__(self, mols: List[Chem.Mol]) -> ComponentResults:
        scores = [np.nan if mol is None else sum(a.GetAtomicNum() == 7 for a in mol.GetAtoms()) for mol in mols]
        return ComponentResults([np.array(scores, dtype=float)])
```

Use it in TOML after the module is discoverable:

```toml
[[scoring.component]]
[scoring.component.NitrogenCount]
[[scoring.component.NitrogenCount.endpoint]]
name = "N count"
weight = 1.0
transform.type = "reverse_sigmoid"
transform.low = 0
transform.high = 5
transform.k = 0.5
```

Run `scripts/list_scoring_components.py --verbose` to confirm the module imported and the component registered before debugging the scoring config itself.
