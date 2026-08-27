# Core Model API Reference

This reference records signatures verified from scvi-tools 1.4.3 source and live import facts. Use `scripts/inspect_model_api.py` to re-check an installed version.

## Common Workflow Skeleton

```python
from scvi.model import SCVI

SCVI.setup_anndata(adata, layer="counts", batch_key="batch")
model = SCVI(adata, n_latent=10)
model.train(max_epochs=100, batch_size=128)
latent = model.get_latent_representation()
```

Rules:

- `setup_anndata` is a classmethod and must be called before constructing the same model class on that AnnData object.
- `setup_anndata` mutates/records setup state on the AnnData object; if the object is copied or subset in a schema-changing way, re-run setup.
- Most PyTorch core models inherit the generic unsupervised `train` unless they override it; `SCANVI` inherits semisupervised training; `AmortizedLDA` uses Pyro SVI; `mlxSCVI` uses MLX training.
- Training accepts Lightning trainer kwargs through `**trainer_kwargs` or `**kwargs`; detailed accelerator/callback behavior belongs to the training-and-inference skill.

## Verified `setup_anndata` Signatures

| Class | Signature |
|---|---|
| `SCVI` | `SCVI.setup_anndata(adata, layer=None, batch_key=None, labels_key=None, size_factor_key=None, categorical_covariate_keys=None, continuous_covariate_keys=None, **kwargs)` |
| `SCANVI` | `SCANVI.setup_anndata(adata, labels_key, unlabeled_category, layer=None, batch_key=None, size_factor_key=None, categorical_covariate_keys=None, continuous_covariate_keys=None, use_minified=True, **kwargs)` |
| `TOTALVI` | `TOTALVI.setup_anndata(adata, protein_expression_obsm_key, protein_names_uns_key=None, batch_key=None, panel_key=None, layer=None, size_factor_key=None, categorical_covariate_keys=None, continuous_covariate_keys=None, **kwargs)` |
| `PEAKVI` | `PEAKVI.setup_anndata(adata, batch_key=None, labels_key=None, categorical_covariate_keys=None, continuous_covariate_keys=None, layer=None, **kwargs)` |
| `MULTIVI` | `MULTIVI.setup_anndata(adata, layer=None, batch_key=None, size_factor_key=None, categorical_covariate_keys=None, continuous_covariate_keys=None, protein_expression_obsm_key=None, protein_names_uns_key=None, **kwargs)` |
| `AUTOZI` | `AUTOZI.setup_anndata(adata, batch_key=None, labels_key=None, layer=None, **kwargs)` |
| `LinearSCVI` | `LinearSCVI.setup_anndata(adata, batch_key=None, labels_key=None, layer=None, **kwargs)` |
| `CondSCVI` | `CondSCVI.setup_anndata(adata, batch_key=None, labels_key=None, fine_labels_key=None, layer=None, unlabeled_category="unlabeled", size_factor_key=None, **kwargs)` |
| `DestVI` | `DestVI.setup_anndata(adata, layer=None, smoothed_layer=None, batch_key=None, **kwargs)` |
| `AmortizedLDA` | `AmortizedLDA.setup_anndata(adata, layer=None, **kwargs)` |
| `mlxSCVI` | `mlxSCVI.setup_anndata(adata, layer=None, batch_key=None, labels_key=None, categorical_covariate_keys=None, continuous_covariate_keys=None, **kwargs)` |

## Constructor Essentials

