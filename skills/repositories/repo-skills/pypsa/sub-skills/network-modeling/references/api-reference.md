# Network modeling API reference

This reference is for constructing and mutating in-memory PyPSA `Network` objects. It intentionally excludes file formats, optimization, power flow, plotting, statistics, and clustering.

## Core signatures

| API | Signature | Modeling notes |
|---|---|---|
| `pypsa.Network` | `Network(import_name='', name='Unnamed Network', ignore_standard_types=False, **kwargs)` | Use empty `import_name` for from-scratch modeling. Standard `LineType` and `TransformerType` rows are loaded unless `ignore_standard_types=True`. Loading from files is an I/O task. |
| `Network.add` | `n.add(class_name, name, suffix='', overwrite=False, return_names=None, **kwargs)` | Main component-construction API. `return_names=None` follows option `params.add.return_names`; pass `return_names=True` for a deterministic returned `pd.Index`. |
| `Network.remove` | `n.remove(class_name, name, suffix='')` | Drops static rows and matching columns from all dynamic tables for that component type. |
| `Network.set_snapshots` | `n.set_snapshots(snapshots, default_snapshot_weightings=1.0, weightings_from_timedelta=False)` | Set before adding time-varying data. Reindexes dynamic tables and fills missing values from attribute defaults. Timezone-aware datetimes are not accepted. |
| `Network.set_investment_periods` | `n.set_investment_periods(periods)` | Periods must be unique, strictly increasing integers. Converts single-index snapshots to a two-level `(period, timestep)` snapshot `MultiIndex` and repeats time series across periods. |
| `Network.set_scenarios` | `n.set_scenarios(scenarios=None, **kwargs)` | Creates stochastic structure. Accepts a sequence for equal probabilities, a `dict`/`Series` for weights, or keyword weights. Weights must sum to one. Cannot be changed once set. |
| `Network.consistency_check` | `n.consistency_check(check_dtypes=False, strict=None)` | Calls `calculate_dependent_values()` and checks unknown buses/carriers, time series, bounds, periods, scenarios, dtypes when requested, and related structure. |
| `Network.sanitize` | `n.sanitize()` | Adds missing buses, adds missing carriers, and assigns deterministic carrier colors. It does not fix wrong names, bad shapes, infeasible capacities, or unintended custom attributes. |
| `Network.copy` | `n.copy(snapshots=None, investment_periods=None, ignore_standard_types=False)` | Deep-copies a network, optionally filtered by snapshots/periods. Copy before solving; solved networks with attached solver model can raise. |
| `Network.equals` | `n.equals(other, log_mode='silent')` | Compare two networks. Use `log_mode='verbose'` for diagnostics or `'strict'` to raise on first mismatch. |
| Options | `pypsa.option_context(*pairs)`, `pypsa.set_option(path, value)`, `pypsa.get_option(path)` | `option_context` takes string/value pairs, e.g. `pypsa.option_context('api.new_components_api', True)`. |

## `Network.add` shape rules

`Network.add` decides static versus time-varying placement from the number of component names and the shape of each attribute value.

| Call shape | Attribute value shape | Stored as | Correct pattern |
|---|---|---|---|
| Single component name | Scalar | Static value | `n.add('Load', 'load', bus='bus', p_set=10)` stores `p_set` in `n.c.loads.static`. |
| Single component name | 1-D list/array/Series with length `len(n.snapshots)` | Dynamic time series | `n.add('Generator', 'wind', p_max_pu=pd.Series(..., index=n.snapshots))`. |
| Multiple component names | Scalar | Broadcast static value | `n.add('Bus', ['a', 'b'], v_nom=110)`. |
| Multiple component names | 1-D list/array/Series with length `len(names)` | Static per-component values | `n.add('Bus', names, x=[0, 1])`; for `Series`, the index must equal `names`. |
| Multiple component names | 2-D array with shape `(len(n.snapshots), len(names))` | Dynamic time series | `n.add('Load', names, p_set=array)`. |
| Multiple component names | `DataFrame` | Dynamic time series | Index must equal `n.snapshots`; columns must equal `names` in the same labels/order. |

Important consequences:

- For a single component, a non-scalar `p_set`, `p_max_pu`, `q_set`, etc. is treated as time-varying over snapshots.
- For multiple components, a 1-D list is static per component; use a 2-D `DataFrame` for time-varying data.
- If a dynamic value is supplied, the corresponding static column still keeps its default; operational code uses the dynamic table when the component name appears in that dynamic table.
- Duplicated names raise `ValueError`. Use unique names, a `suffix`, or `overwrite=True` intentionally.
- A list `suffix` can be used only with a scalar base name, creating one component per suffix.
- Dictionaries are not accepted as dynamic attribute values; use `Series` or `DataFrame`.

## Component defaults and schemas

Each component type carries a defaults table in `n.c.<component>.defaults` and `n.components['ComponentName'].defaults`. Use it to discover:

- valid attribute names,
- whether an attribute is static, varying, or static-or-varying,
- expected dtype and default value,
- whether an attribute is input or output.

