# Options and consistency for modeling

Use this reference when PyPSA options change how networks are constructed, validated, or accessed. Solver and analysis options are intentionally omitted.

## Modeling-relevant options

| Option path | Default | Use in modeling |
|---|---:|---|
| `api.new_components_api` | `False` | When `True`, `n.generators`/`n.loads`/etc. return `Components` objects instead of static `DataFrame`s. Use `n.c.<component>.static` and `.dynamic` for code that works in both modes. |
| `params.add.return_names` | `False` | Controls whether `n.add(...)` returns added names when `return_names=None`. Pass `return_names=True` directly for local deterministic behavior. |
| `warnings.attribute_typos` | `True` | Enables warnings when a custom attribute is edit-distance close to a real attribute, e.g. `p_no` versus `p_nom`. Disable only for deliberate custom attributes. |
| `api.legacy_string_dtype` | `None` | Controls whether imported string data is coerced back to object dtype. Set explicitly to suppress pandas string-dtype FutureWarnings. |
| `params.consistency.numerical_tolerance` | `1e-9` | Tolerance for numerical comparisons in consistency checks such as `p_min_pu > p_max_pu`. |
| `debug.runtime_verification` | `False` | Enables internal integrity assertions after some mutations. Useful for debugging, not routine large-network construction. |
| `general.allow_network_requests` | `True` | Does not affect local from-scratch modeling, but matters for example/download workflows; route those to I/O guidance. |

## Scoped option changes

Prefer `option_context` for temporary behavior. It takes string/value pairs and restores the previous values even if the block raises.

```python
import pypsa

with pypsa.option_context('api.new_components_api', True):
    assert hasattr(n.generators, 'static')

# Outside the block, the prior option value is restored.
```

Multiple pairs are allowed:

```python
with pypsa.option_context('api.new_components_api', True,
                          'params.add.return_names', True):
    added = n.add('Bus', 'temporary-bus')
```

Global forms are available for notebooks or one-off sessions:

```python
pypsa.set_option('warnings.attribute_typos', False)
value = pypsa.get_option('warnings.attribute_typos')
pypsa.reset_option('warnings.attribute_typos')
```

Environment variables use prefix `PYPSA_` and double underscores for nested paths, for example `PYPSA_API__NEW_COMPONENTS_API=true`. Runtime function arguments override options where a function has the corresponding argument.

## Consistency workflow

Run a structural check before solving or running power flow:

```python
n.consistency_check(strict=['unknown_buses', 'unknown_carriers', 'time_series'])
```

Useful strict choices for modeling checks:

| Strict check | Catches |
|---|---|
| `unknown_buses` | Components whose `bus`, `bus0`, `bus1`, ... values do not exist as `Bus` rows. |
| `unknown_carriers` | Non-empty `carrier` values without a `Carrier` row. |
| `time_series` | Misaligned or inconsistent time-series data. |
| `static_power_attrs` / `time_series_power_attrs` | Invalid power bounds such as min values greater than max values. |
| `nans_for_component_default_attrs` | Missing values where the component schema has a non-empty default. |
| `zero_impedances` / `zero_s_nom` | Passive branch parameters that can break load-flow calculations. |
| `investment_periods` | Global constraints referring to investment periods inconsistent with snapshots. |
| `scenarios_sum` | Scenario probabilities modified after setup so they no longer sum to one. |
| `scenario_invariant_attrs` | Topology or mathematical-structure attributes changed across scenarios. |
| `line_types` / `transformer_types` | Standard type tables differ across scenarios. |
| `dtypes` | Wrong dtypes when `check_dtypes=True` is also passed. |
| `all` | All supported strict checks. Use on small networks first. |

`strict=None` applies PyPSA's default strict checks for dispatch delays, maintenance, and phase-shift bounds. Passing a list replaces the default list, so include all checks that should raise.

For dtype checks:

```python
n.consistency_check(check_dtypes=True, strict=['dtypes'])
```

String attributes may be `object` or pandas string dtype depending on the string-dtype option; the dtype checker accepts either for string attributes.

## What `sanitize()` does and does not do

`n.sanitize()` performs three targeted repairs:

1. Add missing `Bus` rows referenced by components.
2. Add missing `Carrier` rows referenced by components.
3. Assign colors to carriers that lack colors.

