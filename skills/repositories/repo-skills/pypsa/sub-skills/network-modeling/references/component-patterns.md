# Component modeling patterns

Use these patterns to build small, explicit, self-contained PyPSA networks before moving to larger data-loading or optimization workflows.

## Minimal safe skeleton

Define carriers first, then buses, then components that reference those buses and carriers.

```python
import pandas as pd
import pypsa

n = pypsa.Network(name='model')

n.add('Carrier', 'AC', nice_name='electricity', color='#1f77b4')
n.add('Carrier', 'wind', nice_name='wind', color='#2ca02c')
n.add('Carrier', 'gas', nice_name='gas', color='#8c564b')
n.add('Carrier', 'demand', nice_name='demand', color='#7f7f7f')

n.set_snapshots(pd.date_range('2024-01-01', periods=3, freq='h'))

n.add('Bus', ['north', 'south'], carrier='AC', v_nom=110, x=[0.0, 1.0], y=[0.0, 0.0])
n.add('Line', 'north-south', bus0='north', bus1='south', r=0.01, x=0.1, s_nom=100, carrier='AC')
n.add('Generator', 'wind-south', bus='south', carrier='wind', p_nom=30,
      p_max_pu=pd.Series([0.2, 0.5, 0.8], index=n.snapshots))
n.add('Generator', 'gas-north', bus='north', carrier='gas', p_nom=50, marginal_cost=40)
n.add('Load', 'load-south', bus='south', carrier='demand', p_set=[20, 22, 21])

n.consistency_check(strict=['unknown_buses', 'unknown_carriers', 'time_series'])
```

## Static and dynamic table pattern

PyPSA stores data in two tables per component class:

- `n.c.<component>.static`: component names as rows, static attributes as columns.
- `n.c.<component>.dynamic.<attribute>`: snapshots as rows, component names as columns.

For a single component, a 1-D list or `Series` is time-varying:

```python
n.add('Load', 'load', bus='bus', p_set=pd.Series([10, 12, 11], index=n.snapshots))
```

For multiple components, a 1-D list is static per component. Use a `DataFrame` for time-varying data:

```python
names = pd.Index(['load-north', 'load-south'], name='name')
buses = pd.Series(['north', 'south'], index=names)
p_set = pd.DataFrame(
    [[12.0, 8.0], [14.0, 7.0], [13.0, 9.0]],
    index=n.snapshots,
    columns=names,
)
n.add('Load', names, bus=buses, carrier='demand', p_set=p_set)
```

When repairing a shape error, first print the expected labels:

```python
print(n.snapshots)
print(names)
print(p_set.index.equals(n.snapshots), p_set.columns.equals(names))
```

## Component choice table

| Component | Use for | Key modeling attributes | Notes |
|---|---|---|---|
| `Carrier` | Bus carriers and technology labels | `co2_emissions`, `color`, `nice_name`, growth attributes | Add rows for every non-empty `carrier` value used by buses, generators, loads, links, stores, lines, etc. |
| `Bus` | Conservation node for electricity, heat, hydrogen, gas, CO2, material flows | `carrier`, `v_nom`, `x`, `y`, voltage bounds | Every one-port and branch component references buses. Define buses before referenced assets. |
| `Load` | Exogenous demand at a bus | `bus`, `carrier`, `p_set`, `q_set`, `sign` | Positive `p_set` withdraws from the bus. Dynamic demand uses `loads.dynamic.p_set`. |
| `Generator` | External supply or bid-like withdrawal at one bus | `bus`, `carrier`, `p_nom`, `p_nom_extendable`, `marginal_cost`, `capital_cost`, `p_max_pu`, `p_min_pu`, `sign` | Use a `Link` instead when fuel is explicitly represented by another bus. |
| `Line` | Passive AC/DC branch with impedance and Kirchhoff behavior | `bus0`, `bus1`, `r`, `x`, `s_nom`, `s_nom_extendable`, `length`, `type` | Use for passive electrical grids. Use `Link` for controllable point-to-point or cross-carrier flows. |
| `Transformer` | Passive two-winding AC transformer between voltage levels | `bus0`, `bus1`, `type`, `s_nom`, `x`, `r`, tap/phase-shift attrs | Standard transformer type can fill electrical values; voltage bases matter. |
| `Link` | Controllable directed conversion or transfer between two or more buses | `bus0`, `bus1`, `bus2...`, `efficiency`, `efficiency2...`, `p_nom`, `p_min_pu`, `marginal_cost` | Positive `p0` withdraws from `bus0`; `p1`, `p2`, ... inject/withdraw according to efficiencies. |
| `StorageUnit` | Coupled power/energy storage at one bus | `bus`, `p_nom`, `max_hours`, `efficiency_store`, `efficiency_dispatch`, `state_of_charge_initial`, `cyclic_state_of_charge`, `inflow` | Energy capacity is coupled to power capacity by `max_hours`. |
| `Store` | Standalone energy storage on a bus | `bus`, `e_nom`, `e_nom_extendable`, `e_min_pu`, `e_max_pu`, `e_initial`, `e_cyclic`, `standing_loss` | Pair with `Link` components for separate charge/discharge power limits. |
| `GlobalConstraint` | Model-wide constraints used during optimization | `type`, `carrier_attribute`, `sense`, `constant`, `investment_period` | Define as model input here, but route solve behavior to optimization. |
| `LineType`/`TransformerType` | Standard physical parameters | Type-specific impedance/thermal attributes | Referenced by `Line.type` or `Transformer.type`; call `calculate_dependent_values()` before inspecting derived values. |

