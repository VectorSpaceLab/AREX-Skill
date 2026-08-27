---
name: downstream-analysis
description: "Use trained scvi-tools models for latent embeddings, normalized
  expression/protein/accessibility, imputation-like posterior outputs,
  differential expression/abundance/accessibility/methylation, feature
  correlations, posterior predictive checks, criticism, and simulation outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# downstream-analysis

Use this sub-skill after a scvi-tools model is constructed and trained, and the task is to extract biological results or quality checks from the fitted posterior.

## Fast Routing

- Need embeddings, denoised values, imputation-like predictions, counterfactual batch conditioning, or posterior predictive samples: read [workflows](references/workflows.md).
- Need exact method names, key parameters, return shapes, or model-family support: read [API reference](references/api-reference.md).
- Need differential expression, abundance, accessibility, methylation, or group/boolean selection behavior: read [workflows](references/workflows.md) and [API reference](references/api-reference.md).
- Need posterior predictive checks or a criticism report for one or more trained models: read [workflows](references/workflows.md).
- Need to debug untrained models, wrong model families, missing categories, invalid gene/region/protein lists, batch conditioning, or memory issues: read [troubleshooting](references/troubleshooting.md).

## Boundaries

- Use data-setup for AnnData/MuData construction, `setup_anndata`, `setup_mudata`, count layers, and registry validation before model creation.
- Use core-models or multimodal-and-spatial for choosing model families and modality-specific setup.
- Use training-and-inference for `.train(...)`, accelerators, callbacks, checkpoints, and long-running inference settings.
- Use model-io-and-hub for saving/loading models or publishing artifacts.

## Minimal Patterns

```python
latent = model.get_latent_representation()
adata.obsm["X_scvi"] = latent

normalized = model.get_normalized_expression(gene_list=["MALAT1"], return_numpy=False)
de = model.differential_expression(groupby="cell_type", group1="B cells", group2="T cells")
```

Validate that the model is trained, the requested method exists on that model family, all `groupby`/`sample_key` categories exist in `.obs`, and feature lists match `adata.var_names`, region names, or protein names before running expensive posterior sampling.
