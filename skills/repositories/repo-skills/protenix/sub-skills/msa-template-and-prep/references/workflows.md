# MSA, Template, RNA, and Prep Workflows

## Command Decision Table

| Need | Command | Input | Output behavior | Cost class |
| --- | --- | --- | --- | --- |
| Protein MSA only | `protenix msa -i INPUT -o OUT_DIR -m protenix` | JSON or protein FASTA | JSON input may be rewritten as `*-update-msa.json`; FASTA input returns sequence-to-MSA-directory results under `OUT_DIR`. | Expensive unless the MSA backend is confirmed available. |
| ColabFold-compatible protein MSA | `protenix msa -i INPUT -o OUT_DIR -m colabfold` | JSON or protein FASTA | Produces split MSA directories when the backend returns usable A3M files; pairing quality depends on post-processing and taxonomy-like headers. | Expensive; requires ColabFold/MMseqs/database setup or service access. |
| Protein MSA plus templates | `protenix mt -i INPUT.json -o OUT_DIR` | JSON only | Runs protein MSA if needed, writes/uses `hmmsearch.a3m`, and returns an updated JSON path. | Expensive; requires HMMER and PDB seqres FASTA. |
| Protein MSA, templates, and RNA MSA | `protenix prep -i INPUT.json -o OUT_DIR` | JSON only | Runs MSA, template search, and RNA MSA where missing; final JSON may be `*-final-updated.json`. | Expensive; requires HMMER plus template and RNA databases. |

Registered CLI command names are `msa`, `mt`, and `prep`. Do not use internal function names such as `msatemplate` or `inputprep` as CLI commands.

## Input Choice: JSON vs FASTA

Use JSON input when the user wants Protenix to update inference path fields:

```bash
protenix msa --input input.json --out_dir msa_out --msa_server_mode protenix
```

Use protein FASTA input when the user only wants MSA directories for raw protein sequences:

```bash
protenix msa --input proteins.fasta --out_dir msa_out --msa_server_mode protenix
```

JSON behavior:

- Scans each `proteinChain` for `pairedMsaPath` and `unpairedMsaPath`.
- Runs protein MSA search when both fields are missing or when a present path does not exist.
- Converts legacy `proteinChain.msa.precomputed_msa_dir` to `pairedMsaPath` and `unpairedMsaPath` when `pairing.a3m` or `non_pairing.a3m` exists.
- Writes `<input-stem>-update-msa.json` beside the input JSON when MSA paths are updated or legacy fields are converted.
- Returns the original JSON when all requested MSA paths already exist.

FASTA behavior:

- Parses protein FASTA records, sorts sequences, runs MSA search, and returns a mapping from sequence string to generated MSA directory.
- Does not author entity metadata, ligands, RNA entries, templates, or prediction JSON. Route schema authoring to `../../input-data-and-features/SKILL.md`.

## MSA Server Mode

`--msa_server_mode` accepts `protenix` and `colabfold`.

Use `protenix` mode when:

- The user wants the default Protenix MMseqs/search backend.
- Taxonomy-aware post-processing is needed for `pairing.a3m`.
- The environment or service is confirmed available and allowed.

Use `colabfold` mode when:

- The user explicitly has a ColabFold/MMseqs workflow or compatible local database.
- The user accepts that raw ColabFold output may need post-processing for Protenix pairing.
- You will validate the resulting split layout before prediction.

In `protenix` mode, post-processing can use taxonomy hit metadata to build `pairing.a3m`; without taxonomy data, the paired file may be query-only and `non_pairing.a3m` carries most usable hits.

## Protein MSA APIs

Live APIs to cite when using Python directly:

```text
runner.msa_search.update_infer_json(json_file: str, out_dir: str, use_msa: bool = True, mode: str = 'protenix') -> Tuple[str, bool]
runner.msa_search.msa_search(seqs: Sequence[str], msa_res_dir: str, mode: str = 'protenix') -> Sequence[str]
```

Generated protein MSA directories normally contain:

```text
<out-dir>/<task-name>/msa/<sequence-id>/
  pairing.a3m
  non_pairing.a3m
```

`sequence-id` is assigned from the sorted pending protein sequences, not necessarily the JSON chain order.

## Template Search Workflow

Use `protenix mt` when a protein JSON needs template information as well as MSA paths:

