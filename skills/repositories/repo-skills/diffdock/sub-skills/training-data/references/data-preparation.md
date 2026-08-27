# Data Preparation

DiffDock training expects prepared local datasets plus split files. This reference gives planning and validation guidance without requiring future agents to open source repository files.

## Dataset Families

| Dataset family | Typical root | Primary use | Notes |
| --- | --- | --- | --- |
| PDBBind | `data/PDBBind_processed` | Score training, validation, evaluation | Each complex id is a directory containing `<id>_protein_processed.pdb` or `<id>_protein.pdb` and ligand files. |
| BindingMOAD | `data/BindingMOAD_2020_processed` | MOAD/DockGen-style score training and generalization | Requires MOAD metadata such as `new_cluster_to_ligands.pkl` and repository split metadata. |
| DockGen | BindingMOAD root for DiffDock-L evaluation; optional separate `DockGen` processed data | Generalization/evaluation planning | README guidance says DiffDock-L evaluation in this repo should use BindingMOAD data directly. |
| PoseBusters | `data/posebusters_benchmark_set` | Evaluation and dataset-layout checks | Uses PDBBind-like complex subdirectories; evaluation commonly uses `protein` and `ligands` file stems. |
| van der Mers / sidechain | `data/pdb_2021aug02_sample` or full processed PDB 2021 data | Sidechain/chemical-group training | Requires `list.csv`, cluster split files, preprocessed `.pt` chains, and optional sidechain ESM indexes. |

Dataset downloads are large. The README describes placing processed PDBBind, BindingMOAD, DockGen, PoseBusters, and van der Mers data under `data/`; this skill preserves the expected relative layouts but does not download or preprocess them.

## Split Files

Known split files include:

- `data/splits/timesplit_no_lig_overlap_train`
- `data/splits/timesplit_no_lig_overlap_val`
- `data/splits/timesplit_test`
- `data/splits/timesplit_test_no_rec_overlap`
- `data/splits/timesplit_val_filter`
- `data/splits/posebusters_benchmark_set_ids.txt`
- `data/splits/MOAD_generalisation_splits.pkl`
- `data/splits/self_distillation_splits.pkl`
- `data/splits/pdbids_2019`

Plain text PDBBind/PoseBusters split files contain one complex id per line. MOAD split metadata is pickle-backed and is read by MOAD dataset code; validate its presence, but do not unpickle unknown files unless the user approves the trust boundary.

## PDBBind Layout

For each id in a PDBBind split, the loader expects a directory under `--pdbbind_dir` with at least:

```text
<id>/
  <id>_protein_processed.pdb   # default protein stem is protein_processed
  <id>_ligand.sdf              # or another RDKit-readable ligand file
```

If `<id>_protein_processed.pdb` is unavailable, ESM sequence-preparation code falls back to `<id>_protein.pdb`, but training parser defaults still use `--protein_file protein_processed`. Use `--protein_file protein` only when the processed stem is not present and the model plan accepts that change.

For PoseBusters-style data, the PDBBind dataset class can use non-default stems, such as `--protein_file protein` and `--ligand_file ligands`, matching evaluation guidance.

## BindingMOAD / DockGen Layout

BindingMOAD training uses `--dataset moad` and `--moad_dir`. The MOAD dataset code expects:

- A processed MOAD root with receptor/ligand files and `new_cluster_to_ligands.pkl`.
- `data/splits/MOAD_generalisation_splits.pkl` for cluster splits.
- Optional `data/splits/pdbids_2019` when enforcing a timesplit.
- Optional ESM paths plus a sequence mapping file when using precomputed MOAD embeddings.

`--split_train` and `--split_val` are still parser flags, but MOAD training primarily reads cluster splits from MOAD metadata rather than plain PDBBind id lists.

## Sidechain / van der Mers Layout

Sidechain training uses `--dataset pdbsidechain` and `--pdbsidechain_dir`. The sidechain dataset expects:

