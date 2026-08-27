# Custom Training Data Preprocessing

## When to Use This Workflow

Use this reference when the user has custom CIF or CIF.GZ structures and wants Protenix-compatible training/fine-tuning data. The preprocessing workflow converts CIF files into bioassembly `.pkl.gz` files and an index CSV that the training dataloader can sample.

Do not run preprocessing automatically. It imports Protenix and data dependencies, opens input structures, writes output files, can use many CPU workers, and may fail on malformed CIF or missing CCD entries.

## No-Run Command Builder

Use the bundled builder to create a command for review:

```bash
python scripts/build_prepare_training_data_command.py \
  --input INPUT_CIF_DIR_OR_LIST.txt \
  --output-csv OUTPUT_INDICES.csv \
  --bioassembly-dir BIOASSEMBLY_OUTPUT_DIR \
  --cluster-file CLUSTERS_BY_ENTITY_40.txt \
  --workers 8
```

For model-generated, custom, or already-normalized CIFs where weighted PDB filters and Assembly 1 expansion are not desired, add `--distillation`.

The builder prints a command and warnings only. It does not import Protenix, read CIF contents, create output directories, update CCD files, or launch preprocessing.

## Actual Preprocessing Command Anatomy

The underlying command shape is:

```bash
python -m scripts.prepare_training_data \
  -i INPUT_CIF_DIR_OR_LIST.txt \
  -o OUTPUT_INDICES.csv \
  -b BIOASSEMBLY_OUTPUT_DIR \
  -c CLUSTERS_BY_ENTITY_40.txt \
  -n NUM_WORKERS
```

Arguments:

- `-i` / `--input_path`: a directory containing top-level `*.cif` or `*.cif.gz`, or a `.txt` file with one CIF path per line.
- `-o` / `--output_csv`: generated index CSV path.
- `-b` / `--bio_output_dir`: output directory for generated `[pdb_id].pkl.gz` bioassembly dictionaries.
- `-c` / `--cluster_file`: optional protein clustering file where each line contains `[PDB ID]_[Entity ID]` entries in one 40 percent identity cluster.
- `-d` / `--distillation`: uses the Distillation parser/setting.
- `-n` / `--n_cpu`: worker process count.

If a cluster file is unavailable, preprocessing can be planned without it, but sampling metadata and cluster diversity can be weaker than with a compatible cluster file.

## WeightedPDB vs Distillation Mode

Without `-d`, preprocessing targets RCSB/WeightedPDB-style input and applies filters documented by the repository:

- Removes water molecules and hydrogens.
- Drops all-unknown polymer chains and chains with no resolved residues.
- Removes chains where adjacent numbered C-alpha distances exceed 10 angstroms.
- Removes elements labeled `X`.
- Reduces very large complexes by retaining interface-capable or nearby chains within documented limits.
- Removes chains with excessive heavy-atom collisions.
- Expands/handles structures in the weighted PDB training style.

With `-d`, preprocessing uses the Distillation setting. Use it for model-generated or custom CIFs where those WeightedPDB filters and Assembly 1 expansion are not desired.

## Output Bioassembly Schema

Each successfully processed CIF produces `[pdb_id].pkl.gz` under the bioassembly output directory. The payload is a pickled dictionary used by the data pipeline, with keys including:

- `pdb_id`: PDB or sample code.
- `assembly_id`: assembly identifier.
- `sequences`: mapping from polymer `label_entity_id` to canonical sequence.
- `release_date`: source release date.
- `num_assembly_polymer_chains`: assembly polymer-chain count.
- `num_prot_chains`: protein-chain count.
- `entity_poly_type`: mapping from polymer `label_entity_id` to `entity_poly.type`.
- `resolution`: float resolution, with `-1` when absent.
- `num_tokens`: token count.
- `atom_array`: processed structural atom array.
- `token_array`: tokenized structural representation.
- `msa_features`: placeholder, typically `None` for preprocessing output.
- `template_features`: placeholder, typically `None` for preprocessing output.

The bundled layout checker performs only shallow path and index checks; it intentionally does not unpickle bioassembly payloads.

## Index CSV Schema

Required columns for custom training CSVs are:

- Common row fields: `type`, `pdb_id`, `cluster_id`.
- First side: `entity_1_id`, `chain_1_id`, `mol_1_type`, `cluster_1_id`.
- Second side: `entity_2_id`, `chain_2_id`, `mol_2_type`, `cluster_2_id`.

Optional but useful columns include `assembly_id`, `release_date`, `resolution`, `num_tokens`, `num_prot_chains`, `eval_type`, `sub_mol_1_type`, and `sub_mol_2_type`.

For `type=chain`, the second-side columns should still exist but be empty. For `type=interface`, both sides should identify the interface members. Molecular type values used in the data pipeline include `protein`, `nuc`, `ligand`, and `ions`.

Validate the generated CSV before planning training:

```bash
python scripts/check_training_data_layout.py DATA_ROOT --index-csv OUTPUT_INDICES.csv
```

## Wiring Custom Outputs Into Training

A low-risk fine-tune on a small custom dataset usually needs:

- `PROTENIX_ROOT_DIR` set to a data root containing shared `common/`, MSA/template, and CCD files.
- `--data.train_sets DATASET_NAME` where the selected dataset's sampler/cropping assumptions fit the custom data.
- `--data.DATASET_NAME.base_info.indices_fpath OUTPUT_INDICES.csv`.
- `--data.DATASET_NAME.base_info.bioassembly_dict_dir BIOASSEMBLY_OUTPUT_DIR`.
- `--data.DATASET_NAME.base_info.mmcif_dir INPUT_OR_RELEASED_MMCIF_DIR` when template/source mmCIF paths are needed.
- Optional `--data.DATASET_NAME.base_info.pdb_list SUBSET.txt` for a released-data subset.

If the custom data semantics differ substantially from released WeightedPDB sampling, ask for or implement a project-specific dataset config rather than forcing every override into an existing dataset name.

## CCD Cache Handling

Protenix first looks for CCD files under the data root's `common/` directory:

- `common/components.cif`
- `common/components.cif.rdkit_mol.pkl`

Custom or newly released structures can contain CCD codes missing from an older cache. The CCD updater can download the latest Chemical Component Dictionary and precompute RDKit molecule objects, producing `components.cif`, `components.cif.rdkit_mol.pkl`, and `components.txt`.

Keep CCD refresh reference-only unless the user approves network, CPU, and destination changes. If the user already has a `components.cif`, the updater can be planned with a download-skip mode that processes the existing file, but it still writes cache outputs.

## Malformed CIF and Empty Output Handling

Preprocessing catches many per-file exceptions and can return no sample indices for a bad structure. After a run, check:

- The output CSV exists and has data rows.
- Required columns are present.
- The bioassembly directory contains `.pkl.gz` files whose names match sampled `pdb_id` values.
- Warning logs identify malformed CIFs, parser failures, or structures filtered to empty.
- Custom ligand failures are not actually missing CCD-cache failures.

Do not treat an empty CSV as a successful small dataset; it means filtering, parsing, input selection, or CCD handling must be revisited.
