# Compound Workflow Troubleshooting

Use this guide to diagnose PaddleHelix compound/drug-discovery failures before running large jobs. Prefer safe validation and path checks over rerunning training blindly.

## Environment and Dependency Failures

### `ModuleNotFoundError: paddle` or Paddle backend errors

Likely causes:

- PaddlePaddle is not installed in the active environment.
- Installed Paddle build does not match CUDA/driver support.
- App code assumes GPU even when the environment is CPU-only.

Actions:

- Confirm whether the user wants CPU-only validation or actual training/inference.
- For training/inference, install a Paddle build matching the user's CUDA/CPU target in an isolated environment.
- For preflight only, run `validate_compound_inputs.py` and avoid importing Paddle-heavy app modules.

### `ModuleNotFoundError: pgl`

Likely causes:

- Graph learning apps such as GEM, PretrainGNNs, GraphDTA, SIGN, SMAN, GIANT, or few-shot PAR need PGL.
- Inspection-only PaddleHelix installs may intentionally omit PGL.

Actions:

- Install a PGL version compatible with the selected Paddle version if the user approves actual model execution.
- If only data/config validation is needed, do not install PGL; validate inputs and document that model execution remains blocked.

### RDKit missing or molecule parsing fails

Likely causes:

- RDKit is absent.
- SMILES contain malformed tokens, salts/mixtures unsupported by the downstream featurizer, or unexpected headers.
- Geometry workflows fail during conformer generation or MMFF optimization.

Actions:

- Run `validate_compound_inputs.py --smiles-file FILE`; it uses RDKit only if installed and otherwise performs conservative syntax checks.
- Remove headers, blank rows, and non-SMILES metadata from files passed to generation/pretraining scripts unless the app explicitly expects CSV.
- For scaffold splits or 3D feature generation, install RDKit in an isolated environment and revalidate.

### OpenBabel missing

Likely causes:

- SIGN/SMAN/PDBbind preprocessing or HelixDock RMSD/conversion steps require OpenBabel.

Actions:

- Ask whether preprocessing/RMSD is needed or whether already processed features can be used.
- Install OpenBabel only in an isolated environment with approval; do not mutate a shared chemistry environment.

### Deprecated `sklearn` package name

Likely causes:

- Some historical PaddleHelix metadata or app docs use `sklearn`; modern pip expects `scikit-learn`.

Actions:

- Install `scikit-learn` directly.
- Use the environment variable workaround for deprecated `sklearn` only if a legacy install path absolutely requires it and the user approves.

## SMILES, CSV, and JSON Problems

### Malformed SMILES before molecular generation

Symptoms:

- JT-VAE preprocessing fails in `mol_tree` or `chemutils`.
- Seq-VAE vocabulary creation or tokenization fails.
- RDKit reports parse errors.

Actions:

```bash
python sub-skills/compound-drug-discovery/scripts/validate_compound_inputs.py \
  --smiles-file data/input.smi \
  --max-smiles-length 120
```

Then fix:

- Remove non-SMILES headers unless explicitly supported.
- Ensure the first token on each line is the molecule string.
- Split multi-column metadata into a separate CSV if the app expects plain `.smi`.
- Replace or remove invalid rows; do not silently drop rows from supervised datasets without preserving label alignment.

### CSV split files fail to load

Symptoms:

- MolTrans classification cannot read `train.csv`, `val.csv`, or `test.csv`.
- Drug synergy scripts fail on DDI/LINCS/RNA CSV files.
- Few-shot PAR task loader cannot find expected task data.

Actions:

- Check that all required splits exist and are non-empty.
- Inspect CSV headers for drug, protein/target, and label columns.
- Confirm row counts and identifiers align across paired feature files.
- Use `validate_compound_inputs.py --csv-file FILE --require-columns col1,col2,...` when column names are known.

### JSON config parse or key errors

Symptoms:

- `json.decoder.JSONDecodeError`.
- Key errors such as missing `compound`, `protein`, `drug_max_seq`, `target_max_seq`, `model`, or train config fields.

Actions:

```bash
python sub-skills/compound-drug-discovery/scripts/validate_compound_inputs.py \
  --json-config path/to/config.json \
  --require-json-keys compound,protein
```

Then fix:

- Remove comments/trailing commas from JSON files.
- Match config type to workflow: GraphDTA config is not a MolTrans config; HelixDock flat update config is not a dataset config.
- Keep model and dataset config paths separate.

## DTI Layout Problems

### GraphDTA missing processed train/test NPZ

Symptoms:

- `--train_data data/davis/processed/train/` or `--test_data data/davis/processed/test/` is empty or missing.
- Training starts but dataset length is zero.

Expected layout:

```text
data/davis/
├── folds/{train_fold_setting1.txt,test_fold_setting1.txt}
├── ligands_can.txt
├── proteins.txt
├── Y
└── processed/{train/davis_train.npz,test/davis_test.npz}
```

Actions:

- Validate the dataset root:

```bash
python sub-skills/compound-drug-discovery/scripts/validate_compound_inputs.py \
  --dataset-kind graphdta \
  --dataset-root data/davis
```

- If raw files exist but processed NPZ files do not, ask before running preprocessing because it may require RDKit and time.
- For Kiba, ensure training command includes `--use_kiba_label`.

### MolTrans classification/regression mismatch

