# LimiX inference config catalog

This reference summarizes the LimiX inference JSON formats and observed default config families. It is self-contained: future agents should not need the original checkout's `config/` directory to understand the choices below.

## Config-list schema

A LimiX inference config is a JSON **list**. Each list item is one preprocessing/inference pipeline, and `LimiXPredictor` uses the list length as the ensemble estimator count. An empty list fails with the predictor assertion that the number of pipelines is zero.

A pipeline item is a JSON object with these common top-level blocks:

| Block | Required by observed defaults? | Meaning |
|---|---:|---|
| `RebalanceFeatureDistribution` | yes | Numeric distribution transforms, optional passthrough of original features, optional SVD expansion, and treatment of categorical/discrete columns. |
| `CategoricalFeatureEncoder` | yes | Categorical handling strategy such as strict ordinal shuffling, one-hot, numeric passthrough, or no transform. |
| `FeatureShuffler` | yes | Random or rotated feature-column reordering. |
| `FingerprintFeatureEncoder` | optional | Boolean flag; if true, appends a salted row-fingerprint feature. |
| `PolynomialInteractionGenerator` | optional | Adds randomized pairwise interaction features after standardization. |
| `retrieval_config` | yes | Retrieval and subsampling switches. Missing this block causes predictor pipeline construction to fail. |

`FilterValidFeatures` is always inserted by the predictor even though it has no config block.

## Observed config matrix

| Config name | Task/use | Model family | Retrieval | MVI | Pipelines | Main preprocessing templates | Selected retrieval keys | CPU-safe config? |
|---|---|---|---:|---:|---:|---|---|---:|
| `cls_default_16M_retrieval.json` | classification | 16M | yes | no | 4 | 2× `quantile_uniform_10` + strict ordinal shuffle + SVD; 2× `None` worker + numeric encoding | `retrieval_len=389`, `sub_feature_ratio=1`, `use_cluster=true`, `cluster_num=22`, `threshold=0.85`, `dynamic_ratio=0.4`, `mixed_method="min"`, `use_threshold=false`, `use_dynamic=false`, `sample_ratio=389` | no |
| `cls_default_2M_retrieval.json` | classification | 2M | yes | no | 4 | same as 16M classification retrieval | `retrieval_len="dynamic"`, `sub_feature_ratio=1`, `use_cluster=true`, `cluster_num=47`, `threshold=0.95`, `dynamic_ratio=0.5`, `mixed_method="max"`, `use_threshold=true`, `use_dynamic=true` | no |
| `cls_default_noretrieval.json` | classification | 16M or 2M | no | no | 4 | 2× `quantile_uniform_10` + strict ordinal shuffle + SVD; 2× `None` worker + numeric encoding | `subsample_ratio=0.7`, `subsample_type="sample"`, `use_type="mixed"`; retrieval/attention flags false | yes |
| `reg_default_16M_retrieval.json` | regression | 16M | yes | no | 8 | 4× `quantile_uniform_all_data` + strict ordinal shuffle + SVD; 4× `power` + one-hot encoding | `retrieval_len="dynamic"`, `sub_feature_ratio=1`, `use_cluster=true`, `cluster_num=45`, `threshold=0.85`, `dynamic_ratio=0.35`, `mixed_method="max"`, `use_threshold=false`, `use_dynamic=true` | no |
| `reg_default_2M_retrieval.json` | regression | 2M | yes | no | 8 | same as 16M regression retrieval | `retrieval_len="dynamic"`, `sub_feature_ratio=1`, `use_cluster=true`, `cluster_num=50`, `threshold=0.67`, `dynamic_ratio=0.45`, `mixed_method="max"`, `use_threshold=true`, `use_dynamic=true` | no |
| `reg_default_noretrieval.json` | regression | 16M or 2M | no | no | 8 | 4× `quantile_uniform_all_data` + strict ordinal shuffle + SVD; 4× `power` + one-hot encoding | `subsample_ratio=0.7`, `subsample_type="sample"`, `use_type="mixed"`; retrieval/attention flags false | yes |
| `reg_default_noretrieval_MVI.json` | missing-value imputation workflow with regression call | 16M MVI workflow | no | yes | 8 | 4× `quantile_uniform_all_data` + strict ordinal shuffle + SVD; 4× `None` worker + one-hot encoding, `discrete_flag=true` | `subsample_ratio=0.7`, `subsample_type="sample"`, `use_type="mixed"`; retrieval/attention flags false | config is CPU-safe, but full MVI inference still needs a local checkpoint and may require CUDA/GPU |