| Class | Constructor shape | Notes |
|---|---|---|
| `SCVI` | `SCVI(adata=None, n_hidden=128, n_latent=10, n_layers=1, dropout_rate=0.1, dispersion="gene", gene_likelihood="zinb", use_observed_lib_size=True, latent_distribution="normal", **kwargs)` | RNA default; `gene_likelihood` supports `"zinb"`, `"nb"`, `"poisson"`, `"normal"`. |
| `SCANVI` | `SCANVI(adata=None, n_hidden=128, n_latent=10, n_layers=1, dropout_rate=0.1, dispersion="gene", gene_likelihood="zinb", use_observed_lib_size=True, linear_classifier=False, datamodule=None, **model_kwargs)` | Usually call `SCANVI.from_scvi_model(scvi_model, unlabeled_category=...)` when starting from pretrained SCVI. |
| `TOTALVI` | `TOTALVI(adata, n_latent=20, gene_dispersion="gene", protein_dispersion="protein", gene_likelihood="nb", latent_distribution="normal", empirical_protein_background_prior=None, override_missing_proteins=False, **model_kwargs)` | Requires registered protein matrix. `override_missing_proteins` handles missing protein panels only when intended. |
| `PEAKVI` | `PEAKVI(adata=None, n_hidden=None, n_latent=None, n_layers_encoder=2, n_layers_decoder=2, dropout_rate=0.1, model_depth=True, region_factors=True, use_batch_norm="none", use_layer_norm="both", latent_distribution="normal", deeply_inject_covariates=False, encode_covariates=False, **model_kwargs)` | ATAC/accessibility model. |
| `MULTIVI` | `MULTIVI(adata, n_genes=None, n_regions=None, modality_weights="equal", modality_penalty="Jeffreys", n_hidden=None, n_latent=None, n_layers_encoder=2, n_layers_decoder=2, dropout_rate=0.1, region_factors=True, gene_likelihood="zinb", dispersion="gene", fully_paired=False, protein_dispersion="protein", **model_kwargs)` | Use for RNA+ATAC/mosaic data; pass `n_genes` and `n_regions` when the feature split is not inferable. |
| `AUTOZI` | `AUTOZI(adata=None, n_hidden=128, n_latent=10, n_layers=1, dropout_rate=0.1, dispersion="gene", latent_distribution="normal", alpha_prior=0.5, beta_prior=0.5, minimal_dropout=0.01, zero_inflation="gene", use_observed_lib_size=True, **model_kwargs)` | Zero-inflation/dropout analysis. |
| `LinearSCVI` | `LinearSCVI(adata=None, n_hidden=128, n_latent=10, n_layers=1, dropout_rate=0.1, dispersion="gene", gene_likelihood="nb", use_observed_lib_size=False, latent_distribution="normal", **model_kwargs)` | Linear decoder for interpretability; default likelihood differs from SCVI. |
| `CondSCVI` | `CondSCVI(adata, n_hidden=128, n_latent=5, n_layers=2, weight_obs=False, dropout_rate=0.05, **module_kwargs)` | Single-cell reference model for DestVI; can use priors via module kwargs. |
| `DestVI` | Prefer `DestVI.from_rna_model(st_adata, sc_model, ...)` | Direct constructor needs decoder state and tensors; use factory after `CondSCVI` training. |
| `AmortizedLDA` | `AmortizedLDA(adata, n_topics=20, n_hidden=128, cell_topic_prior=None, topic_feature_prior=None)` | Pyro-backed topic model; Pyro dependency must be importable. |
| `mlxSCVI` | `mlxSCVI(adata, n_hidden=128, n_latent=10, dropout_rate=0.1, gene_likelihood="nb", **model_kwargs)` | The exported class name is `mlxSCVI`, not `MlxSCVI`; requires MLX optional dependency. |

## Train Signatures to Remember

Generic unsupervised PyTorch models such as `SCVI`, `AUTOZI`, and `LinearSCVI` inherit:

```python
model.train(max_epochs=None, accelerator="auto", devices="auto", train_size=None,
            validation_size=None, shuffle_set_split=True, load_sparse_tensor=False,
            batch_size=128, early_stopping=False, datasplitter_kwargs=None,
            plan_config=None, plan_kwargs=None, datamodule=None,
            trainer_config=None, **trainer_kwargs)
```

`SCANVI` semisupervised training adds label balancing and adversarial options:

```python
model.train(max_epochs=None, n_samples_per_label=None, check_val_every_n_epoch=None,
            train_size=0.9, validation_size=None, shuffle_set_split=True,
            batch_size=128, accelerator="auto", devices="auto",
            adversarial_classifier=None, datasplitter_kwargs=None,
            plan_config=None, plan_kwargs=None, datamodule=None,
            trainer_config=None, **trainer_kwargs)
```

Overridden model training signatures:

