# Network modeling troubleshooting

Start with a minimal working network that reproduces the issue. Keep it in memory, define carriers and buses explicitly, and run `n.consistency_check(...)` before routing to optimization or analysis.

## Symptom matrix

| Symptom or message | Likely cause | Fix |
|---|---|---|
| `components have buses which are not defined` | A component references a missing `bus`, `bus0`, `bus1`, etc. | Add the intended `Bus` rows before components, or run `n.sanitize()` only if automatically adding missing buses is acceptable. Recheck with `strict=['unknown_buses']`. |
| `components have carriers which are not defined` | Non-empty `carrier` value has no `Carrier` row. | Add explicit `Carrier` rows with `color`/`nice_name`, or run `n.sanitize()` to add missing carriers and colors. |
| Carrier color warnings during plotting checks | Carrier exists but has missing or empty `color`. | Set `n.c.carriers.static.loc[carrier, 'color']` or run `n.c.carriers.assign_colors(...)` / `n.sanitize()`. Plotting itself belongs to analysis. |
| `Names for <Component> must be unique` | Duplicate names passed in one `n.add` call. | Deduplicate names, add a suffix, or intentionally use `overwrite=True` for existing rows. |
| Existing component ignored or warning on add | Name already exists and `overwrite=False`. | Use a new name, remove first, or call `n.add(..., overwrite=True)` when replacement is intended. |
| `Series <attr> has an index which does not align with the passed names` | Static per-component `Series` index differs from component names. | Reindex the series to exactly `names`, including label order and string conversion. |
| `DataFrame <attr> has an index which does not align with the network snapshots` | Time-varying table index differs from `n.snapshots`. | Build the table after `set_snapshots`; use `p_set = p_set.reindex(n.snapshots)` only if missing values are intentional and then fill them. |
| `DataFrame <attr> has columns which do not align with the passed names` | Time-varying table columns differ from component names. | Use `p_set = p_set.loc[:, names]` after verifying all names exist; for suffixes, include the suffix in columns. |
| `Array <attr> has shape ... but expected (snapshots, names)` | 2-D array does not match `(len(n.snapshots), len(names))`. | Convert to a labeled `DataFrame` and assert index/columns before `n.add`. |
| A list intended as time series became static values | Multiple component names plus 1-D list means static per-component values. | For multiple components, pass a 2-D array or `DataFrame` indexed by snapshots and columned by names. |
| A list intended as static values became time series | Single component name plus 1-D list means time-varying over snapshots. | Pass a scalar for static data, or pass multiple names if the list is per component. |
| Attribute typo warning: `Did you mean ...?` | Custom attribute is edit-distance close to a real attribute. | Check `n.c.<component>.defaults.index` and rename the attribute. Suppress only deliberate custom attributes via `pypsa.options.warnings.attribute_typos = False`. |
| Misleading attribute warning: standard attribute for another component | Attribute is valid for another component type, not this one. | Verify component choice or rename custom attribute; this warning is intentionally not suppressed by the typo option. |
| `Network has no components '<name>'` | Wrong component list name or typo when using `n.components.<name>`. | Use list names such as `generators`, `loads`, `lines`, or singular class lookup `n.c['Generator']`. |
| `components '<Component>'` AttributeError in `n.add`/`n.remove` | Misspelled component class name. | Use singular class names like `Bus`, `Generator`, `Load`, `Line`, `Link`, `Store`, `StorageUnit`, `Transformer`. |
| Deprecation warning for `n.generators_t` in new API mode | `api.new_components_api=True`; old dynamic accessor is deprecated. | Use `n.generators.dynamic` inside new API mode or `n.c.generators.dynamic` in mode-independent code. |
| Static setter error in new API mode | Assigning `n.generators = df` when `n.generators` is a `Components` object. | Mutate `n.c.generators.static`, or use `n.add`/`n.remove`; avoid whole-table assignment in new API mode. |
| FutureWarning about pandas `str` dtype on import | String data from imported formats is being coerced for legacy compatibility. | Set `pypsa.options.api.legacy_string_dtype` explicitly: `True` for legacy object dtype, `False` to keep pandas string dtype. File import belongs to I/O, but the option can affect dtype checks. |
| `Weightings not defined for all investment periods` | Assigned investment-period weighting index does not equal `n.investment_periods`. | Reindex the weighting DataFrame/Series exactly to `n.investment_periods`. |
| `Investment periods are not strictly increasing integers` | Period list has duplicates, non-integers, or decreasing order. | Use a sorted integer list such as `[2030, 2040, 2050]`. |
| Scenario weights do not sum to one | `set_scenarios` mapping/Series weights sum is not 1. | Normalize weights before calling `set_scenarios`. |
| `Changing scenarios ... already has scenarios defined is not supported` | Attempted to call `set_scenarios` a second time. | Rebuild from a pre-scenario copy or create a new network with the desired scenario set. |
| Scenario invariant attribute error | Topology/model-structure attributes differ across scenarios. | Keep `bus`, `carrier`, `type`, extendability, module size, committability, active status, and standard type rows identical across scenarios; vary only allowed inputs/time series. |
| Line/transformer type scenario error | Standard type tables differ across scenarios. | Broadcast identical `line_types`/`transformer_types` across all scenarios; do not scenario-customize physical type tables. |
| Piecewise data with scenarios raises not implemented | Stochastic networks do not support piecewise breakpoint data. | Use a deterministic network for piecewise modeling or remove piecewise attributes before setting scenarios. |
| Standard type overrides manual impedance | `Line.type` or `Transformer.type` is set while manual `r`/`x` is also edited. | Choose type-driven parameters or manual parameters. If using type-driven data, inspect after `n.calculate_dependent_values()`. |
| `n.copy()` fails after solve with attached solver model | Solved network has an attached solver model. | Copy before solving, or route solver-model cleanup to optimization guidance. |
| `n.equals(...)` returns false without details | Default `log_mode='silent'`. | Use `n.equals(other, log_mode='verbose')` for logged differences or `'strict'` to raise on first mismatch. |

