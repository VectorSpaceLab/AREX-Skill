---
name: compound-drug-discovery
description: "Plan, validate, and troubleshoot PaddleHelix compound
  representation learning, molecular property prediction, DTI, molecular
  generation, drug synergy, few-shot molecular property, and HelixDock
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Compound Drug Discovery

Use this sub-skill when the task is about PaddleHelix chemistry or drug-discovery apps: compound GNN/GEM/InfoGraph representation learning, molecular property prediction, drug-target interaction, molecular generation, drug-drug synergy, few-shot molecular property prediction, HelixDock docking, or preflight validation of chemistry data/configs.

## Route by Intent

- **Compound property prediction or pretraining**: use `references/workflows.md#compound-representation-and-property-prediction` for GEM, GEM-2, PretrainGNNs, and InfoGraph command anatomy; use `references/data-formats.md#compound-property-and-pretraining-data` to verify SMILES, MoleculeNet-style directories, cached NPZ data, configs, and checkpoints.
- **Drug-target interaction**: use `references/workflows.md#drug-target-interaction-dti` for GraphDTA, MolTrans, SIGN, SMAN, GIANT, and BatchDTA routing; use `references/data-formats.md#drug-target-interaction-data` for Davis/Kiba, MolTrans, PDBbind-style, and BatchDTA layouts.
- **Molecular generation**: use `references/workflows.md#molecular-generation` for JT-VAE, SD-VAE, and Seq-VAE; use `references/data-formats.md#molecular-generation-data` for SMILES lists, vocab files, grammar files, model configs, checkpoints, and sampling outputs.
- **Drug synergy or few-shot property tasks**: use `references/workflows.md#drug-synergy-and-few-shot-property-workflows` and `references/data-formats.md#drug-synergy-and-few-shot-data`.
- **HelixDock**: use `references/helixdock.md` for setup, model/data/config/output contracts, resource notes, and skip-network guidance.
- **Input validation before any heavy run**: run `python sub-skills/compound-drug-discovery/scripts/validate_compound_inputs.py --help`, then validate local SMILES/config/data paths before planning training, sampling, preprocessing, or docking.

## Safety Boundaries

- Do not start full training, distributed runs, model downloads, dataset downloads, OpenBabel conversions, docking reproduction, or long MMFF preprocessing without explicit user approval.
- Treat app training launchers and HelixDock reproduce scripts as command-contract evidence only; this skill bundles no launcher that downloads data, mutates source checkouts, or starts training.
- Validate local files first, report missing pieces concretely, and ask before substituting datasets, changing task labels, reducing epochs, or switching GPU/CPU behavior.
- Route core `pahelix` API details, `InMemoryDataset` internals, featurizer implementation, and splitter behavior to `core-api-data`; route protein-only workflows to protein sub-skills.

## Validation Helper

Use the bundled helper for safe checks:

```bash
python sub-skills/compound-drug-discovery/scripts/validate_compound_inputs.py \
  --smiles-file data/input.smi \
  --json-config configs/config.json \
  --dataset-kind graphdta \
  --dataset-root data/davis
```

It checks file existence, JSON parseability, expected directory pieces, CSV headers, and likely malformed SMILES lines with optional RDKit validation when RDKit is installed. It does not import Paddle, start model code, download data, or require the original PaddleHelix checkout.

## Troubleshooting Entry Points

- Missing chemistry/backend dependencies, malformed SMILES/CSV/config JSON, missing NPZ/checkpoint files, and app-specific data layout errors: `references/troubleshooting.md`.
- HelixDock-specific RDKit/OpenBabel/version/model/data/output concerns: `references/helixdock.md#troubleshooting-and-safe-operation`.
- Dataset and config contracts by app family: `references/data-formats.md`.
