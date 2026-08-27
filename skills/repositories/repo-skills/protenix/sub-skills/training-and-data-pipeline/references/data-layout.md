# Protenix Training Data Layout

## Data Root Contract

Protenix training and fine-tuning resolve released dataset paths from a `PROTENIX_ROOT_DIR`-style root. The data config reads `PROTENIX_ROOT_DIR` and falls back to the user's home directory when it is unset, so future agents should set the variable explicitly before training, downloading data, preprocessing, template search, or RNA MSA search.

A training-capable released data root should contain:

- `common/`: shared metadata and caches: `components.cif`, `components.cif.rdkit_mol.pkl`, `clusters-by-entity-40.txt`, `obsolete_release_date.csv`, `obsolete_to_successor.json`, `release_date_cache.json`, and `seq_to_pdb_index.json`.
- `search_database/`: sequence/template/RNA search databases such as PDB seqres, NT-RNA, Rfam, and RNAcentral FASTA files.
- `indices/`: train/evaluation index files, including weighted PDB CSV.GZ files, recentPDB CSV/TXT files, and posebusters CSV files.
- `mmcif/`: raw wwPDB mmCIF files and template-search source structures.
- `mmcif_bioassembly/`: preprocessed weighted PDB bioassembly `.pkl.gz` files used by training.
- `mmcif_msa_template/`: per-sequence directories used by training MSA/template featurizers.
- `rna_msa/`: RNA MSA data with `msas/` and `rna_sequence_to_pdb_chains.json`.
- Optional evaluation components: `posebusters_mmcif/`, `posebusters_bioassembly/`, and `recentPDB_bioassembly/`.

Use `scripts/check_training_data_layout.py DATA_ROOT` for training/fine-tuning roots, and pass `--index-csv INDEX.csv` when checking generated index schemas.

## Released Download Modes

The repository data downloader is reference-only from this skill because it performs network downloads, archive extraction, and deletion of downloaded archives under the chosen data root.

The documented modes are:

- `--inference_only`: downloads inference/search support such as `common` and `search_database`; this is not enough for training.
- `--full`: downloads training and fine-tuning components including `indices`, `mmcif`, `mmcif_bioassembly`, `mmcif_msa_template`, `rna_msa`, posebusters/recentPDB bioassemblies, and search databases.

The downloader requires `PROTENIX_ROOT_DIR` and supports data versions `2024.05.22` and `2026.01.01`. Align the data version with the selected model and dataset names; for example, the 2026-era weighted PDB dataset names should be paired with the matching 2026 data release.

Do not suggest full-data mode as a quick fix. Repository docs call out terabyte-scale storage for full training data, and a failed retry can duplicate partial archives and extracted directories.

## MSA and Template Layout

Training data loading expects protein MSA/template configuration under the data root:

- `common/seq_to_pdb_index.json`: maps unique protein sequences to integer directory IDs.
- `mmcif_msa_template/<index>/pairing.a3m`: paired protein MSAs with taxonomy IDs.
- `mmcif_msa_template/<index>/non_pairing.a3m`: unpaired MSAs.
- `mmcif_msa_template/<index>/hmmsearch.a3m`: template search results.
- `mmcif/`: template structures used by template featurization.
- `common/release_date_cache.json` and `common/obsolete_to_successor.json`: template date and obsolescence metadata.

If a task asks how to generate these files, route the search and post-processing mechanics to `../../msa-template-and-prep/SKILL.md`. This sub-skill only uses the layout to plan training roots and diagnose missing files.

## RNA MSA Layout

Training data config also enables RNA MSA data by default. A released or compatible RNA MSA root includes:

- `rna_msa/rna_sequence_to_pdb_chains.json`: maps RNA sequences to PDB/entity IDs.
- `rna_msa/msas/<pdb_entity_id>/<pdb_entity_id>_all.a3m`: RNA MSA files.

RNA MSA searches require large databases and HMMER tools. Use this sub-skill to check whether the directory exists; route search execution details to `../../msa-template-and-prep/SKILL.md`.

## CCD and Cluster Files

`common/components.cif` and `common/components.cif.rdkit_mol.pkl` are used for ligand and chemical component handling during preprocessing and training. `common/clusters-by-entity-40.txt` provides protein clustering data used by released weighted PDB-style sampling.

If custom structures include newer or custom CCD codes, plan a CCD refresh only after the user approves network, CPU, and destination changes. The CCD updater is reference-only in this skill because it can download and overwrite cache files.

## Dataset Names and Expected Paths

Important released dataset configs include:

- `weightedPDB_before2109_wopb_nometalc_0925`: uses `mmcif/`, `mmcif_bioassembly/`, and `indices/weightedPDB_indices_before_2021-09-30_wo_posebusters_resolution_below_9.csv.gz`.
- `weightedPDB_before250701_v20260101`: uses 2026 release paths under `mmcif/`, `mmcif_bioassembly/`, and 2026 index files.
- `weightedPDB_before210930_v20260101`: uses the 2026 data layout with a 2021-09-30 cutoff index.
- `recentPDB_1536_sample384_0925`: uses `recentPDB_bioassembly/`, `indices/recentPDB_low_homology_maxtoken1536.csv`, and `indices/recentPDB_low_homology_maxtoken1024_sample384_pdb_id.txt`.
- `posebusters_0925`: uses `posebusters_mmcif/`, `posebusters_bioassembly/`, and `indices/posebusters_indices_mainchain_interface.csv`.

When fine-tuning on a custom subset of released data, prefer a `base_info.pdb_list` override before changing dataset code. When using custom bioassemblies and index CSVs, also override `base_info.indices_fpath`, `base_info.bioassembly_dict_dir`, and usually `base_info.mmcif_dir`.

## Read-Only Layout Check

Use the bundled checker before training, fine-tuning, or custom-data debugging:

```bash
python scripts/check_training_data_layout.py DATA_ROOT --index-csv DATA_ROOT/indices/your_indices.csv
```

Useful options:

- Positional `DATA_ROOT`: checks expected root directories such as `common`, `indices`, `mmcif`, `mmcif_bioassembly`, `mmcif_msa_template`, and `search_database`.
- `--index-csv INDEX.csv`: validates required index columns for one generated or released index CSV; may be repeated.
- `--json`: emits machine-readable diagnostics.

The checker does not import Protenix, inspect GPUs, open network connections, unpickle bioassembly files, or modify files.