## Hard case: fix `n.add` DataFrame shape mismatch

Failure pattern:

```python
names = pd.Index(['load-a', 'load-b'], name='name')
# Wrong: columns are bus names, not load names; index may be a RangeIndex.
p_set = pd.DataFrame([[10, 20], [11, 21]], columns=['bus-a', 'bus-b'])
n.add('Load', names, bus=['bus-a', 'bus-b'], p_set=p_set)
```

Repair pattern:

```python
names = pd.Index(['load-a', 'load-b'], name='name')
buses = pd.Series(['bus-a', 'bus-b'], index=names)

p_set = pd.DataFrame(
    [[10.0, 20.0], [11.0, 21.0]],
    index=n.snapshots[:2],
    columns=names,
)

assert p_set.index.equals(n.snapshots[:2])
# If using all snapshots, the index must be n.snapshots exactly:
p_set = p_set.reindex(n.snapshots).ffill().bfill()
assert p_set.index.equals(n.snapshots)
assert p_set.columns.equals(names)

n.add('Load', names, bus=buses, carrier='demand', p_set=p_set)
```

Checklist:

1. Did you call `n.set_snapshots(...)` before building `p_set`?
2. Is `p_set.index.equals(n.snapshots)` true?
3. Is `p_set.columns.equals(names)` true?
4. Is every `bus` value present in `n.c.buses.names`?
5. Is every non-empty `carrier` value present in `n.c.carriers.names`?

## Hard case: migrate old API code under `option_context`

Old API script fragment:

```python
wind = n.generators.query("carrier == 'wind'").index
weekly = n.generators_t.p_max_pu.loc[:, wind].rolling(24).mean()
```

Mode-independent bridge:

```python
gens = n.c.generators
wind = gens.static.query("carrier == 'wind'").index
weekly = gens.dynamic.p_max_pu.loc[:, wind].rolling(24).mean()
```

New API scoped check:

```python
with pypsa.option_context('api.new_components_api', True):
    wind = n.generators.static.query("carrier == 'wind'").index
    weekly = n.generators.dynamic.p_max_pu.loc[:, wind].rolling(24).mean()
```

Migration checklist:

- Replace every `n.<component>` static-table use with `n.c.<component>.static` or `n.<component>.static` inside the scoped new API block.
- Replace every `n.<component>_t.<attr>` with `n.c.<component>.dynamic.<attr>` or `n.<component>.dynamic.<attr>` inside the block.
- Avoid setters like `n.generators = df`; use `n.c.generators.static = df` only when whole-table assignment is genuinely intended, otherwise prefer `n.add`, `n.remove`, or column-level mutation.
- Run a tiny subset through `n.equals(before, log_mode='verbose')` or targeted assertions to confirm the migration did not change table values.

## Debugging sequence for malformed networks

```python
# 1. Verify components and labels.
print(sorted(n.c.keys()))
print(n.c.buses.names)
print(n.c.carriers.names)

# 2. Inspect schema/defaults for a suspect attribute.
print(n.c.generators.defaults.loc[['bus', 'carrier', 'p_nom', 'p_max_pu']])

# 3. Inspect dynamic table labels.
print(n.snapshots)
print(n.c.loads.dynamic.p_set.index)
print(n.c.loads.dynamic.p_set.columns)

# 4. Strict structural check.
n.consistency_check(strict=['unknown_buses', 'unknown_carriers', 'time_series'])

# 5. Optional repair only when missing buses/carriers should be auto-created.
n.sanitize()
n.consistency_check(strict=['unknown_buses', 'unknown_carriers'])
```

If a task asks for solving, power-flow convergence, statistics, plotting, clustering, or file round-trips after this modeling cleanup, route to the appropriate sibling sub-skill.
