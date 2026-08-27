---
name: scvi-tools
description: "Use scvi-tools for probabilistic single-cell omics analysis with
  AnnData/MuData setup, model selection, training, downstream analysis,
  save/load, Hub workflows, and advanced extension/autotune tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# scvi-tools

Use this skill when working with `scvi-tools`, the PyTorch/AnnData-based package for probabilistic analysis of single-cell RNA, protein, ATAC, spatial, methylation, perturbation, velocity, and related omics data.

Use the bundled sub-skills for workflow depth. Keep the root as a router: read only the sub-skill and references needed for the user request.

## First Checks

For a new environment or bug report, verify the install before choosing a workflow:

```bash
python - <<'PY'
import scvi, torch, anndata
print('scvi-tools', scvi.__version__)
print('torch', torch.__version__, 'cuda', torch.cuda.is_available())
print('anndata', anndata.__version__)
PY
```

Or run the bundled diagnostic:

```bash
python scripts/check_scvi_environment.py --json
```

`scvi-tools` requires Python 3.12+ in this checkout. GPU acceleration is optional for most APIs; CPU works for inspection and small examples, while real training may require CUDA/MPS/accelerator-specific PyTorch installations.

## Route by Task

- Preparing input data, `AnnData`/`MuData`, layers, `.obs`, `.obsm`, `.varm`, registries, readers, or `setup_anndata`: use `sub-skills/data-setup/`.
- Choosing and instantiating built-in models such as `SCVI`, `SCANVI`, `TOTALVI`, `PEAKVI`, `MULTIVI`, `AUTOZI`, `LinearSCVI`, `CondSCVI`, `DestVI`, `AmortizedLDA`, or `mlxSCVI`: use `sub-skills/core-models/`.
- Label transfer, semi-supervised annotation, query/reference mapping, doublet detection, or marker-based assignment with `SCANVI`, `SOLO`, or `CellAssign`: use `sub-skills/annotation-and-query/`.
- Multimodal, spatial, ATAC, methylation, velocity, perturbation, contrastive, deconvolution, and external specialized model families: use `sub-skills/multimodal-and-spatial/`.
- Training arguments, `Trainer` behavior, accelerator/device choices, callbacks, validation splits, dataloaders, custom datamodules, or inference dataloaders: use `sub-skills/training-and-inference/`.
- Post-training outputs such as latent representations, normalized expression/protein/accessibility, imputation, differential expression/abundance/accessibility/methylation, posterior predictive checks, criticism, or simulation: use `sub-skills/downstream-analysis/`.
- Saving/loading, model directories, minified data, registry compatibility, version migration, or Hugging Face Hub metadata/publish/load flows: use `sub-skills/model-io-and-hub/`.
- Hyperparameter tuning, Ray/HyperOpt, MLflow, optional extras, developer extension APIs, custom modules, Pyro/module internals, distributions, or neural-network building blocks: use `sub-skills/advanced-operations/`.

## Common End-to-End Pattern

```python
import scvi

scvi.model.SCVI.setup_anndata(adata, layer='counts', batch_key='batch')
model = scvi.model.SCVI(adata, n_latent=10)
model.train(max_epochs=20, accelerator='auto', devices='auto')
latent = model.get_latent_representation()
model.save('my_scvi_model', overwrite=True)
```

For this pattern:

1. Use `data-setup` to make sure `adata` contains valid counts, batch labels, covariates, modality matrices, and registry fields.
2. Use `core-models` or a specialized model sub-skill to choose the class and setup keys.
3. Use `training-and-inference` to tune epochs, batch size, accelerator, callbacks, and dataloaders.
4. Use `downstream-analysis` for accessors and statistical outputs.
5. Use `model-io-and-hub` before handing off a saved model or loading one in another environment.

## Optional Dependencies

The base package covers common model APIs, but several routes need extras or services:

- `autotune`: Ray/HyperOpt and tuning helpers.
- `hub`: Hugging Face Hub and storage metadata workflows.
- `dataloaders`: LaminDB, CELLxGENE Census, TileDB-SOMA, torchdata, and AnnBatch integrations.
- `regseq`, `file_sharing`, `parallel`, `interpretability`, `diagvi`, `mlflow`, `rapids`, `cuda`, `tpu`, `metal`: specialized workflows.

Do not install `all` or broad extras automatically. Install the smallest extra set needed for the requested route, then rerun `scripts/check_scvi_environment.py`.

## Troubleshooting Entry Points

- Cross-cutting install/import/backend/version failures: read `references/troubleshooting.md`.
- Data-field or registry failures: read `sub-skills/data-setup/references/troubleshooting.md`.
- Model-family or modality mismatch: read the nearest model sub-skill troubleshooting reference.
- Training failures: read `sub-skills/training-and-inference/references/troubleshooting.md`.
- Save/load or Hub failures: read `sub-skills/model-io-and-hub/references/troubleshooting.md`.

## Provenance

This generated skill is aligned to the source snapshot in `references/repo-provenance.md`. Refresh the skill if the repository version, public model APIs, optional extras, setup signatures, or save/load/hub behavior changes.
