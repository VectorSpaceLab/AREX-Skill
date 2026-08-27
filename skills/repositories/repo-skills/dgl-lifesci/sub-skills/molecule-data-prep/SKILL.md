---
name: molecule-data-prep
description: "Prepare molecular and protein-ligand data for DGL-LifeSci by
  validating SMILES/CSV inputs, constructing graphs, selecting featurizers and
  datasets, and applying supported split/evaluation helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Molecule Data Prep

Use this sub-skill when a task needs DGL-LifeSci data ingestion or graph preparation before model training or inference:

- Convert SMILES or RDKit molecules into DGL graphs with `dgllife.utils` constructors.
- Choose atom/bond featurizers and check feature field names and dimensions.
- Load custom CSV or unlabeled SMILES inputs with `MoleculeCSVDataset` or `UnlabeledSMILES`.
- Select built-in MoleculeNet, Alchemy, or PDBBind-style dataset classes without writing training loops.
- Split datasets and use support utilities such as `Meter` and `EarlyStopping` for prepared data pipelines.
- Validate tiny fixtures offline with the bundled input validator.

## Start Here

1. Read `references/data-formats.md` to decide the expected input schema and dataset class.
2. Read `references/api-reference.md` for verified constructor signatures, feature fields, graph shapes, and splitter gotchas.
3. Run `scripts/validate_molecule_inputs.py --help` and then validate the user's tiny CSV or TXT fixture before building a full pipeline.
4. If validation fails, use `references/troubleshooting.md` to diagnose invalid SMILES, missing labels, import errors, cache mismatches, or split failures.

## Quick Commands

Validate a labeled CSV and report graph shape summaries:

```bash
python scripts/validate_molecule_inputs.py \
  --input molecules.csv --format csv --smiles-column smiles --tasks task1,task2 \
  --require-labels --graph bigraph --max-rows 50
```

Validate an inference TXT file without labels:

```bash
python scripts/validate_molecule_inputs.py \
  --input smiles.txt --format txt --graph complete --max-rows 25
```

## Routing Boundaries

Stay in this sub-skill for data schemas, graph construction, featurizers, splits, dataset classes, and tiny fixture validation.

Route elsewhere when the task asks for:

- Property model architecture, batching, loss functions, or full train/eval loops: use `property-prediction`.
- Pretrained GIN checkpoints, `load_pretrained`, or model-zoo selection: use `model-zoo-pretraining`.
- WLN reaction center/ranking datasets or reaction-specific atom-map handling: use `reaction-prediction`.
- Binding-affinity model architecture details after PDBBind-style complex graphs are prepared: use `../binding-affinity/SKILL.md`.

## Bundled Resources

- `references/api-reference.md`: verified DGL-LifeSci signatures, graph constructors, featurizers, splitters, `Meter`, and `EarlyStopping` notes.
- `references/data-formats.md`: CSV, TXT, SMILES, built-in dataset, and PDBBind-style data expectations.
- `references/troubleshooting.md`: import/install, optional dependency, invalid data, feature-shape, split, cache, and helper failure fixes.
- `scripts/validate_molecule_inputs.py`: safe offline validator for CSV/TXT SMILES fixtures and optional graph shape summaries.
