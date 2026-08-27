# CLI, Container, And HPC Troubleshooting

## Missing Auxiliary Resources

Symptoms:

- `ctx` fails opening ranking databases or motif annotations.
- `ctx` returns empty or implausible regulons because resources are from the wrong species or gene namespace.
- A planned run cannot start because database files are absent.

Checks and fixes:

- Confirm every ranking database path exists before running `ctx`.
- Prefer current Feather v2 databases with names ending in `*.genes_vs_motifs.rankings.feather` or `*.genes_vs_tracks.rankings.feather`.
- Match expression genes, TF list, motif annotations, and ranking databases by species and symbol namespace.
- Do not let a skill helper download large databases automatically; ask the user to provide approved local resource paths.

## Huge Database Downloads Or Storage Pressure

Symptoms:

- A run plan assumes resources that are not present.
- Containers fail because database files are not mounted or are too large for the selected filesystem.

Checks and fixes:

- Treat ranking databases as pre-existing inputs and document expected filenames.
- Place databases on fast read-shared storage for `ctx`, especially under Dask or scheduler execution.
- Avoid copying multi-GB databases into container layers, temporary job directories, or small home directories.

## Container Path Or Volume Mismatch

Symptoms:

- A command works on the host but containerized pySCENIC reports `No such file or directory`.
- `ctx` can read the adjacency file but cannot read databases or annotations.
- Outputs are missing on the host after a successful container command.

Checks and fixes:

- Replace all command paths with container-runtime paths, such as `/data/...`, after mounting the host project root.
- Use `docker run --rm -v "$HOST_PROJECT:/data" IMAGE sh -lc 'test -r /data/file && test -w /data/out'` before expensive runs.
- Ensure `@args.txt` files contain runtime paths, not host paths.
- Mount every resource root that appears in the command, not only the expression matrix directory.

## `@args.txt` Quoting Problems

Symptoms:

- `pyscenic @ctx.args.txt` treats quoted paths literally.
- Options appear to be missing even though they are visible in the file.
- Paths with spaces fail unexpectedly.

Checks and fixes:

- Put one argument per line.
- Do not wrap paths in shell quotes inside args files.
- Avoid spaces in runtime paths when possible; if paths with spaces are unavoidable, validate with a small `--help` or preflight command in the same runtime.
- Keep comments out of args files unless verified in the target Python argparse behavior.
- Put the subcommand, such as `ctx`, on the first line when invoking `pyscenic @file`.

## Wrong Output Extension

Symptoms:

- Downstream steps cannot read an output.
- Delimiters or output format do not match expectations.
- AUCell tries to append metadata to loom or h5ad output but the expression input has the wrong matching format.

Checks and fixes:

- Use `.tsv` or `.csv` for adjacency tables; pySCENIC chooses text delimiters from suffixes.
- Use `.csv` or `.tsv` for inspectable motif tables from `ctx`.
- Use `.gmt`, `.yaml`, or `.dat` for compact regulon/signature collections when that is the intended AUCell handoff.
- For `aucell -o out.loom`, provide expression input as loom so pySCENIC can copy and append AUC metadata.
- For h5ad output, confirm AnnData support is installed and expression input is also h5ad; route broader scanpy analysis outside this CLI plan.

## CLI Help Or Import Dependency Problems

Symptoms:

- `pyscenic --help` fails before showing help.
- `pyscenic ctx --help` or `arboreto_with_multiprocessing.py --help` fails with import errors.
- Local CLI and container CLI report different behavior.

Checks and fixes:

- Run `python scripts/pyscenic_cli_smoke.py --check-help` from this sub-skill to capture exact command failures.
- Confirm `pyscenic`, `pyscenic.cli.pyscenic`, `pyscenic.aucell`, `pyscenic.prune`, and `pyscenic.utils` import in the selected environment.
- Use the container image when local dependency resolution is unreliable and container runtime is already approved.
- Use `arboreto_with_multiprocessing.py --help` to confirm the Dask-free fallback is on `PATH` before recommending it.

## Expression Orientation Mismatch

Symptoms:

- pySCENIC reports no genes, low TF overlap, or implausible output dimensions.
- `grn` warns that less than 80% of supplied TFs are present in expression genes.

Checks and fixes:

- For CSV/TSV cells-by-genes input, omit `--transpose`.
- For CSV/TSV genes-by-cells input, add `--transpose` to every command that reads expression.
- For loom input, do not use text-file orientation assumptions; check `--gene_attribute` and `--cell_id_attribute` instead.
- Verify species and symbol conventions before rerunning expensive inference.

## Dask Or HPC Shared Filesystem Constraints

Symptoms:

- The scheduler starts but workers fail opening databases or input files.
- `ctx --mode dask_cluster` exits because `--client_or_address` is missing.
- Cluster jobs produce partial outputs or workers fail with path errors.

Checks and fixes:

- For `ctx --mode dask_cluster`, provide `--client_or_address` for an existing scheduler.
- Ensure every Dask worker sees the same input, database, annotation, and output paths.
- Prefer `custom_multiprocessing` for single-host `ctx` unless the task explicitly needs Dask modes.
- Use scheduler-allocated CPU/memory values for `--num_workers`; do not use a workstation default on an HPC node.
- If Dask blocks GRN inference, switch only the GRN step to `arboreto_with_multiprocessing.py` and keep downstream planning unchanged.

## Container Image Variant Confusion

Symptoms:

- CLI tasks are slow to pull or run because a large scanpy image was selected unnecessarily.
- Notebook tasks, scanpy-dependent analysis, or AnnData/h5ad commands fail in the CLI-only image.

Checks and fixes:

- Use the base pySCENIC image for non-interactive CLI pipelines.
- Use the scanpy image only when the task needs scanpy, IPython kernels, downstream notebooks, or missing AnnData/h5ad dependencies that are not available locally.
- Keep image tags explicit and do not mix base and scanpy images between pipeline steps without recording why.

## AnnData Or Scanpy Extras

Symptoms:

- `pyscenic aucell -o output.h5ad` fails importing `anndata` or writing metadata.
- Notebook or downstream visualization commands are unavailable.

Checks and fixes:

- Use an environment with AnnData support, or the scanpy-enabled container when notebooks or scanpy are also needed.
- For pure pySCENIC CLI output, prefer CSV/TSV or loom if h5ad dependencies are not already available.
- Route detailed data export and loom/h5ad behavior to the data I/O/export sub-skill when available.
