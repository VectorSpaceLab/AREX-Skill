# pySCENIC CLI Reference

## Purpose

Use this reference to assemble pySCENIC command-line workflows that move from expression data and TF lists to adjacencies, motif-pruned regulons, and AUCell matrices. Commands assume `pyscenic` is installed and available on `PATH`; use the bundled smoke helper before expensive runs.

## Resource Checklist

Prepare all of these before building an end-to-end command file:

- Expression matrix:
  - CSV/TSV default: cells as rows and genes as columns.
  - CSV/TSV genes as rows and cells as columns: add `--transpose` to each pySCENIC step that reads expression.
  - Loom: genes as rows and cells as columns; default attributes are `Gene` and `CellID`, override with `--gene_attribute` and `--cell_id_attribute` when needed.
- TF list: plain text, one transcription factor per line, matching the expression gene naming convention and species.
- cisTarget ranking databases: one or more local Feather v2 files, normally named like `*.genes_vs_motifs.rankings.feather` or `*.genes_vs_tracks.rankings.feather`.
- Motif-to-TF annotations: local TSV table for the same species/identifier namespace as the ranking databases and expression genes.
- Output directory: writable local or shared path with enough space for adjacency tables, motif tables or regulon files, and AUC matrices.
- Worker plan: bounded `--num_workers` per step; avoid using all logical CPUs on shared machines unless the scheduler grants them.

Ranking databases can be large and motif annotations can also be substantial. This sub-skill should verify that paths already exist; it should not initiate downloads.

## Subcommand Map

`pyscenic` exposes four primary subcommands:

- `pyscenic grn`: infer weighted TF-target adjacencies from expression plus a TF list. Defaults to GRNBoost2; use `--method genie3` for GENIE3. Outputs CSV/TSV adjacency tables depending on suffix.
- `pyscenic add_cor`: optional step that adds Pearson `rho` and regulation direction to adjacencies. `ctx` can also calculate these while building modules from adjacencies.
- `pyscenic ctx`: create modules from adjacency input when `--expression_mtx_fname` is supplied, prune modules against ranking databases, and write enriched motif tables or regulon collections.
- `pyscenic aucell`: score expression cells for regulon or gene-signature activity and write CSV/TSV matrices, loom outputs, or h5ad outputs when AnnData support is installed and both expression input and output use h5ad suffixes.

The installed package also exposes `arboreto_with_multiprocessing.py`, a Dask-free GRNBoost2/GENIE3 fallback for the network inference phase.

## End-to-End Local Template

Set variables to paths in the user environment, then adapt command options. These commands intentionally do not hide required resource choices.

```bash
WORKDIR="/path/to/project"
EXPR="$WORKDIR/expression_cells_by_genes.csv"
TFS="$WORKDIR/tfs.txt"
DB1="$WORKDIR/databases/species-window-a.genes_vs_motifs.rankings.feather"
DB2="$WORKDIR/databases/species-window-b.genes_vs_motifs.rankings.feather"
ANNOTATIONS="$WORKDIR/motif_annotations.tbl"
OUT="$WORKDIR/pyscenic-output"
WORKERS=8
SEED=777
mkdir -p "$OUT"

pyscenic grn \
  --method grnboost2 \
  --num_workers "$WORKERS" \
  --seed "$SEED" \
  -o "$OUT/adjacencies.tsv" \
  "$EXPR" \
  "$TFS"

pyscenic ctx \
  "$OUT/adjacencies.tsv" \
  "$DB1" \
  "$DB2" \
  --annotations_fname "$ANNOTATIONS" \
  --expression_mtx_fname "$EXPR" \
  --mode custom_multiprocessing \
  --num_workers "$WORKERS" \
  --output "$OUT/regulons.csv"

pyscenic aucell \
  "$EXPR" \
  "$OUT/regulons.csv" \
  --num_workers "$WORKERS" \
  --seed "$SEED" \
  -o "$OUT/auc_mtx.csv"
```

Use `--transpose` consistently on `grn`, `add_cor`, `ctx`, and `aucell` when text expression input is genes-by-cells. Do not add `--transpose` for normal loom or h5ad input.