Unspecified attributes are filled from this defaults table. Custom attributes can be added, but they are descriptive only unless PyPSA code explicitly uses them. If a custom attribute is close to a standard attribute name, PyPSA may warn about a possible typo.

Package-level custom component types can be registered with `pypsa.components.types.add_component_type(...)` by supplying a defaults `DataFrame` with the same structure as built-in component defaults. Treat this as advanced session-wide schema modification: it changes the component type library for the current Python process.

## Components store and table access

Prefer the stable Components store for new code:

```python
c = n.c.generators              # same as n.components.generators
static = c.static               # component rows x static attributes
dynamic = c.dynamic             # dict-like: attribute -> snapshots x component names
defaults = c.defaults           # schema/default table
names = c.names                 # component names; scenario dimension removed if present
```

Useful store access patterns:

| Pattern | Meaning |
|---|---|
| `n.components` or `n.c` | Dict-like store of all component classes. |
| `n.c.generators` | `Components` object for `Generator`. |
| `n.c['Generator']` or `n.c['generators']` | Same component via singular class name or list name. |
| `n.c.generators.static` | Static generator `DataFrame` (old `n.generators` under default API). |
| `n.c.generators.dynamic.p_max_pu` | Dynamic generator availability table (old `n.generators_t.p_max_pu`). |
| `n.c.generators.names` | Unique generator names, without scenario level. |
| `n.c.generators.extendables`, `.fixed`, `.committables`, `.modulars` | Indexes derived from nominal capacity, committable, and module-size attributes. |
| `n.c.generators.get_active_assets(period)` | Boolean active mask using `active`, `build_year`, and `lifetime`. |
| `n.c.generators.get_activity_mask(sns)` | Snapshot-by-component activity mask. |
| `n.c.buses.rename_component_names(old='new')` | Rename component names and update cross-references. |

## Old and new Components API

PyPSA supports both old table access and the new Components API. Use `n.c.<component>.static` and `n.c.<component>.dynamic` for code that works under both.

| Access | Default API (`api.new_components_api=False`) | Opt-in API (`api.new_components_api=True`) |
|---|---|---|
| `n.generators` | Static generator `DataFrame` | `Generators` Components object |
| `n.generators_t` | Dynamic dict-like table store | Still accessible but emits a deprecation warning; use `n.generators.dynamic` |
| `n.components.generators` / `n.c.generators` | Components object | Components object |
| Static data | `n.generators` or `n.c.generators.static` | `n.generators.static` or `n.c.generators.static` |
| Dynamic data | `n.generators_t.p` or `n.c.generators.dynamic.p` | `n.generators.dynamic.p` or `n.c.generators.dynamic.p` |

Scoped migration pattern:

```python
with pypsa.option_context('api.new_components_api', True):
    gens = n.generators
    wind = gens.static.query("carrier == 'wind'")
    wind_availability = gens.dynamic.p_max_pu.loc[:, wind.index]
```

Do not assign `n.generators = ...` inside the new API mode; static setters raise. Mutate `n.c.generators.static` or use `n.add(...)`/`n.remove(...)`.

## Snapshots, periods, and scenarios

- Networks default to a single snapshot named `now`.
- `n.snapshot_weightings` has `objective`, `stores`, and `generators` columns.
- `n.timesteps` is the timestep level. With investment periods, `n.snapshots` becomes a `(period, timestep)` `MultiIndex` and `n.periods`/`n.investment_periods` returns the period level.
- `n.investment_period_weightings` has `objective` and `years` columns.
- After `n.set_scenarios(...)`, static component tables are broadcast to a scenario/name `MultiIndex`, and dynamic tables use scenario/name columns. Topology and mathematical-structure attributes must stay identical across scenarios.
- `n.scenario_weightings` is a `DataFrame` with a `weight` column, and `n.has_scenarios` becomes `True`.

## Standard types and dependent values

`LineType` and `TransformerType` rows are standard component tables loaded into a new network by default. If a `Line` or `Transformer` has a non-empty `type`, PyPSA derives electrical parameters from the matching type when dependent values are calculated.

Use one of these patterns:

```python
# Standard type pattern: type determines electrical data.
n.add('Line', 'line', bus0='a', bus1='b', length=10, type='Al/St 240/40 4-bundle 380.0')
n.calculate_dependent_values()

# Manual pattern: no type; provide impedance data yourself.
n.add('Line', 'line', bus0='a', bus1='b', r=0.01, x=0.1, s_nom=100)
```

Avoid mixing manual `r`/`x` values with a non-empty `type` unless you want standard type data to override the manual values and possibly emit an override warning.

## Copy, equality, and mutation safety

- Use `n.copy()` for independent mutation; simple assignment `m = n` only creates another reference.
- Use `n.copy(snapshots=..., investment_periods=...)` to reduce large networks before experimentation.
- If a solved network has an attached solver model, copying may raise. Copy before solving or route solver-model handling to the optimization sub-skill.
- Use `n.equals(other, log_mode='verbose')` or `'strict'` when checking whether a mutation preserved network structure.