```bash
protenix mt --input input.json --out_dir search_out \
  --msa_server_mode protenix \
  --hmmsearch_binary_path /path/to/hmmsearch \
  --hmmbuild_binary_path /path/to/hmmbuild \
  --seqres_database_path /path/to/pdb_seqres_2022_09_28.fasta
```

Only omit binary/database flags when the environment already exposes `hmmsearch` and `hmmbuild` on `PATH` and the PDB seqres FASTA exists in the expected search database directory.

Live APIs:

```text
runner.template_search.run_template_search(msa_for_template_search_dir: Optional[str] = None, msa_for_template_search_name: Optional[str] = None, hmmsearch_binary_path: Optional[str] = None, hmmbuild_binary_path: Optional[str] = None, seqres_database_path: Optional[str] = None) -> None
runner.template_search.update_template_info(json_data: list[dict[str, Any]], hmmsearch_binary_path: Optional[str] = None, hmmbuild_binary_path: Optional[str] = None, seqres_database_path: Optional[str] = None) -> bool
```

Template behavior:

- `run_template_search` expects a directory containing `pairing.a3m` and/or `non_pairing.a3m` plus comma-separated base names such as `pairing,non_pairing`.
- It concatenates those A3M inputs, builds an HMM profile, searches the PDB seqres database, and writes `hmmsearch.a3m` in the same directory.
- `update_template_info` skips protein chains whose `templatesPath` already exists.
- When `templatesPath` is missing or stale, it infers the MSA directory from `pairedMsaPath` or `unpairedMsaPath`, runs template search if needed, and sets `templatesPath` to `hmmsearch.a3m`.
- If no explicit database path is supplied and the default database is missing, Protenix may attempt a download; confirm network and storage permission first.

## Full Prep Workflow

Use `protenix prep` when the JSON may need protein MSA, templates, and RNA MSA in one pass:

```bash
protenix prep --input input.json --out_dir search_out \
  --msa_server_mode protenix \
  --hmmsearch_binary_path /path/to/hmmsearch \
  --hmmbuild_binary_path /path/to/hmmbuild \
  --seqres_database_path /path/to/pdb_seqres_2022_09_28.fasta \
  --nhmmer_binary_path /path/to/nhmmer \
  --hmmalign_binary_path /path/to/hmmalign \
  --hmmbuild_rna_binary_path /path/to/hmmbuild \
  --ntrna_database_path /path/to/nt_rna_2023_02_23_clust_seq_id_90_cov_80_rep_seq.fasta \
  --rfam_database_path /path/to/rfam_14_9_clust_seq_id_90_cov_80_rep_seq.fasta \
  --rna_central_database_path /path/to/rnacentral_active_seq_id_90_cov_80_linclust.fasta \
  --nhmmer_n_cpu 8
```

Live API:

```text
runner.batch_inference.preprocess_input(input_json: str, out_dir: str, use_msa: bool = True, use_template: bool = False, use_rna_msa: bool = False, msa_server_mode: str = 'protenix', hmmsearch_binary_path: Optional[str] = None, hmmbuild_binary_path: Optional[str] = None, seqres_database_path: Optional[str] = None, nhmmer_binary_path: Optional[str] = None, hmmalign_binary_path: Optional[str] = None, hmmbuild_rna_binary_path: Optional[str] = None, ntrna_database_path: Optional[str] = None, rfam_database_path: Optional[str] = None, rna_central_database_path: Optional[str] = None, nhmmer_n_cpu: Optional[int] = None) -> str
```

`preprocess_input` runs stages in this order:

1. Protein MSA via `update_infer_json`.
2. Template search via `update_template_info` when `use_template=True`.
3. RNA MSA via `update_rna_msa_info` when `use_rna_msa=True`.

JSON suffix rules:

- Protein MSA update or legacy conversion writes `<input-stem>-update-msa.json` beside the original input JSON.
- Template or RNA updates write `<input-stem>-final-updated.json`.
- If the intermediate name already contains `-update-msa`, Protenix replaces that suffix with `-final-updated`.
- If no requested stage changes paths, the most recent JSON path is returned unchanged.

## RNA MSA Workflow

Use RNA MSA search only when an `rnaSequence` lacks a valid `unpairedMsaPath` and the user accepts the HMMER/database requirements.