All observed retrieval configs use sample-level retrieval: `subsample_type="sample"`, `use_type="only_sample"`, `retrieval_before_preprocessing=false`, `calculate_sample_attention=true`, and `calculate_feature_attention=false`.

## Key retrieval_config fields

| Key | Values seen or expected | Operational note |
|---|---|---|
| `use_retrieval` | boolean | If true, retrieval attention and subsampling steps are added. CPU predictor construction rejects retrieval when the first pipeline has this set. Treat any retrieval-enabled pipeline as not CPU-safe. |
| `retrieval_before_preprocessing` | boolean | Observed defaults set false, so retrieval attention is inserted after preprocessing transforms. If true, attention/subsampling runs before polynomial/filter/rebalance/encoding steps. |
| `calculate_sample_attention` | boolean | Must be true for sample-level retrieval. |
| `calculate_feature_attention` | boolean | Required for feature-level retrieval or mixed sample+feature use. Observed sample-only retrieval keeps it false. |
| `subsample_type` | `"sample"`, `"feature"` | Determines whether retrieval selects samples or features. Observed defaults use sample retrieval. |
| `use_type` | `"only_sample"`, `"mixed"` | `mixed` requires feature attention in predictor assertions. Observed retrieval configs use `only_sample`; non-retrieval defaults often retain `mixed` but it is inactive. |
| `retrieval_len` | integer or `"dynamic"` | Passed to retrieval inference for sample selection count. Absent from non-retrieval configs. |
| `sub_feature_ratio` | number | Used as the subsample ratio when `SubSampleData.fit` is called; observed retrieval configs set `1`. |
| `use_cluster`, `cluster_num` | boolean, integer | Retrieval selection modifiers; tune via the retrieval sub-skill rather than changing blindly. |
| `use_threshold`, `threshold` | boolean, number | Threshold gating for retrieval. |
| `use_dynamic`, `dynamic_ratio`, `mixed_method` | boolean/string/number | Dynamic retrieval behavior and score combination. Detailed search semantics belong to `../retrieval-optimization/SKILL.md`. |
| `subsample_ratio` | number | Present in non-retrieval configs; inactive when `use_retrieval=false`. |

## Source helper behavior

The source helper names are misspelled as `generate_infenerce_config(args)` and `sample_inferece_params(rng, sample_num=2, repeat_num=2)`.

`generate_infenerce_config(args)` writes a no-retrieval JSON list to `args.inference_config_path`. Its helper-style list has 4 pipeline items:

- 2× `RebalanceFeatureDistribution(worker_tags=["quantile"], discrete_flag=false, original_flag=true, svd_tag="svd")`, `CategoricalFeatureEncoder(encoding_strategy="ordinal_strict_feature_shuffled")`, and `FeatureShuffler(mode="shuffle")`.
- 2× `RebalanceFeatureDistribution(worker_tags=[null], discrete_flag=true, original_flag=false, svd_tag=null)`, `CategoricalFeatureEncoder(encoding_strategy="numeric")`, and `FeatureShuffler(mode="shuffle")`.
- `retrieval_config` has `use_retrieval=false`, both attention flags false, `subsample_ratio=1`, and `subsample_type/use_type=null`.

The helper-style `"quantile"` worker tag is not one of the explicit worker cases in the current preprocessing implementation; it falls back to identity behavior. Use the bundled script's catalog preset when you need observed `quantile_uniform_*` defaults instead of exact helper compatibility.

The bundled `scripts/generate_noretrieval_config.py` can reproduce this helper-style baseline without importing the original repository. It can also emit catalog-style observed task presets when invoked with its catalog preset.

`sample_inferece_params` depends on Hyperopt, returns `(hyperopt_configs, base_config)`, and does not write a file. The sampled config list can include `FingerprintFeatureEncoder`, `PolynomialInteractionGenerator`, additional rebalance worker tags, and a separate `base_config` with `softmax_temperature` and `seed` for `set_inference_config`.

## CPU and checkpoint caveats

- Use no-retrieval configs for CPU. Retrieval-enabled configs are not CPU-compatible and are typically GPU-memory heavy.
- Non-retrieval config validation and preprocessing inspection do not prove that full LimiX inference works. Full model use needs a local LimiX checkpoint; CUDA/GPU may be required for practical classification, regression, retrieval, and MVI runs.
- If a task asks for prediction outputs rather than config validation, route to `../predictor-inference/SKILL.md` after selecting or generating a config.
