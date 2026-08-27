# Planning API Reference

This reference records the public planning APIs verified for AiZynthFinder 4.4.1. It focuses on execution lifecycle and one-step expansion. Configuration schema, output dataframe interpretation, custom plugins, and custom hook implementation are routed to sibling sub-skills.

## `AiZynthFinder`

Import:

```python
from aizynthfinder.aizynthfinder import AiZynthFinder
```

Constructor:

```python
AiZynthFinder(configfile=None, configdict=None)
```

Constructor notes:

- `configfile` has priority over `configdict`.
- `configfile` is a path to a YAML configuration file.
- `configdict` is a Python dictionary source for configuration.
- With neither, a default `Configuration()` is created; load/select stocks and policies before planning.

Important attributes:

- `config`: loaded configuration object.
- `expansion_policy`: policy collection from the config.
- `filter_policy`: filter policy collection from the config.
- `stock`: stock collection from the config.
- `scorers`: loaded scoring collection.
- `tree`: current search tree or `None`.
- `routes`: route collection built by `build_routes()`.
- `analysis`: tree-analysis object built by `build_routes()`.
- `search_stats`: statistics for the latest search.

Target properties:

```python
finder.target_smiles = "CCO"
smiles = finder.target_smiles
finder.target_mol = molecule
molecule = finder.target_mol
```

Target notes:

- Setting `target_smiles` constructs a molecule from the SMILES string.
- Setting either target clears `finder.tree`, so a new search tree is prepared for the new target.
- `target_smiles` returns an empty string when no target is set.

Methods:

```python
finder.prepare_tree() -> None
finder.tree_search(show_progress=False) -> float
finder.build_routes(selection=None, scorer=None) -> None
finder.extract_statistics() -> dict
finder.stock_info() -> dict
```

Lifecycle:

1. Instantiate with `configfile` or `configdict`.
2. Select stocks and policies if defaults are not desired.
3. Set `target_smiles` or `target_mol`.
4. Call `prepare_tree()` explicitly, or let `tree_search()` call it when no tree exists.
5. Call `tree_search(show_progress=False)`.
6. Call `build_routes(selection=None, scorer=None)`.
7. Call `extract_statistics()`, inspect `routes`, and call `stock_info()` as needed.

Method notes:

- `prepare_tree()` raises `ValueError("No target molecule set")` when no target exists.
- `prepare_tree()` raises `ValueError("Target molecule unsanitizable")` when the target cannot be sanitized.
- Focused-bond settings can raise `ValueError("Bonds in 'freeze_bond' must exist in target molecule")` or `ValueError("Bonds in 'break_bonds' must exist in target molecule")`.
- `tree_search()` loops until time limit, iteration limit, no more expansions, or `return_first` solved-route early exit.
- `tree_search(show_progress=True)` uses a progress bar; keep it `False` for log-friendly automation.
- `build_routes()` must run before meaningful `extract_statistics()` route statistics or `stock_info()`.
- `build_routes()` raises `ValueError("Search tree not initialized")` if no search tree exists.
- `extract_statistics()` returns `{}` when no analysis has been built.
- `stock_info()` returns `{}` when no analysis has been built.

Policy and stock selection:

```python
finder.stock.select(["zinc"])
finder.expansion_policy.select(["uspto"])
finder.filter_policy.select(["uspto_filter"])
finder.filter_policy.select_all()
finder.filter_policy.deselect()
```

Selection notes:

- Key names must match the config-loaded collection keys.
- Multiple expansion policies can be selected when the config defines strategies that support it.
- If a filter policy is optional for the task, either select a known filter key or deselect filters intentionally.

Route building options:

```python
finder.build_routes()
finder.build_routes(selection=selection_args)
finder.build_routes(scorer="state score")
finder.build_routes(scorer=["state score", "broken bonds"])
```

Route notes:

- With no `selection`, route selection is built from config post-processing settings: `min_routes`, `max_routes`, and `all_routes`.
- With no `scorer`, scorers come from `post_processing.route_scorers`; if absent, search rewards are reused; if those are absent, `"state score"` is used.
- If `"broken bonds"` is requested, the broken-bonds scorer is loaded from the config.
- Multi-objective and custom scoring details belong to `../route-analysis/SKILL.md` or `../extension-and-development/SKILL.md`.

## `AiZynthExpander`

Import:

```python
from aizynthfinder.aizynthfinder import AiZynthExpander
```

Constructor:

```python
AiZynthExpander(configfile=None, configdict=None)
```

Important attributes:

- `config`: loaded configuration object.
- `expansion_policy`: policy collection from the config.
- `filter_policy`: filter policy collection from the config.
- `stats`: expansion counters, including `"non-applicable"` after `do_expansion()`.

Method:

```python
expander.do_expansion(smiles: str, return_n: int = 5, filter_func=None) -> list[tuple[FixedRetroReaction, ...]]
```

Usage:

```python
expander = AiZynthExpander(configfile="config.yml")
expander.expansion_policy.select(["uspto"])
expander.filter_policy.select(["uspto_filter"])
reactions = expander.do_expansion("CCO", return_n=5)
```

Return notes:

- The return value is a list of tuples of `FixedRetroReaction` objects.
- Each tuple groups reactions producing the same reactant set.
- `return_n` limits unique reactant groups, not necessarily the total number of reaction objects.
- If a generated action has no reactants, it is counted in `expander.stats["non-applicable"]` and skipped.
- `filter_func(reaction)` can reject a reaction by returning `False`.
- If a selected filter policy exposes `feasibility`, the first such filter adds a numeric `feasibility` entry to reaction metadata.
- Each retained unique group gets `expansion_rank` metadata based on insertion order.

Reactant extraction example:

```python
reactants_smiles = []
for reaction_tuple in reactions:
    first_reaction = reaction_tuple[0]
    reactants_smiles.append([mol.smiles for mol in first_reaction.reactants[0]])
```

Metadata dataframe example:

```python
metadata = []
for reaction_tuple in reactions:
    for reaction in reaction_tuple:
        metadata.append(reaction.metadata)
```

## `AiZynthApp`

Import:

```python
from aizynthfinder.interfaces import AiZynthApp
```

Constructor:

```python
AiZynthApp(configfile: str, setup: bool = True)
```

Notes:

- Intended for Jupyter notebooks with IPython display and ipywidgets support.
- The app creates `app.finder`, an `AiZynthFinder` instance.
- With `setup=True`, widgets are displayed immediately.
- With `setup=False`, no widgets are displayed until `setup()` is called.
- The GUI exposes stock, policy, filter, search-limit, reward, and route display controls.
- GUI execution forces the search algorithm to `mcts` if another algorithm is configured.
