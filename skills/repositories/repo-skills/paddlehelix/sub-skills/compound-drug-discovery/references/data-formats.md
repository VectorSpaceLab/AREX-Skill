# Compound Data, Config, and Checkpoint Formats

Use this reference to validate local files before planning PaddleHelix compound/drug-discovery runs. The bundled script `../scripts/validate_compound_inputs.py` checks common SMILES, JSON, and directory layouts safely.

## Compound Property and Pretraining Data

### Generic SMILES Files

Expected format:

- One molecule per non-empty line, usually canonical or raw SMILES.
- Optional whitespace-separated columns are allowed by many scripts; the first token should be the SMILES string.
- Comment/header handling differs by app. For preflight checks, treat lines beginning with `#` as comments and treat a first-row `smiles` header as a header.

Validation focus:

- Empty files, duplicate accidental headers, whitespace-only rows, and obviously invalid characters.
- Optional RDKit parseability when RDKit is installed.
- Maximum sequence length if the downstream model config has `max_length`, `drug_max_seq`, or similar fields.

### PretrainGNNs

Pretraining data roots:

```text
data/chem_dataset/
├── zinc_standard_agent/        # node-level attribute masking data
├── chembl_filtered/            # graph-level supervised data
└── tox21/ or other downstream MoleculeNet task folders
```

Config/checkpoint expectations:

- Compound encoder config JSON: fields commonly include `atom_names`, `bond_names`, `gnn_type`, `hidden_size`, `embed_dim`, `layer_num`, `dropout_rate`, residual/norm options, and pooling.
- Node-level model config: `mask_ratio` and attrmask-specific output settings.
- Supervised/downstream model config: task counts are usually injected by code from dataset metadata.
- Init checkpoint: `compound_encoder.pdparams` from a prior pretraining epoch.
- Output checkpoint layout: `model_dir/epoch<N>/compound_encoder.pdparams` and `model_dir/epoch<N>/model.pdparams`.

Common issues:

- `data_path` points to the parent archive instead of the unpacked dataset folder.
- Scaffold split or molecule featurization fails because RDKit is missing or a `smiles` field is absent.
- Downstream task names do not match the selected dataset directory.

### GEM / GeoGNN

Input expectations:

- A SMILES source path accepted by the app, often a folder of SMILES files for ZINC-like data.
- RDKit must be able to parse molecules and generate geometry-related features; MMFF optimization can be slow.

Config/checkpoint expectations:

- Compound encoder config keys: `atom_names`, `bond_names`, `bond_float_names`, `bond_angle_float_names`, and geometry GNN size/depth fields.
- Pretrain model config keys: `pretrain_tasks`, `mask_ratio`, and task-specific vocabulary/label settings such as `Cm_vocab`.
- Downstream config keys: prediction head style and task settings.
- Output: epoch `.pdparams` checkpoints and downstream final result files.

Common issues:

- A molecule parses as 2D SMILES but fails 3D conformer/MMFF optimization.
- `bond_angle_float_names` or pretrain tasks in config do not match the featurizer used by the script.
- Running all downstream datasets can take one to two days on a single V100-class GPU.

### GEM-2

Dataset/config expectations:

- Dataset config: `data_dir` points to PCQM4Mv2 or processed GEM-2 data; `task_names` identifies label columns such as HOMO-LUMO gap labels.
- Model config: nested model/data settings for channels, dropout, many-body track structure, and transforms.
- Train config: `lr`, `warmup_step`, and decay/EMA fields.
- Checkpoint: `.pdparams` model file for inference or initialization.

Common issues:

- PCQM4Mv2 raw archive is present but processed RDKit-generated 3D data are missing.
- Batch size and GPU count are copied from publication-scale examples without matching available hardware.

### InfoGraph

Expected layout after preprocessing:

```text
data/
├── mutag/
│   ├── raw/
│   │   ├── mutag_188_data.can
│   │   └── mutag_188_target.txt
│   └── processed/
│       ├── data.npz
│       └── smiles.txt
└── ptc_mr/
    ├── raw/
    │   ├── ptc_MR_data.can
    │   └── ptc_MR_target.txt
    └── processed/
        ├── data.npz
        └── smiles.txt
```

Validation focus:

- Raw `.can` and target files exist before preprocessing.
- `processed/data.npz` and `processed/smiles.txt` exist before unsupervised pretraining.
- Config JSON includes atom and bond feature names used by the collate functions.

## Drug-Target Interaction Data

### GraphDTA Davis/Kiba

Expected root for each dataset:

```text
data/davis/ or data/kiba/
├── folds/
│   ├── train_fold_setting1.txt
│   └── test_fold_setting1.txt
├── ligands_can.txt
├── proteins.txt
├── Y
└── processed/
    ├── train/
    │   └── <dataset>_train.npz
    └── test/
        └── <dataset>_test.npz
```