- `list.csv` with at least `CHAINID` and `CLUSTER` columns.
- `valid_clusters.txt` and `test_clusters.txt` in the sidechain root.
- Chain tensors under a nested `pdb/` directory, with paths derived from chain ids.
- Optional sidechain ESM embeddings plus sequence mapping files.

Sidechain/van der Mers preprocessing is heavy because it builds protein graphs, computes valid contact counts, and writes pickle caches.

## CSV Schema Notes

`data/protein_ligand_example.csv` for inference uses:

```text
complex_name,protein_path,ligand_description,protein_sequence
```

Training/evaluation `data/testset_csv.csv` uses a simpler schema:

```text
,protein_path,ligand
```

Do not substitute inference CSVs directly for training split files. Training split files name complexes; dataset roots then supply protein and ligand files for each complex id.

## ESM Embedding Preparation

DiffDock's cached ESM2 workflow has four contracts. Treat the original repository ESM-preparation and conversion files as evidence for these contracts, not as runtime skill dependencies:

1. A local sequence-preparation step must produce either a FASTA file or a sequence-id mapping from the prepared protein structures.
2. An external ESM environment must run the `esm2_t33_650M_UR50D` model with representation layer 33, `per_tok` output, and truncation length 4096.
3. The generated per-sequence `.pt` files must be copied into the active DiffDock data area.
4. The per-sequence outputs must be converted into an aggregate DiffDock `.pt` mapping before training consumes them.

The aggregate mapping stores dictionary keys derived from embedding file stems and values taken from `['representations'][33]`. PDBBind training expects keys like `<complex>_chain_<index>`. MOAD ESM use also needs a sequence mapping file for sequence-to-embedding lookup. Sidechain conversion has separate sequence-id assumptions.

Use [scripts/validate_esm_embedding_index.py](../scripts/validate_esm_embedding_index.py) before training to check for obvious missing or mismatched keys without loading Torch by default. Ask for explicit approval before running sequence extraction, external ESM inference, aggregate `.pt` conversion, or any large embedding copy.

## Cache Behavior

Training can create graph caches automatically when expected pickle files are missing. Cache paths encode dataset options, so changing data/model geometry often changes the cache directory. Important inputs include:

- Base `--cache_path`.
- Dataset type and split id.
- `--limit_complexes`.
- Torsion/no-torsion and number of conformers.
- `--all_atoms`, `--atom_radius`, and `--atom_max_neighbors`.
- `--receptor_radius`, `--c_alpha_max_neighbors`, and chain cutoff.
- `--max_lig_size`, hydrogen removal, and ligand matching settings.
- ESM embedding presence.
- Protein file stem, KNN/radius-graph settings, and miscellaneous atom inclusion.

Confidence training has an additional cache layer for generated ligand positions and RMSDs. It can reuse the original score-model graph cache or create graphs from confidence-training dataset flags when `--use_original_model_cache` is omitted or changed.

## Validation Workflow

Before requesting a heavy run:

1. Validate root directories and split files:

   ```bash
   python sub-skills/training-data/scripts/validate_dataset_layout.py --dataset-type pdbbind --dataset-root data/PDBBind_processed --split-path data/splits/timesplit_no_lig_overlap_train --max-complexes 20
   ```

2. Validate ESM presence and key shape expectations:

   ```bash
   python sub-skills/training-data/scripts/validate_esm_embedding_index.py data/esm2_embeddings.pt --expect-ids data/splits/timesplit_no_lig_overlap_train
   ```

3. Build the planned command without running it:

   ```bash
   python sub-skills/training-data/scripts/build_training_command.py --mode score --dataset pdbbind --data-dir data/PDBBind_processed --split-train data/splits/timesplit_no_lig_overlap_train --split-val data/splits/timesplit_no_lig_overlap_val --limit-complexes 8 --n-epochs 1 --batch-size 2
   ```

4. Ask for approval before running training, confidence cache generation, full graph preprocessing, or external ESM extraction.
