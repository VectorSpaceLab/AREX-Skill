# CLI Reference

This reference covers MSA-generation entry points only. Use the batch-prediction sub-skill for model inference flags and output interpretation.

## `colabfold_batch` public-server MSA route

`colabfold_batch` can query the public MSA server automatically when given FASTA or CSV sequence input. Use it for small, serial jobs and for workflows where the user does not want to maintain local databases.

```bash
# Search the public MSA server and then predict in one command.
colabfold_batch input_sequences.fasta out_dir

# Stage MSAs first, then run prediction later.
colabfold_batch input_sequences.fasta out_dir --msa-only
colabfold_batch input_sequences.fasta out_dir
```

Data assumptions:

- Input can be FASTA or CSV accepted by ColabFold input parsing.
- Complexes can be represented by colon-separated protein chains; route low-level syntax questions to `../../inputs-and-formats/`.
- Public-server use should be serial and small scale. Avoid multiple computers or aggressive parallelism against the public service.

Validation steps:

- Confirm `colabfold_batch --help` works in the active environment before promising a command.
- After `--msa-only`, verify the output directory contains `.a3m` files named after sanitized query names.
- For a staged prediction, pass the same input/output directory relationship that produced the MSAs; do not move or rename files without preserving the query names expected by ColabFold.

## `colabfold_search` local database route

Use `colabfold_search` when the user has local MMseqs2 databases or needs large-scale, private, or repeatable MSA generation.

```bash
colabfold_search input_sequences.fasta /path/to/db_folder msas
colabfold_batch msas predictions
```

Positional arguments:

- `query`: FASTA file with protein or complex queries.
- `dbbase`: directory containing ColabFold MMseqs2 database files.
- `base`: output/intermediate directory. With default unpacking, this becomes a folder of `.a3m` files.

Important options:

- `--mmseqs PATH`: use a specific MMseqs2 binary when `mmseqs` is not on `PATH`.
- `--db1 NAME`: UniRef database basename, default `uniref30_2302_db`.
- `--db2 NAME`: template database basename, default empty and only used with `--use-templates 1`.
- `--db3 NAME`: environmental database basename, default `colabfold_envdb_202108_db`.
- `--db4 NAME`: environmental pairing database basename, default `spire_ctg10_2401_db`.
- `--use-env 0|1`: include environmental unpaired search; default `1`.
- `--use-env-pairing 0|1`: include environmental pairing search for complexes; default `0`.
- `--use-templates 0|1`: produce template `.m8` output; default `0`.
- `--pair-mode unpaired|paired|unpaired_paired`: controls complex MSA pairing output; default `unpaired_paired`.
- `--filter 0|1|2`: filter MSA diversity. `2` also filters paired MSA.
- `--threads N`: MMseqs2 thread count; default `64`.
- `--db-load-mode N`: MMseqs2 database load behavior; local defaults are command-dependent and may be overridden if no index exists.
- `--unpack 0|1`: unpack MMseqs2 output databases into loose `.a3m` files; default `1`.
- `--gpu 0|1`: enable MMseqs2-GPU search; select devices with `CUDA_VISIBLE_DEVICES`.
- `--gpu-server 0|1`: use a running MMseqs2 `gpuserver`.
- `--af3-json`: write AlphaFold3-compatible JSON next to `.a3m` output.
- `--af3-msa-as-path`: store MSA references as file paths in AF3 JSON rather than embedding strings.

Concrete examples:

```bash
# CPU local search, default UniRef + environmental MSAs.
colabfold_search input.fasta /data/colabfold_db msas --threads 32

# Use a non-standard MMseqs2 binary.
colabfold_search input.fasta /data/colabfold_db msas --mmseqs /opt/mmseqs/bin/mmseqs

# Complex pairing only, useful when unpaired MSAs were handled separately.
colabfold_search complex.fasta /data/colabfold_db msas --pair-mode paired

# Include templates when the PDB/template databases are present.
colabfold_search input.fasta /data/colabfold_db msas --use-templates 1 --db2 pdb100_230517

# Keep MMseqs2 database output instead of loose A3M files for later splitting.
colabfold_search input.fasta /data/colabfold_db search_work --unpack 0
```

## `colabfold_split_msas`

`colabfold_split_msas` splits an unpacked or merged MMseqs2 `final.a3m` database into one `.a3m` file per query. It is useful after advanced workflows that intentionally keep merged search output.

```bash
colabfold_split_msas search_folder output_msas
```

Arguments:

- `search_folder`: directory containing `final.a3m` from a previous local search.
- `output_folder`: directory to receive one `.a3m` per MSA.
- `--mmseqs`: accepted by the CLI for compatibility, but splitting itself reads `final.a3m` directly.

Validation steps:

- Confirm `search_folder/final.a3m` exists before running.
- Confirm `output_folder` is writable and has enough space for many loose A3M files.
- After splitting, count `.a3m` files and compare with the number of input jobs.

## Python APIs for advanced agents

Use these APIs only when writing a Python integration around ColabFold internals; otherwise prefer the CLIs.

```python
from pathlib import Path
from colabfold.mmseqs.search import mmseqs_search_monomer, mmseqs_search_pair
from colabfold.mmseqs.split_msas import split_msa

mmseqs_search_monomer(
    dbbase=Path('/data/colabfold_db'),
    base=Path('work'),
    uniref_db=Path('uniref30_2302_db'),
    metagenomic_db=Path('colabfold_envdb_202108_db'),
    mmseqs=Path('mmseqs'),
    use_env=True,
    use_templates=False,
    filter=True,
    threads=32,
    gpu=0,
    gpu_server=0,
    unpack=True,
)

mmseqs_search_pair(
    dbbase=Path('/data/colabfold_db'),
    base=Path('work'),
    uniref_db=Path('uniref30_2302_db'),
    pair_env=True,
    gpu=False,
    gpu_server=False,
)

split_msa(Path('search_folder/final.a3m'), Path('output_msas'))
```

Signature facts:

- `mmseqs_search_monomer(dbbase, base, ..., gpu=0, gpu_server=0, unpack=True)` searches unpaired UniRef/environmental/template databases and can unpack loose `.a3m` files.
- `mmseqs_search_pair(dbbase, base, ..., pair_env=True, gpu=False, gpu_server=False)` creates paired MSA output for complexes.
- `split_msa(merged_msa, output_folder)` writes one `.a3m` per null-separated MSA record.

API caveats:

- These functions shell out to MMseqs2 and can delete intermediate MMseqs2 databases in `base` as part of cleanup.
- Database basenames are relative to `dbbase` and must include corresponding `.dbtype` files.
- If required `.idx` files are absent, the search code falls back to non-index database suffixes and changes `db_load_mode` behavior.