## Buses and carriers

Carriers play two roles: bus media (`AC`, `DC`, `heat`, `hydrogen`) and technology labels (`wind`, `gas`, `electrolyser`). A robust model defines both.

```python
n.add('Carrier', ['AC', 'hydrogen', 'electrolyser'], color=['#1f77b4', '#17becf', '#9467bd'])
n.add('Bus', 'electricity', carrier='AC')
n.add('Bus', 'hydrogen', carrier='hydrogen')
n.add('Link', 'electrolyser', bus0='electricity', bus1='hydrogen', carrier='electrolyser',
      p_nom_extendable=True, efficiency=0.7, capital_cost=100)
```

If carriers are missing, either add them explicitly or use `n.sanitize()` to add missing carrier rows and colors. Explicit rows are better for reproducible plotting and constraints.

## One-port components

One-port components attach to one bus. Their nominal attribute is usually `p_nom` (`Generator`, `StorageUnit`) or `e_nom` (`Store`).

```python
n.add('Generator', 'solar', bus='electricity', carrier='solar', p_nom_extendable=True,
      capital_cost=500, marginal_cost=0, p_max_pu=solar_profile)
n.add('Load', 'electric-demand', bus='electricity', carrier='demand', p_set=demand_profile)
n.add('Store', 'hydrogen-tank', bus='hydrogen', carrier='hydrogen-storage',
      e_nom_extendable=True, e_cyclic=True, standing_loss=0.0)
```

For extendable assets, include finite cost attributes before optimization. For modular expansion, set a positive module size such as `p_nom_mod`, `s_nom_mod`, or `e_nom_mod`; then `n.c.<component>.modulars` lists affected assets.

## Branch and conversion components

Choose branches by physical behavior:

- Use `Line` for passive electric lines whose flow is determined by impedance and nodal imbalance.
- Use `Transformer` for passive AC voltage conversion.
- Use `Link` for controllable HVDC, net transfer capacities, fuel-to-power conversion, heat pumps, electrolysers, and multi-output/multi-input processes.

Bidirectional lossless link:

```python
n.add('Link', 'hvdc', bus0='north', bus1='south', carrier='HVDC',
      p_nom=100, efficiency=1.0, marginal_cost=0.0, p_min_pu=-1.0)
```

Single input with two outputs, e.g. combined heat and power:

```python
n.add('Link', 'chp', bus0='gas', bus1='electricity', bus2='heat', carrier='CHP',
      efficiency=0.3, efficiency2=0.7, p_nom_extendable=True, capital_cost=80)
```

Input plus additional consumed input, e.g. methanation consumes hydrogen and CO2 and produces methane/heat:

```python
n.add('Link', 'methanation', bus0='hydrogen', bus1='CO2', bus2='methane', bus3='heat',
      efficiency=-0.5, efficiency2=0.8, efficiency3=0.2, p_nom_extendable=True)
```