Live API:

```text
runner.rna_msa_search.update_rna_msa_info(json_data: list[dict[str, Any]], out_dir: str, nhmmer_binary_path: Optional[str] = None, hmmalign_binary_path: Optional[str] = None, hmmbuild_binary_path: Optional[str] = None, ntrna_database_path: Optional[str] = None, rfam_database_path: Optional[str] = None, rna_central_database_path: Optional[str] = None, nhmmer_n_cpu: Optional[int] = None) -> bool
```

Behavior:

- Existing valid `rnaSequence.unpairedMsaPath` is respected.
- Missing RNA MSA is searched under `OUT_DIR/<task-name>/rna_msa/<sequence-index>/rna_msa.a3m`.
- RNA search requires `nhmmer`, `hmmalign`, and `hmmbuild`.
- The default databases are NT-RNA, Rfam, and RNAcentral FASTA files under the search database directory.
- If a database is missing and no explicit path is supplied, Protenix may attempt to download it.

## ColabFold-Compatible MSA

Raw ColabFold output is not always enough for Protenix pairing because Protenix pairing logic needs species/taxonomy cues in paired headers. Treat repository ColabFold helpers as reference-only because they shell out to `colabfold_search`, require MMseqs and large ColabFold databases, and may use database-specific options.

Distilled conversion behavior:

- Required positional inputs are a query FASTA, ColabFold database directory, and results directory.
- Important options include `--colabsearch`, `--mmseqs_path`, `--db1`, `--db2`, `--db3`, `--use_env`, `--filter`, `--db_load_mode`, `--output_split`, `--gpu_server`, and `--gpu`.
- Multimer FASTA entries may use ColabFold colon-separated chains.
- Single-chain post-processing can write `non_pairing.a3m` with raw hits plus query-only `pairing.a3m`.
- Multimer post-processing splits concatenated alignments by chain and writes per-chain `pairing.a3m` headers shaped like `UniRef100_<hit>_<pseudo-taxonomy-id>`.

Validation rules:

- Do not point `pairedMsaPath` directly at raw ColabFold output unless it has already been transformed into a per-chain Protenix `pairing.a3m` file.
- Inspect headers after `>query`; taxonomy-readable patterns are required for meaningful multimer pairing.
- If no taxonomy or pseudo-taxonomy is recoverable, warn that the paired MSA is effectively dummy and multimer accuracy may degrade.

## Training MSA Pipeline

Training MSA layout is not the same as one-off inference JSON path filling. For training, Protenix expects sequence-indexed MSA directories and a sequence-to-index mapping.

Distilled stages from repository scripts:

1. Extract unique protein sequences from mmCIF files.
   - Output concepts: `pdb_seq.fasta`, `seq_to_pdb_index.json`, `seq_to_pdb_id_entity_id.json`, and `pdb_index_to_seq.json`.
   - `seq_to_pdb_index.json` maps each exact protein sequence to an integer directory id.
2. Run raw A3M search for each unique sequence.
   - Raw results are index-named `.a3m` files plus taxonomy hit metadata such as `uniref_tax.m8` when available.
   - This is database-heavy and should not be run blindly.
3. Append taxonomy IDs to UniRef headers.
   - Headers are rewritten into patterns like `UniRef100_<hit>_<taxid>/` when a hit taxid is found.
4. Split into final Protenix layout.
   - UniRef100 hits go to `pairing.a3m`; other hits go to `non_pairing.a3m`.
   - Final directories are integer ids under `mmcif_msa_template/<index>/`.
5. Add template search output when template features are expected.
   - `hmmsearch.a3m` lives beside `pairing.a3m` and `non_pairing.a3m`.

Route full training bioassembly/index generation to `../../training-and-data-pipeline/SKILL.md`; keep this sub-skill focused on MSA/search/template/RNA layout and validation.

## Bundled Runtime Tooling

Runtime files include only the read-only layout checker in `scripts/check_msa_template_layout.py`. Use it to inspect already-produced JSON, MSA, template, and RNA MSA paths before deciding whether an expensive search should be launched by the user.

Bulk search launchers and database generators are intentionally distilled into the workflow guidance here instead of copied as runnable skill scripts, because they require external binaries, network/database access, large intermediate files, and user-selected data roots.
