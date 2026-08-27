# LimiX model and config overview

## When to read

Read this before choosing a checkpoint, task route, inference config, device, or validation strategy for LimiX.

## Task support

LimiX is a structured-data foundation model for tabular tasks. The inspected repository exposes one main predictor class, `LimiXPredictor`, and supports these user-facing workflows:

| Workflow | Route | Notes |
| --- | --- | --- |
| Classification | `sub-skills/predictor-inference/` or `sub-skills/benchmark-cli/` | Returns class-probability arrays. Examples use ROC AUC and accuracy. |
| Regression | `sub-skills/predictor-inference/` or `sub-skills/benchmark-cli/` | Returns a torch tensor in normalized target space in the direct API examples. Benchmark CLI denormalizes prediction CSV values. |
| Missing-value imputation | `sub-skills/predictor-inference/` | Uses `mask_prediction=True` with a regression-style call and an MVI-specific non-retrieval config. |
| Retrieval ensemble inference | `sub-skills/retrieval-optimization/` | Retrieval configs compute sample attention and select train samples; use GPU/CUDA and memory planning. |
| Config/preprocess debugging | `sub-skills/configuration-preprocessing/` | Use bundled config inspector/generator and preprocessing references. |

## Model families

| Model family | Public checkpoint signal | Documented task support |
| --- | --- | --- |
| LimiX-16M | `LimiX-16M.ckpt` | classification, regression, missing-value imputation |
| LimiX-2M | `LimiX-2M.ckpt` | classification, regression; smaller/faster/lower-memory than 16M |

Match 16M/2M retrieval config families to the checkpoint family when possible. Non-retrieval configs can be used for either family when the model checkpoint itself is compatible.

## Config selection matrix

| User need | Preferred config style | Device notes |
| --- | --- | --- |
| CPU setup or limited CPU inference experiment | `*_default_noretrieval.json` | CPU rejects retrieval and disables mixed precision. Full model runtime may still be slow. |
| Classification with best documented retrieval performance | `cls_default_16M_retrieval.json` or `cls_default_2M_retrieval.json` | GPU-first; retrieval is memory sensitive. |
| Regression with best documented retrieval performance | `reg_default_16M_retrieval.json` or `reg_default_2M_retrieval.json` | GPU-first; retrieval is memory sensitive. |
| Missing-value imputation | `reg_default_noretrieval_MVI.json` | Use `mask_prediction=True`; MVI config avoids the `power` preprocessing branch. |
| Safe config generation from scratch | bundled `sub-skills/configuration-preprocessing/scripts/generate_noretrieval_config.py` | Generates no-retrieval configs and avoids checkpoint inference. |
| Validate an unknown config | bundled `sub-skills/configuration-preprocessing/scripts/inspect_config.py` | Reports pipeline count, retrieval use, MVI compatibility, CPU safety, and malformed schema. |

## Dataset fit guidance

The public usage guidance targets tabular datasets under roughly 50,000 samples and under roughly 10,000 features. The classification benchmark script skips datasets with 50,000 or more training rows and classification targets with fewer than 2 or more than 10 classes. Larger datasets can increase GPU memory pressure and may reduce the advantage versus classical supervised tabular models.

## Verification boundaries

A safe creation/verification pass can check imports, config schema, helper scripts, and synthetic data-layout fixtures. It cannot prove full LimiX inference unless a local checkpoint is loaded and a real prediction command completes. Treat these as separate evidence levels:

1. **Config/import ready**: imports and JSON config parse pass.
2. **Setup smoke ready**: helper scripts validate local data/config and torch/CUDA availability if requested.
3. **Checkpoint inference verified**: a local `.ckpt` is loaded and `LimiXPredictor.predict()` or the benchmark CLI completes on a bounded dataset.
4. **Retrieval/benchmark verified**: retrieval configs or benchmark loops complete on the intended GPU/data scale.

Do not collapse higher evidence levels into lower ones in reports or user answers.
