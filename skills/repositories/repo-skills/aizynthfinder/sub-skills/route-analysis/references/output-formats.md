# AiZynthFinder Output Formats

AiZynthFinder batch output is designed for post-run analysis. Do not rerun a search just to inspect, summarize, or render existing routes.

## Batch Output Tables

When `aizynthcli` receives multiple SMILES, it writes a JSON or HDF5 file that pandas can read as a dataframe. The default filename is `output.json.gz`.

Use these loading recipes:

```python
import pandas as pd

json_data = pd.read_json("output.json.gz", orient="table")
hdf_data = pd.read_hdf("output.hdf5", "table")
```

Expected table columns from the CLI output specification:

| Column | Meaning |
| --- | --- |
| `target` | Target SMILES. |
| `search_time` | Total search time in seconds. |
| `first_solution_time` | Time until the first solution was found. |
| `first_solution_iteration` | Iteration count when the first solution appeared. |
| `number_of_nodes` | Number of nodes in the search tree. |
| `max_transforms` | Maximum route transformation depth in the search tree. |
| `max_children` | Maximum child count for a search node. |
| `number_of_routes` | Number of routes in the search tree. |
| `number_of_solved_routes` | Number of solved routes in the search tree. |
| `top_score` | Score of the top-ranked route, normally the MCTS reward/state score. |
| `is_solved` | Whether the top-ranked route is solved. |
| `number_of_steps` | Number of reactions in the top-ranked route. |
| `number_of_precursors` | Number of starting materials. |
| `number_of_precursors_in_stock` | Count of starting materials in stock. |
| `precursors_in_stock` | Comma-separated SMILES for stocked starting materials. |
| `precursors_not_in_stock` | Comma-separated SMILES for unstocked starting materials. |
| `precursors_availability` | Semicolon-separated stock availability details. |
| `policy_used_counts` | Per-expansion-policy usage counts. |
| `profiling` | Profiling information such as expansion model calls and reactant generation. |
| `stock_info` | Stock availability for starting materials across extracted routes. |
| `top_scores` | Comma-separated scores of extracted routes. |
| `trees` | List of extracted routes as dictionaries. |

`stock_info` and `trees` are table-only fields and are not printed in single-SMILES terminal summaries.

## Single-Target Tree JSON

When the CLI receives a single SMILES, route statistics are printed to the terminal and top-ranked routes are written to a JSON file, defaulting to `trees.json`.

A tree dictionary follows the `ReactionTree.to_dict()` structure:

- The root is a molecule node with `type: "mol"`, `is_chemical: true`, `smiles`, `hide`, `in_stock`, and optional `children`.
- Reaction nodes have `type: "reaction"`, `is_reaction: true`, `smiles`, `hide`, `metadata`, and optional `children`.
- Molecule and reaction nodes alternate in a directed tree.
- Missing `children` means the node is a leaf.
- `to_dict(include_metadata=True)` can include `route_metadata` at the root with `created_at_iteration` and `is_solved`.

Render or inspect a serialized route with:

```python
from aizynthfinder.reactiontree import ReactionTree

tree = ReactionTree.from_dict(tree_dict)
image = tree.to_image()
route_json = tree.to_json(include_metadata=True)
leaf_smiles = [mol.smiles for mol in tree.leafs()]
```

## Extracting Trees From Batch Tables

The `trees` column contains one list of tree dictionaries per target. Check for missing values and empty lists before rendering.

```python
from aizynthfinder.reactiontree import ReactionTree

all_trees = data["trees"].values
for target_index, target_trees in enumerate(all_trees):
    if not target_trees:
        continue
    for route_index, tree_dict in enumerate(target_trees):
        image = ReactionTree.from_dict(tree_dict).to_image()
        image.save(f"target{target_index:03d}-route{route_index:03d}.png")
```

If the `trees` column is absent, the output can still summarize search statistics and solved status, but it cannot render routes or build `ReactionTree` objects without another tree source.

## Checkpoint Line JSON

When a checkpoint path is supplied to the CLI, `checkpoint.json.gz` contains one processed SMILES result per line. Treat it as line-delimited JSON, not a pandas table. A checkpoint may be partial if a batch search was interrupted.

Safe handling pattern:

```python
import gzip
import json

with gzip.open("checkpoint.json.gz", "rt", encoding="utf-8") as handle:
    for line_number, line in enumerate(handle, start=1):
        if not line.strip():
            continue
        record = json.loads(line)
        target = record.get("target") or record.get("smiles")
```

Malformed lines usually indicate an interrupted write, accidental concatenation, or a file that is not actually an AiZynthFinder checkpoint.

## Concatenating Outputs

AiZynthFinder includes a `cat_aizynth_output` command for concatenating compatible output files. Its CLI requires:

```bash
cat_aizynth_output --files output-1.json.gz output-2.json.gz --output merged.json.gz
```

Optional tree extraction:

```bash
cat_aizynth_output --files output-1.json.gz output-2.json.gz --output merged.json.gz --trees merged-trees.json
```

The command delegates to AiZynthFinder file utilities and expects compatible JSON/HDF5 table-style outputs. If concatenation fails, first verify each input loads independently with pandas and has compatible table columns.

## Safe Summary Script

The bundled `scripts/summarize_aizynth_output.py` reads JSON table, HDF5 table, and checkpoint line JSON outputs. It prints row count, solved count, `top_score` summary, missing expected columns, sample targets, and tree availability. It writes tree summaries only when `--write-tree-summary` is explicitly provided.
