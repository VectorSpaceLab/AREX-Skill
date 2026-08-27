# Search Algorithms and Custom Search Trees

AiZynthFinder selects the search implementation from `search.algorithm`. The built-in default is `mcts`; other built-in algorithms are selected by fully qualified class path. A custom search tree must be importable and match the constructor/protocol used by `AiZynthFinder.prepare_tree()` and `tree_search()`.

## Selection Rules

- `search.algorithm: mcts` uses the built-in MCTS search tree directly.
- Any other value is dynamically loaded as a class path, then instantiated as `cls(root_smiles=<target>, config=<Configuration>)`.
- Custom search tree classes need `one_iteration() -> bool`; `AiZynthFinder.tree_search()` calls it until limits, first solution, `StopIteration`, or error.
- Route extraction expects the tree to work with `TreeAnalysis`. AND/OR search trees should expose `routes()` or compatible graph/tree state as the built-ins do.
- Serialization is algorithm-specific. Do not assume every search tree supports JSON checkpointing or tree serialization.

## MCTS

Config value:

```yaml
search:
  algorithm: mcts
```

Evidence-level behavior:

- MCTS performs selection, expansion, rollout/promising-child traversal, and backpropagation each iteration.
- Reward scorers come from `search.algorithm_config.search_rewards` and must match loaded scorer collection names.
- If one reward is configured, single-objective mode is used.
- If multiple rewards are configured with no weights, Pareto/multi-objective mode is used.
- If multiple rewards and `search_rewards_weights` are configured, weighted-sum mode is used; the number of weights must equal the number of rewards.
- Useful MCTS-specific settings include `C`, `default_prior`, `use_prior`, `prune_cycles_in_search`, `immediate_instantiation`, and `mcts_grouping`.

Typical multi-objective settings:

```yaml
search:
  break_bonds: [[1, 2]]
  algorithm_config:
    search_rewards: ["state score", "broken bonds"]
```

The `broken bonds` scorer is registered during tree setup only when bond constraints and rewards require it. Invalid bond indices for the target molecule raise setup errors.

## Breadth-First

Config value:

```yaml
search:
  algorithm: aizynthfinder.search.breadth_first.search_tree.SearchTree
```

Evidence-level behavior:

- Breadth-first expands all currently expandable molecule nodes at the active depth per iteration.
- It stops early with `StopIteration` when no new nodes are added.
- It extracts routes from the AND/OR tree by splitting routes against the selected stock.
- It does not use MCTS reward-specific settings such as `C`, prior UCB balancing, or MCTS reward weights in the same way.

Use breadth-first when exhaustive shallow exploration is more important than MCTS value-guided exploration, and keep `max_transforms`, `iteration_limit`, and policy cutoffs conservative.

## DFPN

Config value:

```yaml
search:
  algorithm: aizynthfinder.search.dfpn.search_tree.SearchTree
```

Evidence-level behavior:

- DFPN uses proof-number style frontier exploration over an AND/OR tree.
- The built-in implementation documents two limitations: no filter policy support and no serialization/deserialization support.
- It can find and mask solved subtrees while continuing exploration until no frontier remains.
- It extracts routes through the same split AND/OR route pathway used by other AND/OR algorithms.

Do not promise filter policy behavior or serialized search-tree resume for DFPN unless the user has added and tested those capabilities.

## Retro*

Config value:

```yaml
search:
  algorithm: aizynthfinder.search.retrostar.search_tree.SearchTree
```

Evidence-level behavior:

- Retro* uses an AND/OR tree with molecule costs and reaction costs derived from expansion priors.
- It selects the expandable molecule node with the lowest target value, expands it, filters reactions if a filter policy is selected, and updates costs up the tree.
- If no molecule-cost model is configured, the built-in zero-cost model is used.
- A learned Retro* cost can be configured through `search.algorithm_config.molecule_cost`.

Cost model example:

```yaml
search:
  algorithm: aizynthfinder.search.retrostar.search_tree.SearchTree
  algorithm_config:
    molecule_cost:
      cost: aizynthfinder.search.retrostar.cost.RetroStarCost
      model_path: retrostar_value_model.pickle
      fingerprint_length: 2048
      fingerprint_radius: 2
      dropout_rate: 0.1
```

A custom cost class is dynamically loaded from `molecule_cost.cost` and should implement `calculate(mol) -> float`. Avoid hard-coding local model paths in public guidance; users must provide their own model file.

## Custom Search Tree Contract

A custom search tree should be minimal and compatible with the public `AiZynthFinder` orchestration:

- Constructor accepts `config` and optional `root_smiles` keyword arguments.
- `one_iteration()` performs bounded work and returns true if a solution is currently known.
- Raise `StopIteration` only when search should terminate gracefully.
- Maintain enough state for `TreeAnalysis` or a `routes()` method to extract reaction trees.
- Use `config.expansion_policy`, `config.filter_policy`, `config.stock`, and `config.scorers` instead of creating unrelated global state.
- Avoid network/service startup in the constructor; do heavy setup through explicit user configuration or lazy strategy objects.

## Config Mismatch Checklist

- If `search.algorithm` is not `mcts`, use a fully qualified class path unless a custom wrapper supplies an alias.
- If a non-MCTS algorithm is selected, review whether MCTS-only settings in `algorithm_config` are harmless defaults or misleading leftovers.
- If MCTS multi-objective mode is configured, ensure all reward scorer names are loaded before tree setup.
- If `search_rewards_weights` is non-empty, ensure it has exactly one weight per reward.
- If using disconnection-aware workflows, validate `break_bonds`/`freeze_bonds` are lists of atom-index pairs and exist in the target molecule.
- If using Retro* molecule cost, verify the cost class path and model file before running long searches.
