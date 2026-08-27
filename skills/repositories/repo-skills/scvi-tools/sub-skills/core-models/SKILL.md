---
name: core-models
description: "Select and use scvi-tools built-in core model families, including
  setup, training, and common accessors for SCVI, SCANVI, TOTALVI, PEAKVI,
  MULTIVI, AUTOZI, LinearSCVI, CondSCVI, DestVI, AmortizedLDA, and mlxSCVI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Core Models

Use this sub-skill when choosing among scvi-tools built-in model families or writing common `scvi.model` workflows. It covers model selection, modality requirements, setup/train patterns, core constructor and `setup_anndata` signatures, and failures around model registration or modality mismatch.

## Fast Routing

- Need to choose a model from data modalities or labels: read [references/model-selection.md](references/model-selection.md).
- Need exact core `setup_anndata`, constructor, or `train` parameters: read [references/api-reference.md](references/api-reference.md).
- Need to debug missing setup, wrong keys, protein/ATAC/RNA modality shape issues, or optional MLX/Pyro dependencies: read [references/troubleshooting.md](references/troubleshooting.md).
- Need to inspect the installed package API rather than trust static notes: run `python scripts/inspect_model_api.py --model SCVI --model TOTALVI` from this sub-skill directory; repeat `--model` for each model.

## Boundaries

- Use the sibling `data-setup` skill for loading datasets, AnnData/MuData preparation, count layers, registry internals, and setup schema design.
- Use the training-and-inference skill for accelerator selection, callbacks, logging, checkpointing, custom `Trainer` options, and long-running inference operations.
- Use downstream-analysis for differential expression/accessibility, latent visualization, normalized expression/accessibility interpretation, clustering, and result analysis.
- Use multimodal-and-spatial or annotation-and-query for external specialized models and deep spatial/query transfer workflows beyond the built-in core family overview.

## Minimal Core Pattern

```python
import scvi

scvi.model.SCVI.setup_anndata(adata, layer="counts", batch_key="batch")
model = scvi.model.SCVI(adata, n_latent=10)
model.train(max_epochs=100)
latent = model.get_latent_representation()
```

Always call the matching class's `setup_anndata` on the object before constructing that class, and pass modality-specific keys such as `protein_expression_obsm_key` only when the model signature supports them.
