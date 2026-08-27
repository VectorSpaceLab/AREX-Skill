---
name: advanced-operations
description: "Advanced scvi-tools operations: Ray/autotune, MLflow, optional
  extras, developer extension surfaces, custom modules, Pyro internals,
  distributions, constraints, and neural building blocks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# advanced-operations

Use this sub-skill when the task involves scvi-tools internals or infrastructure beyond standard data setup, model fitting, latent extraction, or downstream biology workflows.

## Route here for

- Hyperparameter tuning through `scvi.autotune.run_autotune`, `AutotuneExperiment`, Ray Tune schedulers/searchers, HyperOpt, and scib-metrics tuning.
- Optional dependency decisions for `scvi-tools[autotune]`, `scvi-tools[mlflow]`, `scvi-tools[hub]`, `scvi-tools[parallel]`, `scvi-tools[interpretability]`, `scvi-tools[diagvi]`, RAPIDS, custom dataloaders, and hardware extras.
- MLflow experiment logging through `scvi.settings.mlflow_set_tracking_uri`, `scvi.settings.mlflow_set_experiment`, `scvi.utils.mlflow_logger`, `mlflow_log_artifact`, `mlflow_log_table`, and `mlflow_log_text`.
- Developer extensions using `scvi.model.base.BaseModelClass`, `scvi.module.base.BaseModuleClass`, `LossOutput`, `PyroBaseModuleClass`, `auto_move_data`, `scvi.nn`, and `scvi.distributions`.
- Debugging invalid custom module tensor shapes, distribution parameters, Pyro plate annotations, missing optional extras, Ray initialization, and MLflow artifact limits.

## Do not use this for

- Routine `setup_anndata`, registry-field choices, or AnnData/MuData preparation; use the data setup sub-skill.
- Standard model selection, `SCVI`/`SCANVI`/`TOTALVI` constructor choices, or basic train/query APIs; use core model and training sub-skills.
- Multimodal/spatial user workflows unless the question is about implementing or debugging the underlying module internals.

## References

- For autotune, optional extras, Ray, HyperOpt, scib-metrics, and MLflow, read [references/autotune-and-extras.md](references/autotune-and-extras.md).
- For custom model/module development, Pyro, distributions, constraints, and neural network components, read [references/developer-extension.md](references/developer-extension.md).
- For advanced failure triage, read [references/troubleshooting.md](references/troubleshooting.md).

## Quick checks before acting

- Confirm optional extras are installed before importing `scvi.autotune` or MLflow utilities; default installs may not include Ray, HyperOpt, scib-metrics, muon, or MLflow.
- Validate a model class has already registered data with its setup method before passing AnnData/MuData into `run_autotune`.
- For custom modules, test one minibatch through `module.forward(tensors, compute_loss=True)` and assert returned `inference_outputs`, `generative_outputs`, and `LossOutput` shapes before training.
- For distribution debugging, instantiate with `validate_args=True`, check positive parameters (`mu`, `theta`, `scale`, `rate`, `concentration`), and verify broadcasting across minibatch and feature axes.
