# Planning Workflow Recipes

These recipes cover AiZynthFinder execution. They assume `aizynthfinder` is installed and a usable configuration file or dictionary already points to stock, expansion-policy, and optional filter assets. For creating or validating those assets, use `../configuration-and-data/SKILL.md`.

## CLI: Single Target

Use a literal SMILES when the task is one target and terminal statistics plus a route-tree JSON are enough.

```bash
aizynthcli --config config.yml --smiles "CCO" --output trees.json
```

Behavior:

- If `--smiles` does not name an existing file, AiZynthFinder treats it as a literal SMILES.
- If the literal is not a valid RDKit SMILES, the CLI logs that it is neither a file nor a valid SMILES and exits without starting planning.
- The default single-target route output is `trees.json` when `--output` is omitted.
- Search statistics are written to the logger/terminal. Route-tree interpretation belongs to `../route-analysis/SKILL.md`.
- `--nproc` is invalid for a literal single SMILES; multiprocessing requires `--smiles` to be a file path.

## CLI: Batch File

Use a text file with one SMILES per line for batch planning.

```bash
aizynthcli --config config.yml --smiles targets.smi --output output.json.gz
```

Behavior:

- If `--smiles` names an existing file, every line is stripped and processed as one target.
- The default batch output is `output.json.gz` when `--output` is omitted.
- Batch output is a pandas-compatible JSON or HDF5 file depending on the output suffix.
- Per-target route trees and `stock_info()` are included in the output rows.
- Targets that fail `prepare_tree()` are skipped after a clear message; the final output can still be written with remaining rows.

## CLI: Selected Policies, Filters, and Stocks

Runtime selections must match keys loaded by the config.

```bash
aizynthcli \
  --config config.yml \
  --smiles targets.smi \
  --policy uspto ringbreaker \
  --filter uspto_filter \
  --stocks zinc emolecules \
  --output output.json.gz
```

Selection defaults when flags are omitted:

- Stocks: all loaded stocks are selected.
- Expansion policy: the first loaded expansion policy is selected.
- Filter policy: all loaded filters are selected.

Use explicit flags when reproducibility matters or when a config loads multiple keys. A key mismatch usually fails during policy/filter/stock selection or produces an unexpected empty selection; see `troubleshooting.md`.

## CLI: Checkpointed Batch

Use `--checkpoint` for long batch jobs that should resume from processed rows.

```bash
aizynthcli \
  --config config.yml \
  --smiles targets.smi \
  --output output.json.gz \
  --checkpoint checkpoint.json.gz
```

Checkpoint behavior:

- The checkpoint file is newline-delimited JSON, one processed target per line.
- If the checkpoint exists, AiZynthFinder counts already processed rows and resumes the input file after that count.
- Each new successful or failed processed result is appended as it completes.
- Keep the same input file order, config, policy/filter/stock selections, and output intent when resuming.
- `--checkpoint` is part of the single-process batch path; the multiprocessing helper path does not pass checkpoint through to child commands.

## CLI: Multiprocessing Batch

Use `--nproc` only for batch files.

```bash
aizynthcli \
  --config config.yml \
  --smiles targets.smi \
  --output output.json.gz \
  --policy multi_expansion_strategy \
  --filter uspto_filter \
  --stocks zinc \
  --cluster \
  --nproc 4
```

Behavior:

- `--smiles` must name an existing file or the CLI raises `ValueError`.
- The input file is split across worker processes and temporary per-worker outputs are concatenated.
- Worker commands preserve `--policy`, `--filter`, `--stocks`, `--cluster`, and `--post_processing` selections.
- Worker commands do not preserve `--pre_processing`, `--checkpoint`, or `--log_to_file`; avoid multiprocessing when those are required.
- If not all worker outputs are produced, the CLI raises `FileNotFoundError` and points to `aizynthcli*.log` files.

## CLI: Clustering and Hooks

```bash
aizynthcli \
  --config config.yml \
  --smiles targets.smi \
  --cluster \
  --pre_processing my_pre_module \
  --post_processing my_post_module \
  --output output.json.gz
```

Notes:

- `--cluster` asks AiZynthFinder to cluster extracted routes. The optional route-distance stack must be installed for clustering support.
- `--pre_processing MODULE` imports `MODULE` and calls `pre_processing(finder, index)` before each target; `index` is `-1` for single-target mode and the row index for batch mode.
- `--post_processing MODULE...` imports each module and calls `post_processing(finder)` after route building; returned key/value pairs are merged into statistics.
- Missing hook modules or modules without the expected function are silently ignored by the CLI loader.
- Hook implementation belongs to `../extension-and-development/SKILL.md`.

## Python: Full Planning Lifecycle

```python
from aizynthfinder.aizynthfinder import AiZynthFinder

finder = AiZynthFinder(configfile="config.yml")
finder.stock.select(["zinc"])
finder.expansion_policy.select(["uspto"])
finder.filter_policy.select(["uspto_filter"])

finder.target_smiles = "CCO"
finder.prepare_tree()
finder.tree_search(show_progress=False)
finder.build_routes()
stats = finder.extract_statistics()
stock_info = finder.stock_info()
```

Lifecycle rules:

- `AiZynthFinder(configfile=...)` loads YAML config; `AiZynthFinder(configdict=...)` loads a Python dictionary; with neither, policies and stocks must be loaded manually before useful planning.
- Set `target_smiles` or `target_mol` before `prepare_tree()` or `tree_search()`.
- Calling `tree_search()` without a prepared tree calls `prepare_tree()` automatically.
- Call `build_routes()` after search and before route analysis, `extract_statistics()` with route statistics, or `stock_info()`.
- Assigning a new target clears the previous search tree.
- `tree_search(show_progress=True)` displays a progress bar; prefer `False` for scripts and non-interactive agents.

## Python: One-Step Expansion

```python
from aizynthfinder.aizynthfinder import AiZynthExpander

expander = AiZynthExpander(configfile="config.yml")
expander.expansion_policy.select(["uspto"])
expander.filter_policy.select(["uspto_filter"])
reactions = expander.do_expansion("CCO", return_n=5)

reactants_by_group = [
    [mol.smiles for mol in reaction_tuple[0].reactants[0]]
    for reaction_tuple in reactions
]
```

Behavior:

- `do_expansion()` returns a list of tuples of `FixedRetroReaction` objects.
- Each tuple groups reactions that produce the same reactants.
- `return_n` limits the number of unique reactant groups retained.
- `filter_func` can drop candidate reactions by returning `False` for a reaction object.
- When a selected filter policy exposes feasibility, the first such filter adds a `feasibility` value into reaction metadata.
- Reaction metadata includes `expansion_rank` for retained unique groups.

## GUI and Notebook

Use the notebook interface only when a browser/Jupyter/widget environment is available.

```bash
aizynthapp --config config.yml
```

or save a notebook file without launching it:

```bash
aizynthapp --config config.yml --output aizynthfinder_app.ipynb
```

Inside an existing notebook:

```python
from aizynthfinder.interfaces import AiZynthApp
app = AiZynthApp("config.yml")
finder = app.finder
```

Notes:

- The app wraps an `AiZynthFinder` instance as `app.finder`.
- The GUI supports target entry, stock/policy/filter choices, search limits, MCTS rewards, and route display.
- If the config uses a non-MCTS search algorithm, the GUI resets it to MCTS before running.
- GUI clustering uses optional notebook and route-distance dependencies.
