# Customization Interfaces

AiZynthFinder extension points are regular Python objects loaded either by explicit CLI module import, by a configuration class path, or by direct Python API calls. The future agent should make the extension importable first, then validate the expected method/function contract, then place the import path in YAML or pass the object to the API.

## Dynamic Loading Rules

- Fully qualified specs look like `package.module.ClassName`; AiZynthFinder splits on the final dot, imports `package.module`, then fetches `ClassName`.
- Bare names such as `TemplateBasedExpansionStrategy` only work where the loader supplies a built-in default module. Custom classes should use fully qualified paths.
- Import failures are reported as module-load errors; spelling the module correctly but misspelling the class produces a missing-class error.
- A custom module must be on Python import path in the environment that runs the CLI, notebook, or test. Prefer package installation or an explicit working-directory/module-path setup controlled by the user.

## CLI Hook Modules

The CLI supports lightweight hook modules by importing module names passed to the CLI. Use `planning-workflows` for full CLI command construction; use this section to implement and validate hook modules.

- Pre-processing modules must define `pre_processing(finder, index)`.
- Post-processing modules must define `post_processing(finder)`.
- A pre-processing hook is called before tree setup: for single SMILES, `index` is `-1`; for a file, it is the zero-based index within the remaining input after checkpoint skipping.
- A post-processing hook is called after route building and statistics extraction; it should return a dictionary that can be merged into the output stats.
- AiZynthFinder ignores hook modules that cannot be imported or lack the expected function, so use the checker script to fail loudly before running a long job.

Good hook behavior:

- Do not mutate global state unless the user explicitly needs it.
- Keep file outputs deterministic and user-selected.
- Raise clear exceptions during validation rather than silently returning incomplete data.
- For pre-processing, mutate `finder` configuration or target-dependent settings before `finder.prepare_tree()`; avoid running a search inside the hook.
- For post-processing, read `finder.routes`, `finder.analysis`, `finder.search_stats`, or `finder.extract_statistics()` state; avoid recomputing the search.

## Custom Stocks

There are two stock-related extension surfaces.

### Stock Query Objects

A stock query class should inherit `aizynthfinder.context.stock.queries.StockQueryMixin` and implement at least `__contains__(self, mol) -> bool`, where `mol` is an AiZynthFinder `Molecule`-like object. Optional methods improve reporting or stop criteria:

- `__len__(self)` for size reporting.
- `price(self, mol)` if stock stop criteria or route price scores need prices.
- `amount(self, mol)` if amount stop criteria should be enforced.
- `availability_string(self, mol)` for source labels in output statistics.
- `cached_search(self, mol)` and `clear_cache()` for expensive backends.

Use paths under YAML `stock` when configuring built-in file stocks. Use a custom `type: package.module.ClassName` when loading a custom query class from YAML; constructor keyword arguments are taken from the remaining YAML keys. Direct API users can instantiate the object and call `finder.stock.load(obj, "key")`, then select the key.

### CLI `custom_stock` Module

The CLI attempts to import a module named `custom_stock`. If that module exposes a module-level variable named `stock`, the object is loaded with key `custom_stock` and selected along with requested stocks. This is convenient for local one-off stock logic but less explicit than a YAML class path.

## Custom SMILES Extractors for Stock Building

For `smiles2stock --source module`, the first item after `--files` is an importable module name and the remaining file arguments are passed into a function named `extract_smiles`.

- The function may accept a filename and yield/return SMILES strings from that file.
- A zero-argument extractor returning an iterable is also used in tests, but a filename-accepting generator is the more practical pattern for real files.
- The checker script can verify that `extract_smiles` exists and whether it accepts zero or one positional argument; it does not parse user files.

## Custom Scorers

Custom route/node scorers should inherit `aizynthfinder.context.scoring.scorers_base.Scorer` or the re-exported `Scorer` from the scoring package and implement:

