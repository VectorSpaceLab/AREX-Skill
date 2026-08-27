# Model Catalog

This guide helps choose a Keras-style DeepCTR model for fixed-length CTR and recommender tabular tasks.

Use this sub-skill for binary classification or regression on named feature columns. Route sequence behavior models and multitask outputs elsewhere.

## Default chooser

If you only need one model, start with `DeepFM`.

If the user asks for a more specific interaction bias:

- explicit cross layers: `DCN`, `DCNMix`, `xDeepFM`, or `EDCN`
- interaction attention or interpretability: `AFM` or `AutoInt`
- field-aware interactions: `FiBiNET`, `FLEN`, or `FwFM`
- product-based baselines: `PNN`, `NFM`, `IFM`, or `DIFM`
- legacy or specialized baselines: `CCPM`, `FNN`, `FGCNN`, `ONN`, `MLR`, or `DeepFEFM`

## Selection guide

| Model | Choose when | Constructor notes |
|---|---|---|
| `DeepFM` | You want the safest general-purpose DeepCTR Keras baseline for sparse + dense fixed-length features. It combines linear, FM, and DNN signals. | Good first choice for binary or regression. `fm_group` lets you restrict which groups contribute to FM interactions. The dense-only IO test in this repo shows it can also work without sparse fields. |
| `AFM` | You need pairwise interaction weights you can inspect later. | `use_attention=False` falls back to an FM-style interaction path. The implementation expects sparse or varlen sparse inputs in the interaction branch. |
| `DCN` | You want controllable explicit cross depth. | `cross_num` must be positive if the DNN branch is empty, and vice versa. `cross_parameterization` is `vector` or `matrix`. |
| `DCNMix` | Plain DCN is too rigid and you want a mixture-of-experts cross path. | Uses `low_rank`, `num_experts`, and `cross_num` to shape cross capacity. |
| `xDeepFM` | You want explicit higher-order crosses plus a standard DNN tower. | `cin_layer_size` controls CIN depth. `cin_split_half=True` is the usual setting. |
| `AutoInt` | You want multi-head self-attention over field embeddings instead of hand-designed crosses. | `att_layer_num` or `dnn_hidden_units` must be non-empty. `att_head_num`, `att_embedding_size`, and `att_res` control attention structure. |
| `FiBiNET` | You want field importance reweighting plus bilinear feature interaction. | `bilinear_type` is `all`, `each`, or `interaction`. `reduction_ratio` controls SENET compression. |
| `EDCN` | You want explicit and implicit branches to share information through a bridge. | `cross_num` must be positive. `bridge_type` and `tau` control bridge behavior and regulation strength. |
| `WDL` | You want a simple wide-and-deep baseline without the FM term. | Useful when you want a familiar Keras baseline close to DeepFM but with a simpler interaction story. |
| `NFM` | You want bi-interaction pooling followed by an MLP. | A clean sparse-feature baseline when you do not need attention or cross layers. |
| `PNN` | You want explicit inner-product or outer-product features. | Uses only `dnn_feature_columns`. `use_inner`, `use_outter`, and `kernel_type` (`mat`, `vec`, `num`) control the product path. |
| `FwFM` | You want field-weighted pairwise interactions. | Good when pair-specific field weights matter more than a general FM term. |
| `IFM` | You want input-aware factorization weights that vary by example. | The interaction weights are example-dependent. Sparse features are the core path. |
| `DIFM` | You want a stronger dual input-aware factorization variant. | Requires sparse features for its interaction path and combines attention-style and DNN-derived refinement. |
| `DeepFEFM` | You want field-embedded FM behavior and ablation switches for reproduction or analysis. | Good when you need to toggle `use_fefm`, `use_linear`, or `use_fefm_embed_in_dnn` during experiments. |
| `FLEN` | You want field-aware user/context/item grouping and bi-interaction pooling. | Feature columns should carry meaningful `group_name` values. |
| `FGCNN` | You want learned feature generation from sparse embeddings before the final DNN. | Convolution, pooling, and map sizes must stay aligned across layers. |
| `CCPM` | You want the convolutional click prediction baseline. | Mainly useful as a legacy convolutional baseline. The deep path expects sparse embeddings. |
| `ONN` | You want operation-aware pairwise modeling with configurable feature interactions. | Works as a specialized interaction baseline with pairwise feature operations. |
| `FNN` | You want a simpler embedding-plus-MLP baseline. | Useful as a sanity baseline when you want fewer interaction assumptions. |
| `MLR` | You want a piecewise linear or region-based model rather than a single global logit. | Special output wiring compared with the other catalog items. It uses region, base, and optional bias feature sets. |

## Practical choice rules

- If the user asks for a minimal regression model with a `DenseFeat` vector and save/load, prefer `DeepFM` unless they have a specific interaction requirement.
- If the user asks for explicit vs implicit interactions, start with `DCN` for explicit crosses, `xDeepFM` for explicit plus implicit, `AutoInt` for learned attention, and `AFM` when interpretable pairwise weights matter.
- If the user asks for a model that explains interactions, start with `AFM`, then `FiBiNET` or `AutoInt` depending on whether the user wants pairwise weights or self-attention.
- If the user asks for a field-aware layout, check whether the feature columns already carry useful `group_name` values before choosing `FLEN`, `FwFM`, or `FiBiNET`.

## Choose by task type

- `task="binary"`: the model outputs a sigmoid probability and the usual loss is `binary_crossentropy`.
- `task="regression"`: the model outputs a scalar and the usual loss is `mse`.

## See also

- [references/workflows.md](workflows.md) for compile/fit/predict/save/load recipes.
- [references/api-reference.md](api-reference.md) for exact constructor signatures.
- [references/troubleshooting.md](troubleshooting.md) for model-specific failure modes.
