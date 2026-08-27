# AiZynthFinder Configuration Reference

AiZynthFinder loads YAML into a `Configuration` object. Missing settings use defaults. The main sections for data setup are `search`, `post_processing`, `expansion`, `filter`, `stock`, and optional `scorer`.

## Minimal Config

A minimal useful config needs at least one expansion policy and one stock. A filter is optional.

```yaml
expansion:
  full:
    - uspto_expansion.onnx
    - uspto_templates.csv.gz
stock:
  zinc: zinc_stock.hdf5
```

The `expansion.full` value is short-form expansion syntax: `[model, template]`. The `stock.zinc` value is short-form stock syntax: the path is treated as an in-memory InChI-key stock unless it ends in `.bloom`, which is treated as a molbloom filter stock.

## Environment Variables

YAML values may contain `${VAR}` placeholders. At config load time, AiZynthFinder replaces every `${VAR}` with `os.environ[VAR]` before YAML parsing. If a placeholder is not defined, loading raises `ValueError` and stops.

```yaml
search:
  iteration_limit: ${ITERATION_LIMIT}
  time_limit: ${TIME_LIMIT}
  algorithm_config:
    C: ${MCTS_C}
expansion:
  uspto:
    - ${AIZYNTH_POLICY_MODEL}
    - ${AIZYNTH_TEMPLATE_FILE}
stock:
  zinc: ${AIZYNTH_STOCK_FILE}
```

Because substitution happens before YAML parsing, numeric environment values such as `300` are parsed as numbers when unquoted, while quoted placeholders remain strings. Always check that required env vars exist before handing the config to `aizynthcli` or `aizynthapp`.

## Search Section

`search` is optional. Defaults are safe starter values for MCTS:

| Setting | Default | Notes |
| --- | --- | --- |
| `algorithm` | `mcts` | Can also be a custom import path; custom classes are extension work. |
| `max_transforms` | `6` | Maximum tree depth. |
| `iteration_limit` | `100` | Maximum search iterations. |
| `time_limit` | `120` | Maximum search seconds. |
| `return_first` | `false` | Stop when first solution is found. |
| `exclude_target_from_stock` | `true` | Forces target to be broken down even if in stock. |
| `break_bonds` | `[]` | List of atom-index pairs that must/should break. |
| `freeze_bonds` | `[]` | List of atom-index pairs that should remain intact. |
| `break_bonds_operator` | `and` | `and` means all listed break bonds; `or` means any listed break bond. |

`break_bonds` and `freeze_bonds` must be lists of 2-item lists. Examples: `[[1, 2], [3, 4]]` is valid; `[1, 2]`, `[[1, 2, 3]]`, and scalar values are invalid.

## Algorithm Config

`search.algorithm_config` must be a mapping. It updates MCTS defaults rather than replacing the whole default object.

| Key | Default | Notes |
| --- | --- | --- |
| `C` | `1.4` | Exploration/exploitation balance. |
| `default_prior` | `0.5` | Prior used if policy priors are not used. |
| `use_prior` | `true` | Uses policy priors when true. |
| `prune_cycles_in_search` | `true` | Avoids recreating molecules already seen in a path. |
| `search_rewards` | `[state score]` | Scorer names for MCTS rewards. |
| `search_rewards_weights` | `[]` | Weights for combined reward scoring. |
| `immediate_instantiation` | `[]` | Expansion policy names to instantiate immediately. |
| `mcts_grouping` | `null` | `partial` or `full` groups duplicate expansion states. |

Example:

```yaml
search:
  algorithm: mcts
  algorithm_config:
    C: 1.9
    default_prior: 0.9
    use_prior: false
    prune_cycles_in_search: true
    search_rewards:
      - state score
  max_transforms: 6
  iteration_limit: 100
  time_limit: 120
  return_first: false
  exclude_target_from_stock: true
  break_bonds: [[1, 2], [2, 3]]
  freeze_bonds: [[3, 4]]
  break_bonds_operator: or
```

## Post Processing Section

`post_processing` is optional and controls route extraction after search.

| Setting | Default | Notes |
| --- | --- | --- |
| `min_routes` | `5` | Minimum routes to extract when `all_routes` is false. |
| `max_routes` | `25` | Maximum routes to extract when `all_routes` is false. |
| `all_routes` | `false` | Extract all solved routes. |
| `route_distance_model` | `null` | Optional quick route-distance model path. |
| `route_scorers` | `[]` | Route scorers used after search. |
| `scorer_weights` | `null` | Optional weights for route scorers. |

Route-distance workflows can require optional route-distance dependencies and are primarily output-analysis concerns after a run.

## Expansion Policies

An expansion policy points to a trained model checkpoint and a template table. At least one expansion policy must be loaded and selected before retrosynthesis can generate actions.