It is useful for making a quick exploratory network internally consistent, but it is not a substitute for correcting model intent. It does not:

- fix misspelled bus names when the misspelling created a different intended bus,
- fix duplicated names,
- infer time-series shapes,
- fix contradictory capacity bounds,
- decide technology semantics,
- make scenario-varying topology valid.

Prefer explicit `Carrier` and `Bus` rows in production scripts. Use `sanitize()` when the task asks to heal incomplete component references or when a quick MWE should continue after missing carriers/buses are detected.

## Dependent values and standard types

`n.consistency_check()` calls `n.calculate_dependent_values()` internally. Call it explicitly when you need to inspect derived values after adding or mutating lines/transformers.

Effects include:

- applying `Line.type` and `Transformer.type`,
- filling derived per-unit impedance columns such as `x_pu`, `r_pu`, `x_pu_eff`, `r_pu_eff`,
- propagating line/link/store carrier defaults from connected buses when carrier is empty,
- updating component attributes for extra link ports.

If a typed line or transformer also has manual impedance values, standard type data can override manual values and emit a warning. Choose either a type-driven or manual-impedance pattern unless you intentionally want the override.

## Old-to-new Components API migration

Stable bridge code:

```python
gens = n.c.generators
static = gens.static
dynamic = gens.dynamic
wind_names = static.query("carrier == 'wind'").index
wind_availability = dynamic.p_max_pu.reindex(columns=wind_names)
```

Scoped new API test:

```python
with pypsa.option_context('api.new_components_api', True):
    gens = n.generators          # Components object
    cap = gens.static.p_nom
    dispatch = gens.dynamic.p    # if results/time series exist
```

Default old API equivalent:

```python
cap = n.generators.p_nom
availability = n.generators_t.p_max_pu
```

Migration rules:

- Replace `n.<list_name>` static-table access with `n.c.<list_name>.static` or, inside new API mode, `n.<list_name>.static`.
- Replace `n.<list_name>_t.<attr>` with `n.c.<list_name>.dynamic.<attr>` or, inside new API mode, `n.<list_name>.dynamic.<attr>`.
- Avoid assigning whole `n.generators = df` tables in new API mode; mutate `n.c.generators.static` or use `n.add`/`n.remove`.
- Use `with pypsa.option_context('api.new_components_api', True):` for step-by-step migration, not a session-wide global option, until the script is fully migrated.

## Stochastic and multi-period modeling constraints

Scenarios and investment periods change indexes, so create a tiny test network before scaling.

Investment periods:

- Must be strictly increasing integers.
- Convert snapshots to a two-level `(period, timestep)` `MultiIndex` if snapshots were single-indexed.
- Repeat existing time series across periods when converting from a single-index network.
- Use `investment_period_weightings.objective` for period cost weights and `investment_period_weightings.years` for elapsed-year weights used by global constraints.

Scenarios:

- `set_scenarios` accepts a sequence for equal weights or a mapping/Series/DataFrame/keywords for explicit weights.
- Weights must sum to one within tolerance.
- Changing scenarios after scenarios already exist is not supported.
- Piecewise breakpoint data is not supported on stochastic networks.
- Dynamic data after scenario setup uses columns with levels `['scenario', 'name']`.
- Topology and mathematical structure must be invariant across scenarios: buses, carriers, types, extendability flags, module sizes, committability, active status, and standard type tables cannot differ across scenarios.

Risk preferences are optimization formulation inputs. You may set `n.set_risk_preference(alpha, omega)` only after scenarios exist, but route CVaR solve behavior to the optimization sub-skill.

## Minimal validation snippets

Validate missing buses/carriers strictly:

```python
n.consistency_check(strict=['unknown_buses', 'unknown_carriers'])
```

Repair missing rows, then recheck:

```python
n.sanitize()
n.consistency_check(strict=['unknown_buses', 'unknown_carriers'])
```

Check a multiple-component dynamic table shape before adding:

```python
assert p_set.index.equals(n.snapshots)
assert p_set.columns.equals(names)
n.add('Load', names, bus=buses, p_set=p_set)
```

Compare a migration refactor:

```python
before = n.copy()
with pypsa.option_context('api.new_components_api', True):
    migrated_names = n.generators.static.index
assert set(migrated_names) == set(before.c.generators.names)
```
