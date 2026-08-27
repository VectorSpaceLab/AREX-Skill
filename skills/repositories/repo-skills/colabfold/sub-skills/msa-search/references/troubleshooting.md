# MSA Search Troubleshooting

Use this page for failures owned by MSA generation, local MMseqs2 search, GPU/gpuserver search, split/merge helpers, AF3 JSON export, and local MSA server planning.

## Triage checklist

1. Identify the route: public server through `colabfold_batch`, local `colabfold_search`, split/merge helper, AF3 JSON export, or local API server.
2. Confirm CLI availability:

```bash
colabfold_search --help
colabfold_split_msas --help
mmseqs --help
```

3. For local databases, run:

```bash
python ../scripts/check_mmseqs_databases.py /path/to/db_folder --check-mmseqs
```

4. Reproduce with one small protein query before debugging a large batch.
5. Separate MSA generation from prediction: MSA failures are handled here; model download/JAX/AlphaFold failures route to `../../batch-prediction/`.

## Optional dependency failures

### `colabfold_search: command not found`

Cause: ColabFold is not installed in the active environment, the script directory is not on `PATH`, or the user installed only a different environment.

Fix:

```bash
python -m pip show colabfold
python -m pip install colabfold
python -m pip show -f colabfold | grep colabfold_search || true
```

Then restart the shell or call the script by its absolute environment path if appropriate.

### `mmseqs command not found`

Cause: MMseqs2 is absent or not on `PATH`.

Fix options:

- Install MMseqs2 through the environment manager appropriate for the project.
- Pass an explicit binary with `colabfold_search --mmseqs /path/to/mmseqs`.
- Run the checker with `--mmseqs /path/to/mmseqs --check-mmseqs`.

### MMseqs2 lacks GPU support

Symptoms:

- `mmseqs gpuserver` is unavailable.
- GPU search flags fail immediately.
- `mmseqs --help` does not mention `gpuserver` or GPU options.

Fix:

- Use CPU search with `--gpu 0`, or install a GPU-capable MMseqs2 build compatible with the CUDA stack.
- Do not conflate this with AlphaFold/JAX GPU support; MMseqs2-GPU is a separate backend.

## Backend and GPU failures

### `gpuserver` timeout or search waits for server

Likely causes:

- `gpuserver` and `colabfold_search` were started with different `CUDA_VISIBLE_DEVICES` values.
- The server was started for only one database, but the search expects UniRef and environmental databases.
- `--gpu-server 1` was set without running `mmseqs gpuserver`.
- `--db-load-mode 2` was used but databases are not resident or the server is not visible.

Fix:

```bash
# Use the same device list for server and client.
export CUDA_VISIBLE_DEVICES=0,1
mmseqs gpuserver /data/colabfold_db/uniref30_2302_db --max-seqs 10000 --db-load-mode 0 --prefilter-mode 1 &
mmseqs gpuserver /data/colabfold_db/colabfold_envdb_202108_db --max-seqs 10000 --db-load-mode 0 --prefilter-mode 1 &
colabfold_search input.fasta /data/colabfold_db msas --gpu 1 --gpu-server 1 --db-load-mode 2
```

If still failing, run `colabfold_search ... --gpu 0` on the same input/database to prove the database and query are valid.

### CUDA or VRAM errors during search

Likely causes:

- MMseqs2-GPU build is incompatible with the installed driver/runtime.
- Database/index is too large for the visible GPU memory and host streaming is failing or too slow.
- Too many visible GPUs or wrong device ordering causes unexpected placement.

Fix:

- Pin devices with `CUDA_VISIBLE_DEVICES`.
- Reduce concurrency and try a single small query.
- Fall back to CPU search for the MSA stage.
- Rebuild or reinstall MMseqs2-GPU rather than changing ColabFold prediction dependencies.

## Data and configuration failures

### `FileNotFoundError: Database ... does not exist`

Cause: `dbbase` is wrong, database basenames differ from defaults, or setup did not finish.

Fix:

```bash
python ../scripts/check_mmseqs_databases.py /data/colabfold_db
colabfold_search input.fasta /data/colabfold_db msas --db1 uniref30_2302_db --db3 colabfold_envdb_202108_db
```

