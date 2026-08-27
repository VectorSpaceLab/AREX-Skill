---
name: msa-search
description: "Generate ColabFold MSAs using the public server, local MMseqs2
  databases, GPU search, split/merge helpers, AlphaFold3 JSON export, and local
  MSA server planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MSA Search

Use this sub-skill when the task is to create, validate, stage, or troubleshoot multiple sequence alignments for ColabFold jobs. It owns public-server MSA generation, local `colabfold_search` database searches, MMseqs2 GPU/gpuserver routes, MSA-only staging, split/merge helpers, AlphaFold3 JSON export from MSAs, and local MSA server caveats.

Route away from this sub-skill when the user primarily needs:

- Input syntax, FASTA/CSV/A3M validation, AF3 ligand syntax, or filename normalization: use `../inputs-and-formats/`.
- Running structure prediction after MSAs already exist: use `../batch-prediction/`.
- Amber relaxation, PDB/mmCIF confidence interpretation, or post-processing outputs: use `../relaxation-and-outputs/`.

## Fast route

1. Decide the MSA source:
   - Small serial local jobs: public MSA server through `colabfold_batch --msa-only` or implicit `colabfold_batch input out`.
   - Large batches or private/high-throughput work: local `colabfold_search` with a prepared MMseqs2 database directory.
   - Repeated low-latency local searches: local databases plus MMseqs2 GPU search or `gpuserver`, if hardware and database layout support it.
2. Validate inputs before searching. Protein sequences receive MMseqs2 MSAs; non-protein AF3 components are represented in JSON but do not receive MMseqs2 unpaired MSAs.
3. For local database work, run the bundled read-only checker before giving search commands:

```bash
python scripts/check_mmseqs_databases.py /path/to/db_folder --check-mmseqs --mode cpu
python scripts/check_mmseqs_databases.py /path/to/db_folder --mode gpu --require-index
```

4. Build the workflow from the references:
   - CLI options and examples: [`references/cli-reference.md`](references/cli-reference.md)
   - Local database, GPU, split/merge, and AF3 JSON workflows: [`references/local-mmseqs-workflows.md`](references/local-mmseqs-workflows.md)
   - Local API/MSA server deployment caveats: [`references/msa-server.md`](references/msa-server.md)
   - Failure diagnosis: [`references/troubleshooting.md`](references/troubleshooting.md)

## Common task patterns

- Public server MSA-only staging:

```bash
colabfold_batch input_sequences.fasta out_dir --msa-only
colabfold_batch input_sequences.fasta out_dir
```

- Local database MSA generation:

```bash
colabfold_search input_sequences.fasta /path/to/db_folder msas
colabfold_batch msas predictions
```

- Local GPU search with explicit devices:

```bash
CUDA_VISIBLE_DEVICES=0,1 colabfold_search input_sequences.fasta /path/to/db_folder msas --gpu 1
```

- AlphaFold3-compatible MSA JSON from local search:

```bash
colabfold_search input_sequences.fasta /path/to/db_folder msas --af3-json
```

## Safety notes

- Database setup is a heavy network/storage operation. This sub-skill describes the required layout and safe validation checks but does not bundle or run database download scripts.
- Local MSA server setup mutates system state, downloads binaries/databases, and may install services; treat it as planning guidance unless the user explicitly approves those operations.
- Do not run public MSA server jobs in parallel from multiple machines against the same service/IP. Prefer serial small jobs or a local database/server for high-throughput workloads.
