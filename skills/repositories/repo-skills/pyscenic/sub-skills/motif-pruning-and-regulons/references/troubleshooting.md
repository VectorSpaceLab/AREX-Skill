# Motif Pruning and Regulon Troubleshooting

## Feather v2 and Database Format Problems

Symptoms:

- `pyscenic ctx` fails while opening a ranking database.
- Errors mention incompatible Feather, old database format, missing ranking columns, or `ctxcore`.
- A legacy `.db` file appears in a command copied from old examples.

Actions:

- Prefer modern cisTarget Feather v2 databases compatible with `ctxcore >= 0.2`.
- Use files ending in `*.genes_vs_motifs.rankings.feather` for motif pruning or `*.genes_vs_tracks.rankings.feather` for track-based workflows.
- Do not assume old `.db` examples are valid for current pySCENIC, even though some CLI help still mentions legacy DB files.
- Verify that database species, genome build, and motif collection match the motif annotation TSV.

## Missing or Huge Ranking Database Resources

Symptoms:

- File-not-found errors for database paths.
- Very slow startup or memory pressure before modules are processed.
- Cluster workers fail even though the scheduler can see the files.

Actions:

- Confirm every database path is readable from the process that runs `ctx` and from every cluster worker.
- Avoid initiating downloads in an agent run; ask the user to provide ranking databases or confirm a bounded acquisition plan.
- Start with one database and a small module subset when diagnosing path or memory issues.
- Use `.csv` or `.tsv` output during diagnosis so partial motif evidence is inspectable if the run completes.

## Motif Annotation TSV Schema Problems

Symptoms:

- `pandas.read_csv` reports missing columns.
- `prune2df` returns no annotated enriched features.
- Motif enrichment exists in no-pruning mode but pruning mode returns empty results.

Required default columns for `load_motif_annotations`:

- `#motif_id`
- `gene_name`
- `motif_similarity_qvalue`
- `orthologous_identity`
- `description`

Actions:

- Check that the file is tab-separated and not comma-separated.
- Confirm motif IDs match the ranking database feature IDs.
- Relax `--max_similarity_fdr` or `--min_orthologous_identity` only if the scientific task permits it.
- Try `--no_pruning` to distinguish absent enrichment from missing annotation matches.

## Mode and `client_or_address` Mistakes

Symptoms:

- `AssertionError` says a `client_or_address` value is invalid.
- CLI exits with `--mode "dask_cluster" requires --client_or_address argument.`
- Workers hang because they cannot access database files.

Actions:

- CLI `--mode` accepts `custom_multiprocessing`, `dask_multiprocessing`, or `dask_cluster`.
- API `client_or_address` accepts `custom_multiprocessing`, `dask_multiprocessing`, `local`, a scheduler address such as `127.0.0.1:8786`, or a `distributed.Client`.
- For CLI cluster runs, set both `--mode dask_cluster` and `--client_or_address HOST:PORT`.
- On clusters, use shared paths for databases and annotations; pySCENIC sends database proxy objects to workers rather than copying database contents.

## `num_workers` Versus Database Count

Symptom:

- `AssertionError: The number of databases is larger than the number of cores.`

Cause:

- `custom_multiprocessing` requires at least one worker slot per ranking database.

Actions:

- Set `--num_workers` to at least the number of database files.
- Reduce the database list while testing.
- Use Dask modes if local worker allocation does not fit the database count, while still accounting for memory and shared storage.

## Empty Modules or Empty Motif Results

Symptoms:

- CLI logs `Not a single module loaded` and exits.
- `df2regulons` raises `AssertionError: Signatures dataframe is empty!`.
- Warnings say less than 80% of module genes map to a database or no genes in a module could be mapped.

Actions:

- Verify module file suffix and loader: YAML/YML, DAT, and GMT are module files; adjacency CSV/TSV requires `--expression_mtx_fname` so `ctx` can build modules.
- Check gene identifiers against the ranking database gene universe.
- Lower `--min_genes` only when justified; the default is `20` during module generation.
- Use `--no_pruning` to see whether motifs enrich before annotation-backed target pruning.
- Inspect the motif CSV/TSV before converting with `df2regulons`.

## Output Extension Confusion

Symptoms:

- Expected a motif table but got a regulon collection.
- JSON output cannot be loaded back with `load_signatures`.
- `ValueError: Unknown file format` appears during save or reload.
- `.dat` save or load fails with `binary mode doesn't take an encoding argument` in environments where `ctxcore.openfile` is incompatible with binary pickle modes.

Actions:

- Use `.csv` or `.tsv` for enriched motif tables.
- Use `.gmt`, `.dat`, `.yaml`, or `.yml` for regulon collections, but validate `.dat` in the active environment before relying on it for handoff.
- Prefer `.csv`, `.tsv`, `.gmt`, or `.yaml` when portability is more important than pickle fidelity.
- Treat `.json` as an external export mapping from regulon names to target-gene lists, not as a normal pySCENIC reload format in this checkout.
- Match TSV files with tab separators and CSV files with comma separators when calling `load_motifs` manually.

## Memory and I/O Pressure

Symptoms:

- `MemoryError` while processing a module/database pair.
- Dask worker memory warnings.
- Severe slowdown on shared database storage.

Actions:

- Reduce `--num_workers` to lower concurrent database reads and recovery-curve memory.
- Reduce Dask `--chunk_size` for large modules or cluster runs.
- Try `custom_multiprocessing` for stable local execution, or `dask_multiprocessing` when Dask scheduling is preferred.
- Keep large ranking databases on fast shared storage; avoid network filesystems with high latency when possible.
- Start with one database and a small module subset to estimate memory.

## Cluster Shared-Drive Caveats

Symptoms:

- Scheduler starts tasks but workers fail with missing files.
- A run works locally but fails on a cluster.

Actions:

- Confirm that every worker sees the same absolute or mounted paths for ranking databases and motif annotations.
- Avoid temporary node-local paths for resources used by worker processes.
- If shared storage is slow, reduce concurrency before increasing worker count.
- Record database names and parameter thresholds outside the runtime skill output for reproducibility.

## Feature/Interval Parsing Errors

Symptoms:

- `Feature.from_string` raises assertions about BED columns, integer coordinates, score, or strand.
- Interval overlaps do not match expectations.

Actions:

- Provide at least chromosome, start, and end columns.
- Use zero-based, half-open intervals.
- Ensure start/end columns are integers and optional score is numeric.
- Restrict strand to `+`, `-`, `.`, or `?` when present.
- Validate interval behavior with a tiny in-memory `Feature.from_string(...)` example before relying on larger BED files.
