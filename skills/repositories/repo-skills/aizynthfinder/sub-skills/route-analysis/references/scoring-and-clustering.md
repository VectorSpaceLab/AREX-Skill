# Scoring, Rescoring, Distances, and Clustering

AiZynthFinder can score both live search-tree nodes and serialized `ReactionTree` objects. For post-run analysis, prefer working from existing `ReactionTree` dictionaries rather than rerunning searches.

## Built-In Scorer Names

Common built-in scorer names from the scoring implementation:

| Scorer | Reported name | Main use |
| --- | --- | --- |
| `StateScorer` | `state score` | Default tree-search reward combining stock fraction and max transform. |
| `NumberOfReactionsScorer` | `number of reactions` | Count route reaction steps; lower is usually better. |
| `NumberOfPrecursorsScorer` | `number of pre-cursors` | Count terminal precursor molecules; lower is usually better. |
| `NumberOfPrecursorsInStockScorer` | `number of pre-cursors in stock` | Count terminal precursors available in stock. |
| `FractionInStockScorer` | `fraction in stock` | Fraction of route leaves currently in stock. |
| `FractionInSourceStockScorer` | `fraction in <sources>` | Fraction of leaves available from named stock sources. |
| `FractionOfIntermediatesInStockScorer` | `fraction of intermediates in <stock>` | Fraction of non-root intermediate molecules in a named stock. |
| `PriceSumScorer` | `sum of prices` | Sum precursor prices with defaults for missing prices. |
| `StockAvailabilityScorer` | `stock availability` | Product of per-source stock availability scores. |
| `DeltaSyntheticComplexityScorer` | `delta-SC score` | Synthetic-complexity delta using an SCScore model. |
| `AverageTemplateOccurrenceScorer` | `average template occurrence` | Mean template occurrence across route reactions. |
| `MaxTransformScorer` | `max transform` | Maximum transform depth. |
| `ReactionClassMembershipScorer` | `reaction class membership` | Product score for membership in accepted reaction classes. |
| `ReactionClassRankScorer` | `reaction class-rank score` | Class-rank route score requiring class-rank inputs. |
| `RouteCostScorer` | `route cost` | Badowski-style route cost using precursor and reaction costs. |
| `BrokenBondsScorer` | `broken bonds` | Scores whether configured focus bonds break. |
| `RouteSimilarityScorer` | `route similarity` | Route-distance-model score against reference routes. |
| `DeepSetScorer` | `expert-augmented score` | Expert-augmented model score requiring model files. |
| `CombinedScorer` | Combined scorer names or custom short name | Weighted combination of existing scorers. |

Only the first four are default-loaded by `ScorerCollection(config)`. Other scorers may require config entries, stock data, model files, reference routes, reaction-class files, or optional route-distance dependencies.

## Rescoring Existing Routes

A `RouteCollection` can compute additional scores or reorder routes with a loaded scorer.

```python
from aizynthfinder.analysis import RouteCollection
from aizynthfinder.reactiontree import ReactionTree

reaction_trees = [ReactionTree.from_dict(tree_dict) for tree_dict in target_trees]
routes = RouteCollection(reaction_trees=reaction_trees)

# scorer must be an initialized AiZynthFinder Scorer object
routes.compute_scores(scorer)
routes.rescore(scorer)
scored_dicts = routes.dict_with_scores()
```

Caveats:

- Scorers that need a live `Configuration` must be initialized with one; table outputs alone do not reconstruct config, stock, or model state.
- Some scorers score live MCTS nodes more directly, but most can score `ReactionTree` objects.
- `rescore()` mutates route order and reorders cached dict/image/json payloads if those caches exist.
- `compute_scores()` updates `all_scores` without changing order.
- `dict_with_extra(include_scores=True, include_metadata=True)` is the safest export if downstream consumers need both route metadata and score annotations.

## Multi-Objective Analysis

`TreeAnalysis(search_tree, scorer=[...])` enables multi-objective behavior on a live search tree:

- `pareto_front()` returns Pareto-front solutions and raises for single-objective analysis.
- `best()` returns the single highest-scoring solution and raises for multi-objective analysis.
- `sort()` uses Pareto ranks when multiple scorers are present.

Use multi-objective `TreeAnalysis` only when the search tree object is still available. Serialized output files normally contain route dictionaries and score columns, not enough state to rebuild all search-tree internals.

## Distance Matrices

`ReactionTree.distance_to(other)` and `RouteCollection.distance_matrix(recreate=False)` convert AiZynthFinder route dictionaries through `rxnutils` route readers and use route similarity:

```python
distance = tree_a.distance_to(tree_b)
matrix = routes.distance_matrix()
```

Notes:

- Distance is `1.0 - simple_route_similarity`.
- A malformed tree dictionary can fail during `rxnutils` conversion.
- `RouteCollection.distance_matrix()` caches the result unless `recreate=True`.
- Empty, unsolved, or schema-incomplete route lists should be validated before computing distances.

## Clustering

`RouteCollection.cluster(n_clusters, max_clusters=5, **kwargs)` clusters routes based on the collection distance matrix.

Behavior and requirements:

- Requires optional clustering support from the `route_distances` package. If unavailable, AiZynthFinder raises `ValueError` explaining that clustering is not supported and extras are needed.
- If the collection has fewer than 3 routes, clustering returns an empty NumPy array and does not create meaningful clusters.
- If the distance matrix cannot be computed, clustering catches `ValueError` and returns an empty array.
- `n_clusters < 2` asks the clustering helper to optimize the cluster count up to `max_clusters`.
- Successful clustering populates `routes.clusters` with `RouteCollection` sub-collections.

Safe pattern:

```python
try:
    labels = routes.cluster(n_clusters=2)
except ValueError as err:
    message = str(err)
    # Usually optional clustering support is missing.
else:
    if len(labels) == 0:
        # Too few routes or invalid tree data for distance calculation.
        pass
```

## Combined Reaction Trees

`RouteCollection.combined_reaction_trees(recreate=False)` merges all route graphs into a combined representation useful for overlap analysis or visualization. It uses cached state unless `recreate=True`.

Use it after validating that route dictionaries parse into `ReactionTree` objects. Combined-tree issues are usually upstream schema issues, not evidence that search must be rerun.

## Interpreting Output Scores

The `top_score` and `top_scores` columns usually reflect the default MCTS reward/state score unless a different scoring setup was used. In table summaries:

- `top_score` is scalar and suitable for numeric summaries.
- `top_scores` is often a comma-separated string for extracted routes.
- `number_of_solved_routes` can be more informative than `is_solved` when only lower-ranked routes are solved.
- A target with `is_solved=False` can still have route trees; inspect `number_of_routes`, `number_of_solved_routes`, and the `trees` list before declaring no output.