Config expectations:

```json
{
  "compound": {
    "atom_names": ["atomic_num", "chiral_tag"],
    "bond_names": ["bond_dir", "bond_type"],
    "gnn_type": "gin",
    "embed_dim": 32,
    "layer_num": 5,
    "hidden_size": 32,
    "output_dim": 128
  },
  "protein": {
    "max_protein_len": 1000,
    "embed_dim": 128,
    "num_filters": 32,
    "output_dim": 128
  },
  "dropout_rate": 0.2
}
```

Validation focus:

- Raw metadata files exist before preprocessing.
- Processed NPZ train/test directories exist before training.
- Kiba commands include `--use_kiba_label`; Davis commands usually do not.
- `model_config` path points to a JSON file, not a directory.

### MolTrans Classification

Expected layout:

```text
dataset/classification/
├── DAVIS/
│   ├── train.csv
│   ├── val.csv
│   └── test.csv
├── BindingDB/
│   ├── train.csv
│   ├── val.csv
│   └── test.csv
└── BIOSNAP/
    ├── full_data/{train.csv,val.csv,test.csv}
    ├── unseen_drug/{train.csv,val.csv,test.csv}
    ├── unseen_protein/{train.csv,val.csv,test.csv}
    └── missing_data/...       # missingness-specific splits
```

CSV expectations:

- Each split must contain drug, target/protein, and label columns recognizable by the MolTrans loader.
- Practical column names vary by dataset; inspect headers and ensure they represent drug SMILES/substructure text, protein sequence, and interaction label.
- `train_cls.py --dataset` accepts `cls_davis`, `cls_biosnap`, or `cls_bindingdb`.

### MolTrans Regression

Expected layout:

```text
dataset/regression/
├── DAVIS/{affinity.txt,SMILES.txt,target_seq.txt}
├── KIBA/{affinity.txt,SMILES.txt,target_seq.txt}
├── BindingDB/
│   ├── BindingDB_Kd.txt
│   ├── BindingDB_SMILES.txt
│   ├── BindingDB_SMILES_new.txt
│   ├── BindingDB_Target_Sequence.txt
│   └── BindingDB_Target_Sequence_new.txt
├── ChEMBL/
│   ├── Chem_Affinity.txt
│   ├── Chem_Kd_nM.txt
│   ├── Chem_SMILES.txt
│   ├── Chem_SMILES_only.txt
│   └── ChEMBL_Target_Sequence.txt
└── benchmark/{DAVIStest,KIBAtest}
```

Allowed `train_reg.py --dataset` values include `raw_chembl_pkd`, `raw_chembl_kd`, `raw_bindingdb_kd`, `raw_davis`, `raw_kiba`, `benchmark_davis`, and `benchmark_kiba`.

MolTrans model config keys:

```json
{
  "drug_max_seq": 50,
  "target_max_seq": 545,
  "emb_size": 384,
  "input_drug_dim": 23532,
  "input_target_dim": 16693,
  "interm_size": 1536,
  "num_attention_heads": 12,
  "flatten_dim": 81750,
  "layer_size": 2,
  "dropout_ratio": 0.1,
  "attention_dropout_ratio": 0.1,
  "hidden_dropout_ratio": 0.1
}
```

Validation focus:

- Classification/regression dataset names align with the script selected.
- `config.json` parses and contains all sequence/vocabulary/dimension keys above.
- CSV/text split files are not empty and have consistent row counts for paired drug/target/label files.

### SIGN / SMAN / GIANT PDBbind-Style Data

Expected data concepts:

- Raw PDBbind or CSAR complexes contain protein-ligand structure files that may require conversion to MOL2 or graph feature extraction.
- Preprocessed data contain protein-ligand graphs, atom/bond/spatial features, and train/test/validation split names based on `dataset`.
- `cutoff` or `cut_dist` controls atom-distance thresholds, commonly `5`.

Validation focus:

- Raw structure files exist before preprocessing.
- Preprocessed train/test/val files exist before training.
- OpenBabel is present only if preprocessing/conversion is requested.
- `--cuda -1` or CPU-equivalent behavior is supported for SIGN/GIANT, while older SMAN code uses Paddle static graph APIs and may require compatible Paddle/PGL versions.

### BatchDTA

Expected data concepts:

- Processed data directory under the BatchDTA app contains Davis/KIBA cross-validation splits and BindingDB subsets.
- Pairwise methods may expand examples substantially; confirm storage and GPU/distributed requirements before running.
- BatchDTA mixes Torch and Paddle dependencies depending on backbone and pairwise/pointwise mode.

Validation focus:

- `--data_path` points to unpacked `Data` or processed data root, not the zip archive.
- `--dataset` value matches `DAVIS`, `KIBA`, or BindingDB-mode scripts.
- Distributed launch commands are approved and available before using `torch.distributed.launch`.