- `TOTALVI.train(max_epochs=None, lr=0.004, accelerator="auto", devices="auto", train_size=None, validation_size=None, shuffle_set_split=True, batch_size=256, early_stopping=True, check_val_every_n_epoch=None, reduce_lr_on_plateau=True, n_steps_kl_warmup=None, n_epochs_kl_warmup=None, adversarial_classifier=None, datasplitter_kwargs=None, plan_kwargs=None, external_indexing=None, **kwargs)`
- `PEAKVI.train(max_epochs=500, lr=0.0001, accelerator="auto", devices="auto", train_size=None, validation_size=None, shuffle_set_split=True, batch_size=128, weight_decay=0.001, eps=1e-08, early_stopping=True, early_stopping_patience=50, check_val_every_n_epoch=None, n_steps_kl_warmup=None, n_epochs_kl_warmup=50, datasplitter_kwargs=None, plan_kwargs=None, datamodule=None, **kwargs)`
- `MULTIVI.train(max_epochs=500, lr=0.0001, accelerator="auto", devices="auto", train_size=None, validation_size=None, shuffle_set_split=True, batch_size=128, weight_decay=0.001, eps=1e-08, early_stopping=True, check_val_every_n_epoch=None, n_steps_kl_warmup=None, n_epochs_kl_warmup=50, adversarial_mixing=True, datasplitter_kwargs=None, plan_kwargs=None, **kwargs)`
- `CondSCVI.train(max_epochs=300, lr=0.001, accelerator="auto", devices="auto", train_size=1, validation_size=None, shuffle_set_split=True, batch_size=128, datasplitter_kwargs=None, plan_kwargs=None, **kwargs)`
- `DestVI.train(max_epochs=2000, lr=0.003, accelerator="auto", devices="auto", train_size=1.0, validation_size=None, shuffle_set_split=True, batch_size=128, n_epochs_kl_warmup=200, datasplitter_kwargs=None, plan_kwargs=None, **kwargs)`
- `AmortizedLDA` uses Pyro SVI training: `train(max_epochs=None, accelerator="auto", device="auto", train_size=None, validation_size=None, shuffle_set_split=True, batch_size=128, early_stopping=False, lr=None, training_plan=None, datasplitter_kwargs=None, plan_config=None, plan_kwargs=None, trainer_config=None, **trainer_kwargs)`
- `mlxSCVI` uses MLX training: `train(max_epochs=None, accelerator="auto", devices="auto", train_size=None, validation_size=None, shuffle_set_split=True, batch_size=128, datasplitter_kwargs=None, plan_kwargs=None, **trainer_kwargs)`

## Setup Examples by Model

### SCANVI with unlabeled cells

```python
from scvi.model import SCANVI

SCANVI.setup_anndata(
    adata,
    labels_key="cell_type",
    unlabeled_category="Unknown",
    layer="counts",
    batch_key="batch",
)
model = SCANVI(adata, n_latent=10)
model.train(max_epochs=100, n_samples_per_label=100)
predicted = model.predict()
```

### TOTALVI with CITE-seq protein matrix

```python
from scvi.model import TOTALVI

TOTALVI.setup_anndata(
    adata,
    layer="counts",
    batch_key="batch",
    protein_expression_obsm_key="protein_expression",
)
model = TOTALVI(adata, n_latent=20)
model.train(max_epochs=200)
protein = model.get_normalized_protein_expression()
```

### PEAKVI ATAC-only

```python
from scvi.model import PEAKVI

PEAKVI.setup_anndata(adata, batch_key="batch")
model = PEAKVI(adata)
model.train(max_epochs=200)
accessibility = model.get_accessibility_estimates()
```

### MULTIVI RNA + ATAC

```python
from scvi.model import MULTIVI

MULTIVI.setup_anndata(adata, batch_key="batch")
model = MULTIVI(adata, n_genes=n_genes, n_regions=n_regions)
model.train(max_epochs=200)
latent = model.get_latent_representation()
```

### CondSCVI then DestVI

```python
from scvi.model import CondSCVI, DestVI

CondSCVI.setup_anndata(sc_adata, labels_key="cell_type", batch_key="batch")
sc_model = CondSCVI(sc_adata)
sc_model.train(max_epochs=300)

DestVI.setup_anndata(st_adata, layer="counts")
st_model = DestVI.from_rna_model(st_adata, sc_model)
st_model.train(max_epochs=1000)
proportions = st_model.get_proportions()
```
