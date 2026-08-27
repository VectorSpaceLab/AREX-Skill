# Database and External Tool Preparation

## Safety Rule

Treat database preparation and search execution as heavy side-effecting work. Do not run downloads, clustering, ColabFold setup, HMMER searches, MMseqs searches, or bulk training MSA generation unless the user has confirmed:

- The target data root and available storage.
- Network/download permission, if a database is missing.
- Required binaries are installed or explicit binary paths are available.
- The expected time budget is acceptable.

The runtime skill bundles only a read-only checker. It does not bundle database shell scripts because those scripts download or generate large files.

## Minimal Preflight

Before recommending `protenix mt` or `protenix prep`, check file presence and binaries:

```bash
which hmmsearch hmmbuild nhmmer hmmalign kalign
python sub-skills/msa-template-and-prep/scripts/check_msa_template_layout.py /path/to/data_root/search_database
```

When binaries are not on `PATH`, use explicit command flags instead of changing the user's environment:

- Template: `--hmmsearch_binary_path`, `--hmmbuild_binary_path`.
- RNA: `--nhmmer_binary_path`, `--hmmalign_binary_path`, `--hmmbuild_rna_binary_path`.
- Template parsing/alignment at prediction time may also need `--kalign_binary_path` in prediction workflows; route prediction command construction to `../../cli-and-inference/SKILL.md`.

When databases are not in the default search database directory, use explicit command flags:

- Template: `--seqres_database_path`.
- RNA: `--ntrna_database_path`, `--rfam_database_path`, `--rna_central_database_path`.

## Template Search Database

Template search needs a PDB seqres FASTA:

```text
search_database/pdb_seqres_2022_09_28.fasta
```

Behavior to remember:

- Template search defaults to `search_database/pdb_seqres_2022_09_28.fasta` under the configured data root.
- If the default file is missing and no explicit `--seqres_database_path` is supplied, Protenix may attempt to download it.
- Template search reads `pairing.a3m` and/or `non_pairing.a3m` from the MSA directory and writes `hmmsearch.a3m` beside them.

Safe recommendation order:

1. Validate existing `templatesPath` and `hmmsearch.a3m` with the checker.
2. If missing, confirm `hmmsearch`, `hmmbuild`, and the seqres FASTA exist.
3. Run `protenix mt` only after confirming MSA search behavior and database availability.
4. If protein MSA files already exist and only templates are missing, direct API use of `run_template_search` can avoid rerunning MSA, but still requires HMMER and seqres.

## RNA MSA Databases

RNA search needs three FASTA databases:

```text
search_database/nt_rna_2023_02_23_clust_seq_id_90_cov_80_rep_seq.fasta
search_database/rfam_14_9_clust_seq_id_90_cov_80_rep_seq.fasta
search_database/rnacentral_active_seq_id_90_cov_80_linclust.fasta
```

Behavior to remember:

- RNA search uses `nhmmer`, `hmmalign`, and `hmmbuild`.
- It searches NT-RNA, Rfam, and RNAcentral, merges and deduplicates results, and writes `rna_msa.a3m`.
- `update_rna_msa_info` writes RNA results under `OUT_DIR/<task-name>/rna_msa/<sequence-index>/rna_msa.a3m` and sets `rnaSequence.unpairedMsaPath`.
- If a default database file is missing and no explicit path is supplied, Protenix may attempt to download it.

Safe recommendation order:

1. If the user has released RNA MSA data, prefer using `rna_msa/rna_sequence_to_pdb_chains.json` plus `rna_msa/msas/<entity>/<entity>_all.a3m` when it covers the sequence.
2. If the user has a custom RNA A3M, validate it and set `rnaSequence.unpairedMsaPath`.
3. Run `protenix prep` only when HMMER binaries and all RNA database FASTAs are confirmed.
4. If HMMER/database requirements cannot be met, route prediction guidance to `../../cli-and-inference/SKILL.md` and explicitly discuss the `--use_rna_msa` trade-off.

## Protein MSA Search Backends

Protein MSA generation can use Protenix mode or ColabFold-compatible mode:

```bash
protenix msa -i input.json -o msa_out -m protenix
protenix msa -i input.json -o msa_out -m colabfold
```

Both modes can be expensive. Confirm whether the backend is a remote service, a local MMseqs database, or a local ColabFold database before running.

Validation after search:

- Ensure each protein chain received valid `pairedMsaPath` and/or `unpairedMsaPath` fields.
- Run the checker on the updated JSON and generated MSA root.
- Inspect `pairing.a3m` headers for taxonomy-readable identifiers if the target is a multimer.
- Treat query-only `pairing.a3m` as a dummy paired MSA.

## ColabFold/MMseqs Preparation

ColabFold-compatible MSA generation requires external setup that this skill does not bundle:

- `colabfold_search` executable.
- `mmseqs` executable.
- ColabFold databases such as UniRef and environmental databases.
- Optional GPU/server settings depending on the local install.

The repository's ColabFold helper is reference-only. Its important knobs are:

```text
--colabsearch
--mmseqs_path
--db1
--db2
--db3
--use_env
--filter
--db_load_mode
--output_split
--gpu_server
--gpu
```

After ColabFold search, ensure output is split into Protenix directories:

```text
<results>/msa/<chain-index>/pairing.a3m
<results>/msa/<chain-index>/non_pairing.a3m
```

Do not use raw concatenated ColabFold A3M as `pairedMsaPath` unless it has already been split and the paired headers contain taxonomy-like or pseudo-taxonomy identifiers.

## Training MSA Database Preparation

Bulk training MSA preparation is a multi-stage data pipeline, not a quick inference prep step.

Reference-only source stages:

- Extract unique protein sequences from mmCIF files into sequence/index maps.
- Run raw A3M search for each unique sequence.
- Add taxonomy IDs to UniRef hits using search metadata.
- Split raw A3M files into `pairing.a3m` and `non_pairing.a3m`.
- Run template search to produce `hmmsearch.a3m` if template features are required.

Do not copy or run fixture-specific training scripts blindly. They are evidence for layout and process, not lightweight runtime utilities. Route full bioassembly/index generation and training dataset orchestration to `../../training-and-data-pipeline/SKILL.md`.

## Download Scripts as Evidence Only

Repository database scripts are useful for understanding expected filenames and data roots, but they are not safe runtime helpers:

- They can download very large datasets.
- They can generate large clustered database files.
- They may require external tools and long runtimes.
- They can mutate the user's data root.

When a user asks for database preparation, summarize required files and ask for confirmation before executing any download or generation command. Prefer validating existing files first with the bundled checker.