If using non-default names, pass `--db1`, `--db2`, `--db3`, and `--db4` explicitly.

### Missing `.idx` files

Meaning:

- Not necessarily fatal for batch CPU `colabfold_search`; the code can fall back to non-index suffixes and `db_load_mode 0` behavior.
- Important for low-latency server, fast single-query, and GPU/gpuserver workflows.

Fix:

- For batch CPU work, continue if `.dbtype` markers exist and performance is acceptable.
- For server/GPU workflows, prepare indexes in an approved database setup process and re-run the checker with `--require-index`.

### Environmental database missing

Symptoms: default search fails looking for `colabfold_envdb_202108_db`.

Fix options:

```bash
# Use UniRef-only MSAs if acceptable.
colabfold_search input.fasta /data/colabfold_db msas --use-env 0
```

Or complete the environmental database setup before running full ColabFold-like MSAs.

### Template database missing

Symptoms occur only when `--use-templates 1` is requested.

Fix:

- Disable templates for MSA-only workflows that do not need template `.m8` output.
- If templates are required, confirm the PDB/template database basename and pass `--db2` explicitly.

## CLI and API failures

### No `.a3m` files after local search

Likely causes:

- `--unpack 0` kept MMseqs2 databases instead of loose files.
- Search failed before the unpack step.
- Output directory differs from the one being inspected.

Fix:

```bash
find msas -maxdepth 1 -type f -print | head
colabfold_split_msas search_work output_msas
```

If `final.a3m` is absent, inspect the MMseqs2 error before trying to split.

### `colabfold_split_msas` fails on `final.a3m`

Cause: the search folder does not contain `final.a3m`, or the file is incomplete/corrupt.

Fix:

- Confirm the source search used `--unpack 0` or otherwise preserved `final.a3m`.
- Re-run a small local search and split that output.
- Ensure the output folder is writable.

### Python API removes intermediate files

The internal search functions run MMseqs2 cleanup commands such as `rmdb` and remove temporary directories under `base`. Do not point `base` at a directory containing unrelated user files. Use a dedicated work directory.

## Public server workflow failures

### Server errors, queue delays, or rate limits

Fix:

- Retry a single small query later.
- Use `colabfold_batch input out --msa-only` to separate network/MSA failures from GPU prediction failures.
- For large or automated jobs, switch to local `colabfold_search` or a local MSA server.
- Do not work around public-service limits with multiple machines or uncontrolled parallelism.

### Privacy concern after planning public-server route

Fix: switch to local databases or a local MSA server. Public server workflows transmit sequences to an external service.

## AF3 JSON failures

### JSON is missing non-protein MSAs

Expected behavior: ColabFold MMseqs2 generates MSAs for protein sequences. Non-protein AF3 components such as RNA, DNA, CCD, and SMILES can be represented in JSON, but RNA entries do not receive ColabFold unpaired MSAs.

Fix: validate the AF3 JSON structure and route detailed molecule syntax repair to `../../inputs-and-formats/`.

### JSON parse error

Fix:

```bash
python -m json.tool msas/job.json >/dev/null
```

If parsing fails, regenerate from a minimal input and check sequence headers/job names for unsafe characters. For SMILES inputs, replace aromatic bond `:` characters with `;` before parsing.

## Local MSA server failures

### Server starts but jobs fail

Likely causes:

- Config paths point to missing databases or template folders.
- Worker count is too high for CPU/RAM.
- MMseqs2 binary path differs between shell and service context.
- Results/scratch directory is not writable by the service user.

Fix:

- Validate database paths with the bundled checker.
- Run one foreground local worker before using a service manager.
- Lower worker count and database parallelism.
- Inspect server logs for the exact MMseqs2 command failure.

### Server is reachable but unsafe to expose

Fix before exposure:

- Keep database-management endpoints disabled unless on a trusted admin-only network.
- Add TLS/authentication through an appropriate proxy or server config.
- Enable rate limiting for shared resources.
- Define cleanup for job results and scratch directories.
