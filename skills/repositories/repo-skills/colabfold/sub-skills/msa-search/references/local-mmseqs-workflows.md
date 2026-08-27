# Local MMseqs Workflows

Use local MMseqs2 when public-server limits, privacy, reproducibility, or throughput make server MSAs unsuitable. Local search requires large prepared databases and a compatible `mmseqs` binary.

## Choose public server vs local database

Prefer public-server MSAs when:

- The job is small and serial.
- The user accepts sending protein sequences to the public MSA service.
- The machine does not have hundreds of GB of database storage.
- The user primarily needs convenience and will run prediction locally afterward.

Prefer local databases when:

- The job is large, automated, private, or repeated.
- The user needs stable database versions or local auditability.
- Public-server rate/queue behavior is a bottleneck.
- A local MSA server or GPU-accelerated MMseqs2 route is being planned.

A common large multimer strategy is MSA-only staging on a CPU/search node followed by GPU prediction on another node:

```bash
colabfold_search complex_batch.fasta /data/colabfold_db msas --threads 64 --pair-mode unpaired_paired
colabfold_batch msas predictions
```

## Database layout assumptions

Default local search expects these basenames under the database directory:

- `uniref30_2302_db.dbtype` for UniRef search.
- `colabfold_envdb_202108_db.dbtype` for environmental search when `--use-env 1`.
- Optional `pdb100_230517.dbtype` or configured template DB when `--use-templates 1`.
- Optional `spire_ctg10_2401_db.dbtype` for environmental pairing when `--use-env-pairing 1`.

Index files are workload-dependent:

- No precomputed index can be fine for batch `colabfold_search`; the search code detects missing `.idx`/`.idx.index` and uses non-index suffixes.
- Precomputed `.idx` files are important for low-latency server use and GPU/gpuserver workflows.
- If `MMSEQS_IGNORE_INDEX` is set, ColabFold ignores indexes even if present.

Run the bundled read-only checker before constructing commands:

```bash
python ../scripts/check_mmseqs_databases.py /data/colabfold_db
python ../scripts/check_mmseqs_databases.py /data/colabfold_db --mode cpu --use-templates
python ../scripts/check_mmseqs_databases.py /data/colabfold_db --mode gpu --require-index --check-mmseqs
```

The checker reports missing database markers, optional index markers, MMseqs2 availability, and risky environment settings. It never downloads, deletes, or rewrites databases.

## Database setup planning

Database setup is intentionally not bundled as an executable script because it downloads very large archives, may rsync template mmCIF data, creates indexes, and can require close to TB-scale memory/storage for server-grade indexes.

Planning facts to preserve in user guidance:

- Search-only ColabFold installs can use `pip install colabfold` plus conda/system packages for `mmseqs2`.
- The database setup workflow creates UniRef, environmental, template, and optional index files.
- `MMSEQS_NO_INDEX=1` skips index creation and is often appropriate for large batch `colabfold_search` where precomputed indexes are not needed.
- Without `MMSEQS_NO_INDEX=1`, setup creates indexes that are useful for server use, fast single-query searches, and GPU/gpuserver routes.
- GPU database setup uses `GPU=1` and requires an MMseqs2 build with GPU support.
- Template/PDB data setup is optional unless the command uses `--use-templates 1` or a local API server needs templates.

Do not tell future agents to run a source checkout setup script from the original repository. Instead, explain the storage/network implications, ask for approval, and use current official installation/database instructions appropriate to the user environment.

## CPU search workflow

1. Validate environment:

```bash
command -v colabfold_search
command -v mmseqs
python ../scripts/check_mmseqs_databases.py /data/colabfold_db --check-mmseqs
```

2. Run search:

```bash
colabfold_search input_sequences.fasta /data/colabfold_db msas --threads 32
```

3. Validate output:

```bash
find msas -maxdepth 1 -name '*.a3m' -type f | wc -l
head -n 5 msas/*.a3m
```

4. Hand off to prediction:

```bash
colabfold_batch msas predictions
```

Troubleshooting checks:

- Missing `uniref30_2302_db.dbtype` means the database directory or basename is wrong.
- Missing environmental DB can be handled with `--use-env 0` if the user accepts UniRef-only MSAs.
- If no `.a3m` files appear, confirm `--unpack 1` was used or split `final.a3m` with `colabfold_split_msas`.

