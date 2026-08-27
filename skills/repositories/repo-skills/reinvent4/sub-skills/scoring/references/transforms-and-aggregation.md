# Transforms and Aggregation

## Mental Model

A REINVENT4 scoring function does three things:

1. Each endpoint computes a raw component value for each SMILES.
2. Optional `transform.*` settings map raw values into a 0-1 desirability score.
3. `[scoring].type` aggregates transformed endpoint scores using normalized endpoint weights, then applies filters and penalties according to component tags.

Use a standalone `run_type = "scoring"` job to inspect raw and transformed columns before putting the same block into a staged-learning config.

## Transform Catalog

### `sigmoid`

Use when higher raw values should become better scores.

```toml
transform.type = "sigmoid"
transform.low = 0.2
transform.high = 0.8
transform.k = 0.5
```

The transition is centered between `low` and `high`; larger `k` makes the transition sharper.

### `reverse_sigmoid`

Use when lower raw values should become better scores.

```toml
transform.type = "reverse_sigmoid"
transform.low = 1.0
transform.high = 3.0
transform.k = 0.5
```

Common uses: LogP upper control, rotatable bonds, SAScore, docking scores where more negative is better. For docking-like negative values, set `low` to the better/more negative end and `high` to the worse/less negative end if using examples that were validated with reverse sigmoid.

### `double_sigmoid`

Use when a property should stay in a preferred window.

```toml
transform.type = "double_sigmoid"
transform.low = 200.0
transform.high = 500.0
transform.coef_div = 500.0
transform.coef_si = 20.0
transform.coef_se = 20.0
```

Common uses: molecular weight, TPSA, descriptor windows. `low` and `high` define the desirable range. `coef_si` and `coef_se` control the left and right edge steepness; `coef_div` controls the overall scale and is often set near `high` in examples.

### Step Transforms

Use step transforms only when a hard cutoff is intended; they provide no smooth gradient.

```toml
transform.type = "step"
transform.low = 0
transform.high = 3
```

- `right_step`: returns 1 if value is at least `high`.
- `left_step`: returns 1 if value is at most `low`.
- `step`: returns 1 if `low <= value <= high`.

### `exponential_decay`

Use for monotonically decreasing desirability.

```toml
transform.type = "exponential_decay"
transform.k = 1.0
```

`k` must be positive. Negative raw values are clamped to 1.0 by the implementation.

### `value_mapping`

Use for categorical outputs such as `MMP`.

```toml
transform.type = "value_mapping"
[scoring.component.MMP.endpoint.transform.mapping]
MMP = 0.5
"No MMP" = 0.0
```

Any output key not present in the mapping becomes `NaN`, so include every expected category.

## PUMAS Mode

Set `use_pumas = true` under `[scoring]` only when intentionally using the PUMAS desirability transform library. REINVENT maps `custom_product` to `geometric_mean` and `custom_sum` to `arithmetic_mean` in PUMAS mode. Keep configs simple unless a PUMAS-specific transform has been validated separately.

## Aggregation Types

```toml
[scoring]
type = "geometric_mean"
```

Supported names:

- `geometric_mean` / `custom_product`: weighted geometric mean. A near-zero endpoint strongly suppresses the total score. This is the usual choice when all objectives must be acceptable.
- `arithmetic_mean` / `custom_sum`: weighted arithmetic mean. Strong endpoints can compensate for weak endpoints. Use when trade-offs are scientifically acceptable.

Weights are normalized across ordinary scorer endpoints. For example, weights `2.0`, `1.0`, and `1.0` become relative contributions of 50%, 25%, and 25% among those endpoints.

## Filters, Scorers, and Penalties

Component tags determine score flow:

- Scorers are included in weighted aggregation.
- Filters run before scorers and update the valid-mask. A molecule failing a filter receives total score zero regardless of other endpoints. Filters are not also used as ordinary scorer components.
- Penalties are computed after ordinary aggregation and multiply the total score.

Practical examples:

- Use `custom_alerts` as a filter for disallowed SMARTS. Do not tune it by weight; a match zeros the molecule.
- Use `MatchingSubstructure` as a penalty when absence or presence of a substructure should scale the final score rather than invalidate the molecule before aggregation.
- Use ordinary weighted components for soft objectives such as QED, MW, similarity, docking, or QSAR predictions.

## Endpoint Design Patterns

### QED + MW + Similarity

```toml
[scoring]
type = "geometric_mean"

[[scoring.component]]
[scoring.component.QED]
[[scoring.component.QED.endpoint]]
name = "QED"
weight = 1.0

[[scoring.component]]
[scoring.component.MolecularWeight]
[[scoring.component.MolecularWeight.endpoint]]
name = "MW 200-500"
weight = 1.0
transform.type = "double_sigmoid"
transform.low = 200.0
transform.high = 500.0
transform.coef_div = 500.0
transform.coef_si = 20.0
transform.coef_se = 20.0

[[scoring.component]]
[scoring.component.TanimotoSimilarity]
[[scoring.component.TanimotoSimilarity.endpoint]]
name = "ECFP similarity"
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

### Multi-Endpoint Component

```toml
[[scoring.component]]
[scoring.component.pmi]

[[scoring.component.pmi.endpoint]]
name = "PMI npr1"
weight = 0.79
params.property = "npr1"

[[scoring.component.pmi.endpoint]]
name = "PMI npr2"
weight = 0.21
params.property = "npr2"
```

Each endpoint contributes separately to aggregation. Tune weights at endpoint level, not component level, unless the component explicitly documents shared component-level params.

## Debugging Transforms

When total scores look wrong:

1. Run a scoring-only config on known SMILES and inspect both raw and transformed CSV columns.
2. Check that raw values are in the expected units and direction.
3. Temporarily set all weights to 1.0 and reduce to two or three components.
4. Verify no filter is zeroing the molecule before other scorers matter.
5. For geometric aggregation, remember that a single zero or tiny transformed score dominates the total.
6. For `value_mapping`, confirm emitted strings match mapping keys exactly after string conversion.
7. Use `scripts/validate_scoring_config.py --show-params` to verify endpoints and transforms are attached to the intended component key.
