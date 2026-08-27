# AUCell And Binarization Workflows

These workflows assume regulons or gene signatures already exist. If the task is to create regulons from a network or motif enrichment result, route to `../motif-pruning-and-regulons/SKILL.md` first.

## Workflow 1: Score Activity With The Python API

1. Prepare an expression matrix as cells x genes.
2. Prepare `GeneSignature` or regulon objects whose gene identifiers match expression columns.
3. Optionally inspect detection-driven AUC threshold candidates.
4. Run `aucell` with a fixed `seed` and an appropriate `num_workers` value.
5. Confirm the result is cells x regulons.

```python
import pandas as pd
from ctxcore.genesig import GeneSignature
from pyscenic.aucell import aucell, derive_auc_threshold

exp_mtx = pd.DataFrame(
    [[9, 8, 0, 0], [8, 7, 0, 1], [0, 1, 9, 8]],
    index=["CellA", "CellB", "CellC"],
    columns=["GeneA", "GeneB", "GeneC", "GeneD"],
)
regulons = [
    GeneSignature(name="TF_AB", gene2weight={"GeneA": 1.0, "GeneB": 1.0}),
    GeneSignature(name="TF_CD", gene2weight={"GeneC": 1.0, "GeneD": 1.0}),
]
threshold_candidates = derive_auc_threshold(exp_mtx)
auc_mtx = aucell(
    exp_mtx,
    regulons,
    auc_threshold=float(threshold_candidates.loc[0.05]),
    seed=13,
    num_workers=1,
)
assert list(auc_mtx.index) == list(exp_mtx.index)
assert list(auc_mtx.columns) == ["TF_AB", "TF_CD"]
```

Use `create_rankings` and `aucell4r` instead of `aucell` when you need to reuse a ranking matrix across many signature collections.

## Workflow 2: Run `pyscenic aucell` Safely

For cells x genes CSV input:

```bash
pyscenic aucell expression.cells_x_genes.csv signatures.gmt \
  --auc_threshold 0.05 \
  --num_workers 4 \
  --seed 13 \
  -o auc.csv
```

For genes x cells CSV/TSV input:

```bash
pyscenic aucell --transpose expression.genes_x_cells.tsv signatures.gmt \
  --num_workers 4 \
  --seed 13 \
  -o auc.csv
```

For weighted regulons where weights should affect recovery, include `--weights`. Without `--weights`, CLI scoring ignores signature weights.

Before trusting a run, check:

- Text matrix rows and columns match the selected orientation.
- Signature names become output columns.
- Most signature genes overlap expression matrix gene columns.
- Output rows correspond to cells unless intentionally transposed for text output.
- Loom or h5ad output is only requested when the matching optional dependencies and metadata are present.

## Workflow 3: Binarize AUCell Activity

Use `binarize` when the task needs active/inactive regulon calls per cell.

```python
from pyscenic.binarization import binarize, derive_threshold

threshold = derive_threshold(auc_mtx, "TF_AB", seed=13, method="hdt")
binary_mtx, thresholds = binarize(
    auc_mtx,
    threshold_overides={"TF_AB": threshold},
    seed=13,
    num_workers=1,
)
assert binary_mtx.shape == auc_mtx.shape
assert set(binary_mtx.stack().unique()).issubset({0, 1})
```

Manual thresholds are useful when the automated distribution check is biologically implausible, too conservative for a unimodal distribution, or needs to match external SCENIC/SCope thresholds. Use the exact keyword `threshold_overides`.

## Workflow 4: Plot Activity Thresholds

Use plotting for inspection, not as the only validation.

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pyscenic.plotting import plot_binarization

fig, ax = plt.subplots(figsize=(4, 3))
plot_binarization(auc_mtx, "TF_AB", float(thresholds["TF_AB"]), bins=20, ax=ax)
fig.tight_layout()
fig.savefig("TF_AB_binarization.png", dpi=150)
```

If the distribution is unimodal, expect the threshold to be `mean + 2 * std`; the threshold line may sit near the high tail and mark few or no cells active.

## Workflow 5: Compute Regulon Specificity Scores

Use RSS to summarize which regulons are specific to cell type labels.

```python
import pandas as pd
from pyscenic.rss import regulon_specificity_scores
from pyscenic.plotting import plot_rss

cell_types = pd.Series(
    ["Type1", "Type1", "Type2"],
    index=auc_mtx.index,
    name="cell_type",
)
cell_types = cell_types.reindex(auc_mtx.index)
rss = regulon_specificity_scores(auc_mtx, cell_types)
assert set(rss.index) == set(cell_types.unique())
assert list(rss.columns) == list(auc_mtx.columns)
```

For plotting, call `plot_rss(rss, "Type1", top_n=5)` and save the Matplotlib figure. RSS expects meaningful non-negative AUC values; all-zero columns are not useful specificity inputs.

## Workflow 6: Verify Orientation With A Tiny Fixture

A safe orientation test should use a signature enriched in one group of cells and assert that those cells score higher.

```python
expected_high = auc_mtx.loc[["CellA", "CellB"], "TF_AB"].mean()
expected_low = auc_mtx.loc[["CellC"], "TF_AB"].mean()
assert expected_high > expected_low
```

If this assertion fails on a real dataset, first suspect a matrix orientation problem, mismatched gene symbols, or a signature file separator/format issue.

## Bundled Smoke Helper

Run the bundled helper to prove the installed API path works on tiny data:

```bash
python scripts/aucell_smoke.py
python scripts/aucell_smoke.py --show-cli
```

The helper generates an in-memory expression matrix and signatures, runs AUCell, optionally runs binarization, and checks output orientation. It performs no network access, training, downloads, or destructive filesystem actions.

## Bounded Validation Ideas

- Use `scripts/aucell_smoke.py` to assert output orientation, expected regulon columns, and higher AUC for cells expressing signature genes.
- Use `pyscenic aucell --help` to verify the CLI surface without requiring data files.
- Build an intentionally unimodal AUC matrix plus a manual `threshold_overides` mapping to confirm diagnosis and override behavior.