## GPU search workflow

GPU search uses MMseqs2-GPU through `colabfold_search --gpu 1`. It is separate from AlphaFold/JAX GPU prediction.

```bash
CUDA_VISIBLE_DEVICES=0,1 colabfold_search input_sequences.fasta /data/colabfold_db msas \
  --gpu 1 --threads 32
```

Requirements:

- MMseqs2 binary supports GPU search.
- CUDA runtime/driver is visible to MMseqs2.
- Databases were prepared in a GPU-compatible form when required by the MMseqs2 version and setup route.
- `CUDA_VISIBLE_DEVICES` is set before the command when only specific devices should be used.

Validation:

```bash
mmseqs --help | grep -E 'gpuserver|--gpu' || true
python ../scripts/check_mmseqs_databases.py /data/colabfold_db --mode gpu --require-index --check-mmseqs
```

If GPU search fails, retry a small CPU search to separate database/input problems from GPU backend problems:

```bash
colabfold_search input_sequences.fasta /data/colabfold_db msas_cpu --gpu 0 --threads 8
```

## Optional `gpuserver` workflow

Use `gpuserver` for repeated low-latency searches. It keeps databases resident in GPU memory or streams efficiently between host and GPU memory.

Start servers for the default environmental and UniRef databases:

```bash
CUDA_VISIBLE_DEVICES=0,1 mmseqs gpuserver /data/colabfold_db/colabfold_envdb_202108_db \
  --max-seqs 10000 --db-load-mode 0 --prefilter-mode 1 &
ENV_PID=$!
CUDA_VISIBLE_DEVICES=0,1 mmseqs gpuserver /data/colabfold_db/uniref30_2302_db \
  --max-seqs 10000 --db-load-mode 0 --prefilter-mode 1 &
UNIREF_PID=$!
```

Run searches against the same visible devices:

```bash
CUDA_VISIBLE_DEVICES=0,1 colabfold_search input_sequences.fasta /data/colabfold_db msas \
  --gpu 1 --gpu-server 1 --db-load-mode 2
```

Stop servers when done:

```bash
kill "$ENV_PID" "$UNIREF_PID"
```

Critical caveat: use the same `CUDA_VISIBLE_DEVICES` value for `gpuserver` and `colabfold_search`. If they differ, `colabfold_search` can wait for a server that is invisible from its device namespace until the timeout.

## Split and merge workflows

Default `colabfold_search` uses `--unpack 1`, which writes one `.a3m` per job. Advanced users may keep MMseqs2 database outputs and split later.

```bash
colabfold_search input_sequences.fasta /data/colabfold_db search_work --unpack 0
colabfold_split_msas search_work output_msas
```

When writing a Python workflow, the split helper is:

```python
from pathlib import Path
from colabfold.mmseqs.split_msas import split_msa
split_msa(Path('search_work/final.a3m'), Path('output_msas'))
```

A separate merge-and-split helper exists for workflows where `uniref.a3m` and `bfd.mgnify30.metaeuk30.smag30.a3m` were produced separately. It shells out to `mmseqs mergedbs`, writes `merged.a3m`, then splits null-separated records. Prefer the maintained CLI route unless the user explicitly has those intermediate MMseqs2 databases.

## AlphaFold3 JSON export

`colabfold_search --af3-json` writes AlphaFold3-compatible JSON alongside generated MSAs.

```bash
colabfold_search input_sequences.fasta /data/colabfold_db msas --af3-json
```

For public-server MSAs through `colabfold_batch`, AF3 JSON export skips structure prediction and writes JSON only:

```bash
colabfold_batch input_sequences.fasta out_dir --af3-json
```

AF3 data assumptions:

- Protein components receive MMseqs2 MSAs.
- DNA/RNA/CCD/SMILES components can be represented in FASTA for JSON export, but RNA entries do not receive ColabFold MMseqs2 unpaired MSAs; they are marked so downstream AF3 can handle them.
- SMILES aromatic bond colons should be replaced with semicolons before input parsing; route syntax repair to `../../inputs-and-formats/`.

Validation:

```bash
find msas -maxdepth 1 \( -name '*.a3m' -o -name '*.json' \) -type f -print
python -m json.tool msas/*.json >/dev/null
```