## Optional Correlation Step

Use `add_cor` when a task needs an inspectable adjacency file with correlation direction before `ctx`:

```bash
pyscenic add_cor \
  --mask_dropouts \
  -o "$OUT/adjacencies_with_rho.tsv" \
  "$OUT/adjacencies.tsv" \
  "$EXPR"
```

Then feed `adjacencies_with_rho.tsv` into `ctx`. Without `--mask_dropouts`, pySCENIC uses all cells for current correlation behavior.

## Dask-Free GRN Fallback

Use the bundled executable `arboreto_with_multiprocessing.py` if Dask startup, scheduler connectivity, or Dask metadata issues block `pyscenic grn`:

```bash
arboreto_with_multiprocessing.py \
  --method grnboost2 \
  --num_workers "$WORKERS" \
  --seed "$SEED" \
  --output "$OUT/adjacencies.tsv" \
  "$EXPR" \
  "$TFS"
```

This fallback stays on one host and cannot distribute a GRN run across cluster nodes. Route detailed network-inference choices to `../network-inference/SKILL.md`.

## `ctx` Output Suffix Choices

Choose the `ctx --output` suffix before running:

- `.csv` or `.tsv`: enriched motif table with motif, NES/AUC/rank metadata, annotations, context, and target-gene information; best for inspection and later conversion.
- `.gmt`, `.yaml`, or `.dat`: regulon/signature collections for compact downstream AUCell input.
- `.json`: export-style regulon mapping; verify intended reload behavior before using it as the normal pipeline handoff.

If the first `ctx` positional input is an adjacency table (`.csv` or `.tsv`), include `--expression_mtx_fname` so `ctx` can build modules. If the first input is already a module/signature file (`.yaml`, `.gmt`, `.dat`), `--expression_mtx_fname` is not required unless the command is reconstructing modules.

## `@args.txt` Command Files

`pyscenic` uses Python argparse `fromfile_prefix_chars="@"`, so arguments can be placed one per line and invoked as `pyscenic @args.txt`. Prefer this for long `ctx` commands, especially inside containers or schedulers.

Example `ctx.args.txt`:

```text
ctx
/path/in/runtime/adjacencies.tsv
/path/in/runtime/db1.genes_vs_motifs.rankings.feather
/path/in/runtime/db2.genes_vs_motifs.rankings.feather
--annotations_fname
/path/in/runtime/motif_annotations.tbl
--expression_mtx_fname
/path/in/runtime/expression_cells_by_genes.csv
--mode
custom_multiprocessing
--num_workers
8
--output
/path/in/runtime/regulons.csv
```

Rules for robust args files:

- Put each option and each value on its own line.
- Do not add shell quotes around paths; the shell is not parsing lines inside the file.
- Use paths as seen by the executing runtime, such as container-internal mounted paths, not host-only paths.
- Keep comments out of args files unless the local argparse version has been verified to ignore them.
- When using `pyscenic @ctx.args.txt`, the first line should be the subcommand.

## Dry-Run Planning Checklist

Before running a full pipeline, verify:

1. `pyscenic --help`, `pyscenic grn --help`, `pyscenic ctx --help`, and `pyscenic aucell --help` all work in the exact runtime environment.
2. Every input path exists where the command will execute, including inside containers and on cluster workers.
3. The expression orientation decision is written down and applied consistently.
4. TF list, motif annotations, ranking databases, and expression matrix use compatible species and gene identifiers.
5. Ranking databases are current Feather v2 files unless intentionally working with a legacy installation.
6. Output suffixes match intended file formats.
7. `--num_workers` fits CPU and memory allocation; for `ctx`, ranking database memory can dominate.
8. Local output, temporary, and database paths are visible to every Dask/HPC worker when using cluster modes.

The bundled script can print equivalent templates and optional args files:

```bash
python scripts/pyscenic_cli_smoke.py \
  --check-help \
  --emit-template \
  --workdir /runtime/work \
  --workers 8
```