## Molecular Generation Data

### JT-VAE

Expected layout:

```text
data/zinc/
├── 250k_rndm_zinc_drugs_clean_sorted.smi
└── vocab.txt

zinc_processed/
├── ... processed split shards ...

vae_models/
└── model.iter-<step>
```

Config keys:

- `hidden_size`, `latent_size`, `depthT`, `depthG`.
- Optimization and KL schedule: `lr`, `clip_norm`, `beta`, `step_beta`, `max_beta`, `warmup`, `anneal_rate`, `anneal_iter`, `kl_anneal_iter`.
- Logging/checkpoint cadence: `print_iter`, `save_iter`.

Validation focus:

- SMILES file exists and has parseable first-token SMILES lines.
- Vocabulary file exists before training/sampling.
- `--model` checkpoint exists before sampling.
- `--output` parent directory is writable.

### SD-VAE

Expected layout:

```text
data/data_SD_VAE/
├── context_free_grammars/
│   └── mol_zinc.grammar
└── zinc/
    └── 250k_rndm_zinc_drugs_clean.smi

model/
└── train_model_epoch499
```

Config keys:

- `latent_dim`, `max_decode_steps`, `eps_std`, `encoder_type`, and `rnn_type` in model config.
- Training args include loss type, epoch count, batch size, learning rate, KL coefficient, and gradient clipping.

Validation focus:

- Grammar file, info folder, and SMILES file exist before cooking data.
- Saved model directory exists before prior sampling or reconstruction.

### Seq-VAE

Expected layout:

```text
data/zinc_moses/
├── train.csv
└── test.csv

results/
├── train_models/
└── config/
```

Config keys:

- `max_length`, encoder cell/layers/dropout, decoder cell/layers/dropout, latent size, hidden sizes, and embedding freeze flag.
- Training args include epoch count, batch size, initial learning rate, KL start/end schedule, and output directories.

Validation focus:

- CSV contains a SMILES column or first column of SMILES strings.
- SMILES length does not exceed `max_length` without an explicit truncation policy.

## Drug Synergy and Few-Shot Data

### DTSyn

Expected files:

- `ddi.csv`: drug combination labels, often with SMILES/drug identifiers and synergy labels.
- `gene_vector.csv`: LINCS gene-expression vector features.
- `rna.csv`: RNA feature table.
- Optional `ddi_test` CSV for held-out evaluation.

Validation focus:

- Required CSV files exist, parse, and are non-empty.
- Drug identifiers align across DDI, LINCS, and RNA feature tables.

### RGCN Drug Synergy

Expected files:

- `DDI/DDs.csv` or equivalent DDI labels.
- `DTI/drug_protein_links.tsv`.
- `PPI/protein_protein_links.txt`.
- `all_drugs_name.fet` drug physicochemical features.

Validation focus:

- DDI/DTI/PPI files are not accidentally still compressed archives.
- Feature file covers the drugs referenced by DDI labels.
- CPU/GPU choice is explicit; remove `--cuda` when CPU-only.

### Few-Shot Molecular Property (PAR)

Expected layout:

```text
data/
├── muv/
├── sider/
├── tox21/
└── toxcast/
```

Validation focus:

- `--dataset` and `--test-dataset` are one of the available task folders.
- `--pretrained_weight_path` exists when `--pretrained 1` is used.
- `--n-shot-train`, `--n-shot-test`, and `--n-query` are feasible for each task's label counts.

## Checkpoint and Output Conventions

- Paddle model checkpoints usually end in `.pdparams`; directory names often include `epoch<N>` or `model.iter-<step>`.
- GraphDTA writes to `model_dir/<dataset>_<config_name>` when using its shell wrapper.
- JT-VAE sampling writes a plain text output file and prints MOSES-style metrics when evaluation is available.
- HelixDock docking outputs are documented separately in `helixdock.md`.

## Minimal Preflight Matrix

| Workflow | Required before run | Common output |
| --- | --- | --- |
| GraphDTA | raw Davis/Kiba metadata, processed train/test NPZ, model config JSON | model dir, MSE/CI |
| MolTrans classification | train/val/test CSV splits, config JSON | AUROC logs/checkpoints |
| MolTrans regression | SMILES/target/affinity text files or benchmark folders, config JSON | MSE/CI logs/checkpoints |
| JT-VAE | SMILES file, vocab file, config JSON, checkpoint for sampling | processed shards, model.iter checkpoints, samples |
| GEM/PretrainGNN | molecule dataset root, encoder/model configs, optional checkpoint | `.pdparams` checkpoints and downstream metrics |
| HelixDock | model checkpoint, dataset config, encoder/model/train configs, processed/raw complexes | predicted SDF files and logs |
