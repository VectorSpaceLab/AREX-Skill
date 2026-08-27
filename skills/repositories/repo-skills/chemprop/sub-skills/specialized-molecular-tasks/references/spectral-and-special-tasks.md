# Spectral and Special Task Workflows

Chemprop's task registry includes ordinary molecule/reaction tasks and specialized predictors for uncertainty, multiclass, and spectra. This reference focuses on options that interact with specialized molecular schemas.

## Task Types

Common `--task-type` values include:

- `regression`
- `regression-mve`
- `regression-evidential`
- `regression-quantile`
- `classification`
- `classification-dirichlet`
- `multiclass`
- `multiclass-dirichlet`
- `spectral`

Reaction and multicomponent inputs can use the regression uncertainty variants in the same way as molecule inputs:

```bash
chemprop train -i rxn.csv --reaction-columns rxn_smiles --task-type regression-mve
chemprop train -i rxn.csv --reaction-columns rxn_smiles --task-type regression-evidential --evidential-regularization 0.2
chemprop train -i rxn.csv --reaction-columns rxn_smiles --task-type regression-quantile --alpha 0.1
```

## Spectral Tasks

Use `--task-type spectral` when targets are bins or positions in a spectrum and the model should consider all target columns together. Spectral predictions are positive and normalized so each predicted spectrum sums to `1`.

```bash
chemprop train \
  -i spectra.csv \
  --smiles-columns smiles \
  --target-columns mz_100 mz_101 mz_102 mz_103 \
  --task-type spectral \
  --metrics sid earthmovers \
  --save-dir spectral_model
```

Default spectral behavior uses spectral information divergence (`sid`) as criterion/metric. `earthmovers` / `wasserstein` can be used as an additional metric or loss where appropriate.

Important version note: the Python predictor implementation supports `spectral_activation` values `softplus`, `exp`, or `None`, but the Chemprop 2.2.3 CLI does not expose `--spectral-activation`. The CLI also has commented-out placeholders for spectra target floors and phase masks. Do not generate CLI commands that rely on unavailable spectral activation, target-floor, phase-feature, or spectra-phase-mask flags.

## Loss and Metric Choices

Loss registry entries relevant to specialized tasks include:

- Regression: `mse`, `mae`, `rmse`, `bounded-mse`, `bounded-mae`, `bounded-rmse`.
- Uncertainty: `mve`, `evidential`, `quantile`, `pinball`, `quantile-point`, `pinball-point`.
- Classification: `bce`, `ce`, `binary-mcc`, `multiclass-mcc`, `dirichlet`.
- Spectral: `sid`, `earthmovers`, `wasserstein`.
- Enrichment: `nlogprob_enrichment`.

Metrics include `mse`, `mae`, `rmse`, bounded variants, `r2`, `binary-mcc`, `multiclass-mcc`, `roc`, `prc`, `accuracy`, and `f1`. For multi-output MolAtomBond models, non-default tracking metrics need a suffix such as `rmse-atom`, `val_loss-bond`, or `rmse-mol` so Chemprop knows which predictor family to track.

## Specialized Descriptor Interactions

Molecule-level descriptors and generated molecule featurizers can be used with molecule, reaction, and reaction-plus-molecule workflows:

```bash
chemprop train \
  -i rxn_solvent.csv \
  --reaction-columns rxn_smiles \
  --smiles-columns solvent_smiles \
  --target-columns rate \
  --descriptors-columns temperature pressure \
  --molecule-featurizers morgan_count rdkit_2d
```

For per-atom and per-bond feature files, remember:

- Atom features/descriptors must match the atom ordering used by the RDKit molecule; use `--reorder-atoms` for mapped atom targets when needed.
- Bond features/descriptors must match Chemprop/RDKit bond ordering.
- Component-indexed path syntax is needed for multicomponent inputs: `--atom-descriptors-path 1 solvent_atom_descs.npz`.
- Reaction components warn that extra atom and bond features are unsupported by the condensed reaction graph featurizer.

## Bounded and Constrained Outputs

Bounded losses use `<`/`>` markers in target values and are useful when measurements are censored or thresholded. Constrained MolAtomBond prediction is separate: it uses `--constraints-path` and `--constraints-to-targets` so atom or bond predictions satisfy molecule-level sums. Do not substitute bounded losses for constraints when the scientific requirement is a conservation/sum rule.

## When to Prefer Python API Workflows

Prefer the Python API over the CLI when the task requires:

- Setting spectral activation behavior not exposed by the CLI.
- Custom constraint networks or custom predictor wiring.
- Deep inspection of `MolAtomBondMPNN` outputs before Chemprop writes predictions.
- Novel collate logic or dataloaders beyond the standard CSV/NPZ parser.

Route those requests to `../python-api-modeling/` after using this sub-skill to identify the schema and Chemprop model family.
