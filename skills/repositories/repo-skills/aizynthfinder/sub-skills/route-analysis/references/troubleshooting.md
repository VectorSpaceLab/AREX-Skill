# Route-Analysis Troubleshooting

Use this guide for existing AiZynthFinder outputs, route dictionaries, images, scores, and clustering. If the root cause is search execution or data configuration, route to the owning sub-skill after file-level triage.

## Output File Will Not Load

Symptoms:

- `pd.read_json(..., orient="table")` raises a schema/orientation error.
- `pd.read_hdf(..., "table")` raises a missing key or PyTables error.
- The file extension is `.json.gz`, but line-by-line JSON parsing works instead of pandas table loading.

Likely causes and fixes:

- Wrong file type: batch outputs are table-oriented JSON/HDF5, while checkpoints are line-delimited JSON. Try checkpoint parsing only for checkpoint files.
- Wrong HDF5 key: AiZynthFinder table outputs use key `table`.
- Missing optional dependency: HDF5 loading requires pandas HDF support, normally PyTables. Install/enable the dependency in the user’s environment rather than changing the output.
- Partial/interrupted output: compare file size, gzip integrity, and whether the last JSON/checkpoint line is complete.

## Missing Expected Columns

Symptoms:

- `KeyError: 'trees'` when rendering.
- Summary tables lack `target`, `top_score`, or `is_solved`.
- Single-SMILES terminal output is confused with batch dataframe output.

Likely causes and fixes:

- Single-target CLI output writes trees to `trees.json` and prints stats; it does not create the full batch table with `stock_info` and `trees` unless invoked in batch mode.
- `trees` may be missing after concatenation or after exporting a reduced table. Summarize available columns first, then ask for the original full output or `trees.json` if rendering is required.
- A missing `trees` column prevents route rendering, route-distance calculation, clustering, and `ReactionTree.from_dict()` workflows, but does not prevent solved-count and score summaries.

## No Routes or Unsolved Target

Symptoms:

- `number_of_routes` is zero.
- `number_of_solved_routes` is zero.
- `is_solved` is false and tree lists are empty.

Interpretation:

- The output may be valid: AiZynthFinder can finish a search without finding solved routes.
- Summarize `search_time`, `number_of_nodes`, `max_transforms`, `number_of_routes`, and `policy_used_counts` to distinguish “no search progress” from “routes found but unsolved.”
- If the user wants to change search behavior, route to `planning-workflows`.
- If failures point to missing stocks, policy/model loading, or invalid target/config data, route to `configuration-and-data`.

## Invalid Reaction Tree Schema

Symptoms:

- `ReactionTree.from_dict(tree_dict)` fails.
- `to_image()`, `distance_to()`, or `RouteCollection.distance_matrix()` fails on a tree dictionary.
- Tree dictionaries contain unexpected node keys or broken molecule/reaction alternation.

Expected structure:

- Root molecule node: `type: "mol"`, `is_chemical: true`, `smiles`, `in_stock`, `hide`, and optional `children`.
- Reaction node: `type: "reaction"`, `is_reaction: true`, `smiles`, `metadata`, `hide`, and optional `children`.
- Nodes alternate molecule -> reaction -> molecule.
- Missing `children` marks a leaf.

Fixes:

- Validate that `trees` is a list of dictionaries per target, not a JSON string requiring `json.loads()`.
- If trees were exported separately, confirm whether the file is a list of routes or a wrapper object containing a tree list.
- Avoid repairing chemistry semantics by hand; if serialization is corrupted by a search/export bug, route to `planning-workflows` for reproduction.

## Rendering/PIL/Image Failures

Symptoms:

- `ReactionTree.to_image()` raises a rendering error.
- `RouteCollection.images` contains `None` entries.
- Molecule depiction fails for specific SMILES.

Likely causes and fixes:

- Invalid tree schema or invalid molecule SMILES. Confirm `ReactionTree.from_dict()` succeeds before rendering.
- Missing image dependencies or PIL/RDKit rendering support in the active environment. Summarize routes without images if rendering is optional.
- Hidden nodes and stock colors affect display; `to_image(in_stock_colors=None, show_all=True)` defaults to showing all nodes and standard stock coloring.
- `RouteCollection.make_images()` catches `ValueError` and records `None`, so inspect which route failed rather than assuming the whole collection failed.

## Clustering or Distance Failures

Symptoms:

- `RouteCollection.cluster()` raises “Clustering is not supported by this installation.”
- `distance_matrix()` fails during route conversion.
- Clustering returns an empty array.

Likely causes and fixes:

- Optional `route_distances` support is absent. Clustering requires AiZynthFinder extras that include route-distance tooling; explaining this is enough unless the user asks to modify the environment.
- Fewer than 3 routes: clustering intentionally returns an empty array.
- Malformed route trees can fail conversion through `rxnutils`. Validate each tree with `ReactionTree.from_dict()` and a minimal `to_dict()` round trip.
- Custom route-distance backend setup belongs in `extension-and-development`.

## Scoring Problems

Symptoms:

- A scorer name is missing from `ScorerCollection`.
- Rescoring fails because stock/model/reference inputs are missing.
- `best()` or `pareto_front()` raises a `ValueError`.

Likely causes and fixes:

- `ScorerCollection(config)` default-loads only `state score`, `number of reactions`, `number of pre-cursors`, and `number of pre-cursors in stock`.
- Additional scorers may need explicit config, stock data, reference routes, class-rank files, or model files.
- `TreeAnalysis.best()` is single-objective only; `pareto_front()` is multi-objective only.
- Implementing or registering new scorer classes belongs in `extension-and-development`.

## Checkpoint and Partial Output Issues

Symptoms:

- Checkpoint files parse for early lines but fail near the end.
- Duplicate targets appear after resumed or concatenated runs.
- A checkpoint lacks all table columns.

Likely causes and fixes:

- Checkpoints are line JSON with one processed SMILES result per line, not complete pandas tables.
- Interrupted jobs can leave a truncated final line; skip or repair only with explicit user approval and keep the original file unchanged.
- Concatenating checkpoints is different from `cat_aizynth_output` table concatenation. For final reports, prefer the completed batch output table when available.

## Summarizer Script Fallbacks

The bundled summarizer handles missing optional dependencies gracefully:

- JSON table and checkpoint summaries use the Python standard library and do not require pandas.
- If HDF5 support, pandas, or PyTables is missing, it reports the HDF loading error without attempting unsafe repairs.
- If expected columns are absent, it prints the missing column list and summarizes available data.
- It never writes tree summaries unless `--write-tree-summary` is supplied.