Symptoms:

- `train_cls.py` is pointed at regression text folders.
- `train_reg.py` is pointed at classification split CSVs.
- Dataset choice is not one of the script's allowed values.

Actions:

- Classification route: use `cls_davis`, `cls_biosnap`, or `cls_bindingdb` with `dataset/classification/.../{train,val,test}.csv`.
- Regression route: use `raw_*` or `benchmark_*` values with `dataset/regression/...` text/benchmark files.
- Validate model config contains MolTrans keys such as `drug_max_seq`, `target_max_seq`, `input_drug_dim`, and `input_target_dim`.

### SIGN/SMAN/GIANT PDBbind preprocessing missing

Symptoms:

- Train/val/test subsets are not found under `data_dir` or `data_path`.
- OpenBabel/Chimera conversion was skipped.
- Feature arrays or graph files are absent.

Actions:

- Confirm whether the user has raw PDBbind/CSAR structures or already processed features.
- Ask before running preprocessing; it can be slow and may require OpenBabel and large raw datasets.
- Keep `cutoff`/`cut_dist` consistent between preprocessing and training.

### BatchDTA data path confusion

Symptoms:

- Pairwise scripts cannot find `Data/` files.
- Distributed GraphDTA script fails before model execution.

Actions:

- Confirm `--data_path` points to unpacked processed data, not the zip archive.
- Confirm selected script corresponds to pairwise vs pointwise and DeepDTA vs GraphDTA vs MolTrans.
- Ask before launching distributed Torch runs.

## Molecular Generation Problems

### JT-VAE vocabulary or checkpoint missing

Symptoms:

- `sample.py` fails because `--vocab` or `--model` is missing.
- Training fails because `zinc_processed` does not exist.

Actions:

- Build the vocabulary from the same training SMILES source used for preprocessing.
- Run preprocessing only after validating the SMILES file.
- Confirm checkpoint path such as `vae_models/model.iter-441000` exists before sampling.

### SD-VAE grammar files missing

Symptoms:

- `make_dataset_parallel.py`, `dump_cfg_trees.py`, `sample_prior.py`, or `reconstruct_zinc.py` cannot find grammar/info files.

Actions:

- Confirm `context_free_grammars/mol_zinc.grammar` and the info folder exist.
- Validate the SMILES file and saved model directory before sampling or reconstruction.

### Seq-VAE max length or CSV problems

Symptoms:

- Tokenization fails or samples truncate unexpectedly.
- `trainer.py` cannot find `train.csv`.

Actions:

- Check `model_config.json` `max_length` against the longest SMILES line.
- Confirm CSV header/column handling for the user's data and preserve label/metadata columns separately if needed.

## HelixDock Problems

Use `helixdock.md` for detailed docking troubleshooting. Common short checks:

- `model/helixdock.pdparams` exists and is complete.
- Dataset config JSON parses and references existing raw/processed data paths.
- RDKit version is compatible with documented expectations.
- OpenBabel is installed if RMSD/conversion is requested.
- Paddle distributed launch and GPUs are approved and available.
- Non-commercial and online-service terms are acceptable for the user's intended use.

## GPU Memory and Runtime Problems

Symptoms:

- CUDA out of memory.
- A training command appears to hang.
- Distributed launch creates unexpected logs or fails on rank initialization.

Actions:

- Confirm job scale: dataset size, epochs, batch size, number of samples, and checkpoint cadence.
- Reduce batch size, epochs, workers, or sample counts only with user approval because results and runtimes change.
- Prefer a dry run on one tiny user-approved subset if the app supports it; otherwise validate data and explain why a smoke test is not safe.
- Ensure outputs are directed to user-approved model/log directories, not accidental source-tree defaults.

## Download, License, and Service Caveats

- PaddleHelix app READMEs reference many external datasets, pretrained models, and online services. Do not download or upload without explicit approval.
- HelixDock and the main PaddleHelix repository include non-commercial license language; check intended use for commercial contexts.
- Some datasets require third-party terms, manual registration, or contact forms; do not bypass these processes.

## Quick Diagnostic Commands

```bash
# Validate a SMILES file and JSON config.
python sub-skills/compound-drug-discovery/scripts/validate_compound_inputs.py \
  --smiles-file data/input.smi \
  --json-config configs/config.json

# Validate GraphDTA layout.
python sub-skills/compound-drug-discovery/scripts/validate_compound_inputs.py \
  --dataset-kind graphdta \
  --dataset-root data/davis

# Validate MolTrans classification layout.
python sub-skills/compound-drug-discovery/scripts/validate_compound_inputs.py \
  --dataset-kind moltrans-classification \
  --dataset-root dataset/classification/DAVIS

# Validate JT-VAE prerequisites.
python sub-skills/compound-drug-discovery/scripts/validate_compound_inputs.py \
  --dataset-kind jtvae \
  --dataset-root . \
  --smiles-file data/zinc/250k_rndm_zinc_drugs_clean_sorted.smi \
  --json-config configs/config.json \
  --require-files data/zinc/vocab.txt,vae_models/model.iter-441000
```

Interpretation:

- Exit code `0`: no blocking validation errors found.
- Exit code `1`: blocking errors found; fix these before training/docking.
- Warnings: possible issues or optional dependency gaps; decide whether they matter for the requested workflow.