Short form:

```yaml
expansion:
  uspto:
    - uspto_model.onnx
    - uspto_templates.csv.gz
```

Full form:

```yaml
expansion:
  uspto:
    type: template-based
    model: uspto_model.onnx
    template: uspto_templates.csv.gz
    template_column: retro_template
    cutoff_cumulative: 0.995
    cutoff_number: 50
    use_rdchiral: true
    use_remote_models: false
    rescale_prior: false
    mask: template_mask.npz
```

Expansion defaults for `template-based` include `template_column: retro_template`, `cutoff_cumulative: 0.995`, `cutoff_number: 50`, `use_rdchiral: true`, `use_remote_models: false`, and `rescale_prior: false`. `mask` is optional and should be a NumPy `.npz` file containing a Boolean vector with the same length as the template table.

Template tables may be HDF5 with key `table` or TSV-like `.csv`/`.csv.gz` read with tab separators and index column 0. The template column defaults to `retro_template`, although some template CSV fixtures use `template`; match the column setting to the file.

## Multi Expansion

AiZynthFinder includes a multi-expansion strategy that combines existing expansion strategies. This is a full-form expansion policy and requires the referenced strategy keys to already exist in `expansion`.

```yaml
expansion:
  uspto:
    - uspto_model.onnx
    - uspto_templates.csv.gz
  ringbreaker:
    - ringbreaker_model.onnx
    - ringbreaker_templates.csv.gz
  combined:
    type: MultiExpansionStrategy
    expansion_strategies: [uspto, ringbreaker]
    additive_expansion: true
    expansion_strategy_weights: [0.7, 0.3]
    cutoff_number: 50
```

If `expansion_strategy_weights` is set, weights must sum to 1. If `additive_expansion` is false or omitted, the strategy can stop after the first non-empty strategy.

## Filter Policies

Filters are optional feasibility checks on proposed reactions. A filter policy must be selected before it is applied; planning CLIs commonly select all loaded filters.

Short form:

```yaml
filter:
  uspto: uspto_filter_model.onnx
```

Full form:

```yaml
filter:
  uspto:
    type: quick-filter
    model: uspto_filter_model.onnx
    exclude_from_policy: [ringbreaker]
    filter_cutoff: 0.05
    use_remote_models: false
```

`quick-filter`, `feasibility`, and `quick_keras_filter` all resolve to the quick Keras filter class. Built-in non-model filter aliases include `reactants_count` and `frozen_substructure`; `BondFilter` uses `search.freeze_bonds` when configured as a filter class.

## Stock Section

Stocks define what precursors are purchasable or otherwise terminal. The stock section can contain named stocks plus optional `stop_criteria`.

Short form:

```yaml
stock:
  zinc: zinc_stock.hdf5
```

Full in-memory InChI-key stock:

```yaml
stock:
  buyables:
    type: inchiset
    path: zinc_stock.hdf5
    inchi_key_col: inchi_key
    price_col: price
```

MongoDB stock:

```yaml
stock:
  commercial_db:
    type: mongodb
    host: db-hostname
    database: stock_db
    collection: molecules
```

Molbloom stock:

```yaml
stock:
  bloom_stock:
    type: bloom
    path: stock.bloom
    smiles_based: false
```

Stock aliases include `inchiset`, `mongodb`, and `bloom`. If a short-form stock path ends in `.bloom`, AiZynthFinder chooses a molbloom query; otherwise it chooses an in-memory InChI-key query.

## Stock Stop Criteria

Stop criteria can limit when a stock hit counts as acceptable. They only fully work for stock query classes that can provide the needed price or amount metadata.

```yaml
stock:
  zinc: zinc_stock.hdf5
  stop_criteria:
    price: 10
    amount: 100
    weight: 250
    counts:
      C: 10
      O: 4
```

`counts` and legacy `size` both map to element-count thresholds. Missing price or amount information does not necessarily fail config loading, but the criteria may be ineffective for stock classes that cannot compute those properties.

## Validation Checklist

Before executing a search:

1. Resolve every `${VAR}` placeholder or ask the user to set it.
2. Confirm the config parses as a YAML mapping.
3. Confirm `search.algorithm_config` is a mapping when present.
4. Confirm `break_bonds` and `freeze_bonds` are lists of 2-item lists.
5. Confirm each expansion short form has exactly `[model, template]`.
6. Confirm each full-form expansion has `model` and `template` unless it is a custom strategy with different requirements.
7. Confirm each filter short form is a model path and each full quick-filter has `model`.
8. Confirm each stock full form has `path` for file-backed stock types or Mongo connection settings for `mongodb`.
9. Warn on missing local model, template, mask, stock, or route-distance files.
10. Route to planning-workflows only after the static config is structurally clean.