- `_score_node(self, node) -> float`
- `_score_reaction_tree(self, tree) -> float`
- `__repr__(self) -> str` or a meaningful `scorer_name` so the collection key is stable.

YAML `scorer` entries use class paths as keys and pass the nested mapping to `cls(config, **kwargs)`. A scorer instance can also be loaded with `finder.scorers.load(scorer)`. Search-time MCTS rewards reference scorers by their collection names, while post-processing route ranking can use configured route scorers; use `route-analysis` for interpreting resulting scores.

## Custom Expansion Policies

Expansion strategies should inherit `aizynthfinder.context.policy.ExpansionStrategy` and implement:

- `__init__(self, key, config, **kwargs)` calling the base initializer.
- `get_actions(self, molecules, cache_molecules=None) -> (actions, priors)`.
- `reset_cache(self)` when the strategy caches predictions.

The base class supports `_required_kwargs`; missing required keys raise a policy error during construction. `ExpansionPolicy.load_from_config` accepts either a short two-item template-based form or a mapping with `type: package.module.ClassName` plus strategy-specific constructor kwargs. Custom strategies should return AiZynthFinder `RetroReaction` objects such as template-based or SMILES-based reactions, with priors aligned to the action list.

`MultiExpansionStrategy` combines selected expansion strategies by key. Important settings:

- `expansion_strategies`: selected policy keys to combine.
- `additive_expansion`: when true, concatenate actions from all strategies; when false, stop after the first strategy that returns actions.
- `expansion_strategy_weights`: optional weights; if present, they must sum to one.
- `cutoff_number`: optional pruning after combining.

## Custom Filter Policies

Filter strategies follow the same dynamic loading pattern under YAML `filter`. A custom filter should inherit the filter strategy base class and reject reactions by raising the expected rejection exception from its call/apply path. If no filter policy is selected, filter application is skipped.

## Optional Plugin Strategies

The bundled plugin-style expansion strategies are optional and extra dependent. They should be treated as examples or user-installed modules, not as always-available core functionality.

### Chemformer REST

Chemformer-based strategies call an external REST service and require a `url` setting. They retry requests, but failed connections or non-OK responses can leave the cache empty and produce no actions. Service startup, model loading, hostnames, ports, and GPU paths are user-specific and should not be baked into a reusable skill.

Common YAML shape:

```yaml
expansion:
  chemformer:
    type: expansion_strategies.ChemformerBasedExpansionStrategy
    url: http://host:port/chemformer-api/predict
search:
  algorithm_config:
    immediate_instantiation: [chemformer]
  time_limit: 300
```

For disconnection-aware Chemformer, `search.break_bonds` must be non-empty and valid for the target molecule. It can be combined with template-based expansion through `MultiExpansionStrategy`.

### ModelZoo

ModelZoo expansion requires the `ssbenchmark`/ModelZoo stack to be installed and an external model module path. The strategy raises an import error if the optional package is absent and requires `module_path` in config. Local model checkpoint/vocabulary paths, GPU mode, and external model repositories are user-managed.

## Config Placement Summary

Use `configuration-and-data` for full YAML authoring, but for extension placement remember:

- `stock.<key>.type`: stock query class path.
- `scorer.<class-path>`: scorer class path key, with kwargs as value.
- `expansion.<key>.type`: expansion strategy class path.
- `filter.<key>.type`: filter strategy class path.
- `search.algorithm`: `mcts` or a search tree class path.
- `search.algorithm_config.molecule_cost.cost`: Retro* molecule-cost class path.

## Validation Workflow

1. Run `python scripts/check_custom_aizynth_module.py --mode <mode> --target <module-or-class>`.
2. For config-loaded classes, use the same fully qualified string that will appear in YAML.
3. For CLI hook modules, validate the module with `--function pre_processing` or `--function post_processing` when the module has both or when absence must be explained.
4. Instantiate only when safe; pure import/signature checks are preferred for services, remote models, or GPU-backed extensions.
5. Add focused tests around the interface contract before broad planning runs.