Negative efficiency on `bus1` means that port withdraws from the corresponding bus when `p0` is positive.

## Storage choice

Use `StorageUnit` when power and energy capacity are tied by `max_hours`:

```python
n.add('StorageUnit', 'battery', bus='electricity', carrier='battery',
      p_nom_extendable=True, max_hours=4, efficiency_store=0.95,
      efficiency_dispatch=0.95, cyclic_state_of_charge=True)
```

Use `Store` plus `Link` components when charge and discharge power ratings should be independent from energy capacity:

```python
n.add('Bus', 'battery-bus', carrier='battery')
n.add('Store', 'battery-energy', bus='battery-bus', carrier='battery', e_nom_extendable=True, e_cyclic=True)
n.add('Link', 'battery-charge', bus0='electricity', bus1='battery-bus', carrier='battery-charge',
      p_nom_extendable=True, efficiency=0.95)
n.add('Link', 'battery-discharge', bus0='battery-bus', bus1='electricity', carrier='battery-discharge',
      p_nom_extendable=True, efficiency=0.95)
```

## Standard line and transformer types

A new network includes standard `line_types` and `transformer_types` unless created with `ignore_standard_types=True`.

```python
n.add('Bus', ['hv', 'lv'], v_nom=[20.0, 0.4], carrier='AC')
n.add('Transformer', 'trafo', bus0='hv', bus1='lv', type='0.25 MVA 20/0.4 kV')
n.calculate_dependent_values()
```

For a line:

```python
n.add('Bus', ['a', 'b'], v_nom=380.0, carrier='AC')
n.add('Line', 'line', bus0='a', bus1='b', length=10.0, type='Al/St 240/40 4-bundle 380.0')
n.calculate_dependent_values()
```

Do not set manual impedance values on the same row unless you accept that standard type calculation can override them.

## Investment periods

Define periods after snapshots. Periods must be strictly increasing integers.

```python
n.set_snapshots(pd.date_range('2024-01-01', periods=24, freq='h'))
n.set_investment_periods([2030, 2040])
n.investment_period_weightings.loc[2030, ['objective', 'years']] = [1.0, 10.0]
n.investment_period_weightings.loc[2040, ['objective', 'years']] = [0.9, 10.0]
```

After this, `n.snapshots` has `(period, timestep)` levels and dynamic tables are indexed by that `MultiIndex`. Use `n.c.generators.get_active_assets(2030)` and `get_activity_mask()` to inspect assets with `build_year`, `lifetime`, and `active` settings.

## Scenarios

`set_scenarios` broadcasts static and dynamic data into stochastic structure. Define scenarios once, and keep topology and mathematical structure identical across scenarios.

```python
n.set_scenarios({'low': 0.4, 'high': 0.6})

# Scenario-specific load after scenario setup: columns are (scenario, name).
n.c.loads.dynamic.p_set = pd.DataFrame(
    {
        ('low', 'load'): [80.0, 90.0, 85.0],
        ('high', 'load'): [100.0, 120.0, 110.0],
    },
    index=n.snapshots,
)
n.c.loads.dynamic.p_set.columns = pd.MultiIndex.from_tuples(
    n.c.loads.dynamic.p_set.columns,
    names=['scenario', 'name'],
)
```

Scenario weights must sum to one. Attributes such as `bus`, `carrier`, `type`, `p_nom_extendable`, module sizes, `committable`, `active`, and standard type tables must not vary across scenarios.

## Safe mutation patterns

Rename components with cross-reference updates:

```python
n.rename_component_names('Bus', old_bus='new_bus')
# Equivalent component-level form:
n.c.buses.rename_component_names(old_bus='new_bus')
```

Remove rows and their time-varying columns:

```python
n.remove('Generator', ['old-wind', 'old-gas'])
```

Overwrite intentionally:

```python
n.add('Bus', 'north', v_nom=220, overwrite=True)
```

Compare before and after complex refactors:

```python
before = n.copy()
# mutate n
assert not before.equals(n)          # mutation changed something
n.equals(before, log_mode='verbose') # inspect differences if needed
```
