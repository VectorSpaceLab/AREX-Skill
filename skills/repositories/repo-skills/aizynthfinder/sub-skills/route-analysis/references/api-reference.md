# Route-Analysis API Reference

This reference covers public APIs useful for inspecting existing search results. It intentionally avoids search setup, model configuration, and custom extension implementation.

## `TreeAnalysis`

Import:

```python
from aizynthfinder.analysis import TreeAnalysis
```

Constructor:

```python
TreeAnalysis(search_tree, scorer=None)
```

Use when a live search tree object is already available. The default scorer is `StateScorer(search_tree.config)`. Passing a list of scorers enables multi-objective analysis.

Verified methods:

| Method | Purpose | Notes |
| --- | --- | --- |
| `best()` | Return the highest-scored route/node. | Raises `ValueError` for multi-objective analysis. |
| `pareto_front()` | Return Pareto-front routes/nodes. | Raises `ValueError` for single-objective analysis. |
| `sort(selection=None)` | Return sorted/selected items and score dictionaries. | Uses Pareto rank sort for multi-objective analyses. |
| `tree_statistics()` | Return search-tree and top-route statistics. | Feeds many CLI output columns. |

Lifecycle:

```python
analysis = TreeAnalysis(search_tree)
routes = RouteCollection.from_analysis(analysis)
stats = analysis.tree_statistics()
```

If the task starts from `output.json.gz`, use the serialized `trees` column and `ReactionTree.from_dict()` instead; table outputs do not reconstruct the original search tree.

## `RouteCollection`

Import:

```python
from aizynthfinder.analysis import RouteCollection
```

Constructor and factory:

```python
RouteCollection(reaction_trees, **kwargs)
RouteCollection.from_analysis(analysis, selection=None)
```

Core attributes:

- `reaction_trees`: ordered `ReactionTree` objects.
- `scores`: current route scores used for ordering.
- `all_scores`: accumulated score dictionaries per route.
- `route_metadata`: `ReactionTree.metadata` for each route.
- `clusters`: cluster sub-collections after `cluster()` succeeds.

Properties and methods:

| API | Purpose | Caveats |
| --- | --- | --- |
| `dicts` / `make_dicts()` | Convert routes to AiZynthFinder dictionaries. | Cached after first creation. |
| `jsons` / `make_jsons()` | Convert routes to JSON strings. | Uses `ReactionTree.to_json()`. |
| `images` / `make_images()` | Convert routes to PIL images. | Invalid/rendering failures yield `None` in `make_images()`. |
| `compute_scores(*scorers)` | Add scores to `all_scores`. | Scorers must accept nodes or reaction trees. |
| `rescore(scorer)` | Reorder routes by a scorer and update scores. | Mutates route order and cached payload order. |
| `dict_with_scores()` | Return dicts with score data at the root. | Shortcut for `dict_with_extra(include_scores=True)`. |
| `dict_with_extra(include_scores=False, include_metadata=False)` | Include scores and/or metadata in route dict roots. | Does not modify original tree objects. |
| `distance_matrix(recreate=False)` | Compute pairwise route distances. | Converts dicts through `rxnutils`; malformed routes can fail. |
| `cluster(n_clusters, max_clusters=5, **kwargs)` | Cluster routes by distance matrix. | Requires optional clustering support; fewer than 3 routes returns an empty array. |
| `combined_reaction_trees(recreate=False)` | Combine route graphs for shared-route visualization/analysis. | Cached unless `recreate=True`. |

From serialized table trees:

```python
from aizynthfinder.analysis import RouteCollection
from aizynthfinder.reactiontree import ReactionTree

reaction_trees = [ReactionTree.from_dict(tree_dict) for tree_dict in target_trees]
routes = RouteCollection(reaction_trees=reaction_trees)
summary_dicts = routes.dict_with_extra(include_metadata=True)
```

## `ReactionTree`

Import:

```python
from aizynthfinder.reactiontree import ReactionTree
```

Construct from serialized output:

```python
tree = ReactionTree.from_dict(tree_dict)
```

Verified methods and properties:

| API | Purpose | Notes |
| --- | --- | --- |
| `child_reactions(reaction)` | Return child reaction nodes under a reaction node. | Input is a reaction node from the same graph. |
| `depth(node)` | Return stored node depth, or `-1` if missing. | Molecule/reaction depths alternate by tree level. |
| `distance_to(other)` | Return `1.0 - simple_route_similarity`. | Depends on `rxnutils` route conversion. |
| `get_subtree(mol)` | Return a subtree rooted at a molecule object. | Raises if molecule is absent. |
| `get_subtree_from_smiles(query)` | Return a subtree rooted at a matching SMILES. | Raises if no molecule SMILES matches. |
| `hash_key()` | Return recursive SHA-224 tree hash. | Useful for route identity/deduplication. |
| `in_stock(node)` | Return stored stock status for a node. | This is serialized state, not a live stock lookup. |
| `is_branched()` | Detect whether route depth differs from reaction count. | Uses leaves and reaction count. |
| `leafs()` | Iterate terminal molecule nodes. | Method name is `leafs`, not `leaves`. |
| `metadata` | Return `created_at_iteration` and `is_solved`. | Can be included with `to_dict(include_metadata=True)`. |
| `molecules()` | Iterate molecule nodes. | Useful before subtree extraction. |
| `parent_molecule(mol)` | Return a molecule node's parent molecule. | Raises for the root molecule. |
| `reactions()` | Iterate reaction nodes. | Reaction metadata often includes template/class fields. |
| `subtrees()` | Iterate molecule-rooted subtrees with children. | Excludes the original root and leaf-only molecules. |
| `to_dict(include_metadata=False)` | Serialize to AiZynthFinder route dictionary. | Main interchange format. |
| `to_json(include_metadata=False)` | Serialize pretty JSON string. | JSON wrapper around `to_dict()`. |
| `to_image(in_stock_colors=None, show_all=True)` | Render a route image. | Requires rendering dependencies and valid molecule/reaction schema. |

Minimal inspection:

```python
tree = ReactionTree.from_dict(tree_dict)
leafs = list(tree.leafs())
reactions = list(tree.reactions())
info = {
    "root": tree.root.smiles,
    "is_solved": tree.is_solved,
    "leaf_count": len(leafs),
    "reaction_count": len(reactions),
    "branched": tree.is_branched(),
}
```

## `ScorerCollection`

Import:

```python
from aizynthfinder.context.scoring import ScorerCollection
```

Constructor:

```python
ScorerCollection(config)
```

Default scorers are loaded automatically:

- `state score`
- `number of reactions`
- `number of pre-cursors`
- `number of pre-cursors in stock`

Useful methods:

| API | Purpose |
| --- | --- |
| `names()` | List loaded scorer names. |
| `objects()` | List scorer objects. |
| `load(scorer, silent=False)` | Add an initialized scorer object. |
| `load_from_config(**scorers_config)` | Load scorer classes by class/module specification. |
| `make_subset(subset_names)` | Create a scorer subset by existing names. |
| `score_vector(item)` | Score an item with selected scorers. |
| `weighted_score(item, weights)` | Weighted sum over selected scorer outputs. |

Custom scorer implementation belongs in `extension-and-development`; this sub-skill only explains how to use loaded scorers for route analysis.

## `cat_aizynth_output`

The installed command concatenates compatible AiZynthFinder output tables:

```bash
cat_aizynth_output --files batch-a.json.gz batch-b.json.gz --output merged.json.gz
```

Required options are `--files` and `--output`; `--trees` optionally writes all trees to a separate file. Use it after confirming individual input files load correctly.
