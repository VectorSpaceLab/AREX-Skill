---
name: python-api-modeling
description: "Build Chemprop v2 Python API workflows for data objects,
  dataloaders, MPNN model wiring, Lightning training/prediction, scaling
  transforms, metrics/losses, ensembling, and save/load."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Chemprop Python API Modeling

Use this sub-skill when a user wants to write or repair Python code that uses Chemprop directly for molecular property prediction. Prefer Python API patterns here; route pure `chemprop train`, `chemprop predict`, `chemprop fingerprint`, `chemprop convert`, or `chemprop hpopt` commands to CLI-oriented sub-skills. Route reaction/MolAtomBond task constraints to `specialized-molecular-tasks` and uncertainty-specific interpretation to `uncertainty-advanced`.

## Core Workflow

1. Create Chemprop datapoints from RDKit molecules or SMILES.
2. Wrap them in `MoleculeDataset`, `ReactionDataset`, `MulticomponentDataset`, or `MolAtomBondDataset` as appropriate.
3. Build dataloaders with `chemprop.data.build_dataloader`; keep `shuffle=False` for validation, test, and prediction loaders.
4. Wire a model from message passing, aggregation, and predictor modules.
5. Train or predict with `lightning.pytorch.Trainer`.
6. Save portable Chemprop model files with `chemprop.models.save_model`; reload with `chemprop.models.load_model` or class `load_from_file` helpers.

```python
import numpy as np
from lightning import pytorch as pl
from chemprop import data, models, nn

smiles = ["CCO", "CCN", "c1ccccc1"]
y = np.array([[0.1], [0.2], [0.3]], dtype=float)
dset = data.MoleculeDataset([
    data.MoleculeDatapoint.from_smi(smi, target) for smi, target in zip(smiles, y)
])
loader = data.build_dataloader(dset, batch_size=2, shuffle=True)

mp = nn.BondMessagePassing(d_h=64, depth=2)
agg = nn.MeanAggregation()
predictor = nn.RegressionFFN(input_dim=mp.output_dim, n_tasks=1, hidden_dim=64)
model = models.MPNN(mp, agg, predictor, metrics=[nn.RMSE(), nn.MAE()])

trainer = pl.Trainer(accelerator="cpu", devices=1, logger=False, enable_checkpointing=False, max_epochs=1)
trainer.fit(model, loader)
```

## References

- `references/api-reference.md`: public classes, constructors, registries, model save/load, and batch signatures.
- `references/python-workflows.md`: end-to-end recipes for training, prediction, scaling, ensembling, and checkpoint use.
- `references/model-components.md`: component compatibility notes for message passing, aggregation, predictors, losses, metrics, transforms, and dataloaders.
- `references/troubleshooting.md`: common Python API failures and fixes.
- `scripts/chemprop_api_smoke.py`: self-contained CPU smoke script for minimal MPNN training, prediction, and save/load validation.

## Key Guardrails

- Keep predictor `input_dim` equal to the feature dimension produced by `model.fingerprint`; for plain `MPNN` this is usually `message_passing.output_dim` plus any post-aggregation `X_d` width.
- Use regression predictors with regression targets, binary predictors with binary labels, multiclass predictors with integer class targets and `n_classes`, and spectral predictors with spectrum-shaped targets.
- Use `UnscaleTransform` on predictors for scaled regression targets, `ScaleTransform` on `X_d`/`V_d`, and `GraphTransform` on extra atom/bond features.
- Build prediction loaders with `shuffle=False`; Lightning warns and user-facing row order becomes ambiguous if prediction data is shuffled.
- Preserve target names by passing `output_columns` to `save_model` and reading them back with `chemprop.models.utils.load_output_columns` when needed.
