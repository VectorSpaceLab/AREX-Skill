# Sequence and interest API reference

This reference summarizes the package APIs that matter for DIN, DIEN, and sequence/multi-value inputs.

## Feature-column constructors

| Constructor | Signature | Sequence-specific notes |
| --- | --- | --- |
| `SparseFeat` | `SparseFeat(name, vocabulary_size, embedding_dim=4, use_hash=False, dtype="int32", embedding_name=None, group_name="default_group")` | `embedding_name` defaults to `name`. Set `embedding_name` to the target feature name for history and negative-history columns. `use_hash=True` prints a notice; on-the-fly hashing is not implemented in the torch version. |
| `VarLenSparseFeat` | `VarLenSparseFeat(sparsefeat, maxlen, combiner="mean", length_name=None)` | Reserves `maxlen` input columns. `combiner` is used for pooled sequence features (`sum`, `mean`, `max`). `length_name` adds a length column and is required for DIN/DIEN behavior attention. |
| `DenseFeat` | `DenseFeat(name, dimension=1, dtype="float32")` | Dense values can be included beside target/history embeddings. |

`get_feature_names(feature_columns)` builds the ordered list of input keys, including generated `length_name` keys.

## DIN

```python
DIN(
    dnn_feature_columns,
    history_feature_list,
    dnn_use_bn=False,
    dnn_hidden_units=(256, 128),
    dnn_activation="relu",
    att_hidden_size=(64, 16),
    att_activation="Dice",
    att_weight_normalization=False,
    l2_reg_dnn=0.0,
    l2_reg_embedding=1e-6,
    dnn_dropout=0,
    init_std=0.0001,
    seed=1024,
    task="binary",
    device="cpu",
    gpus=None,
)
```

| Parameter | Meaning | Practical guidance |
| --- | --- | --- |
| `dnn_feature_columns` | All features used by the deep part, including target sparse, context, dense, and `hist_*` `VarLenSparseFeat` columns. | DIN passes an empty linear feature list internally; put selected features here. |
| `history_feature_list` | Target behavior feature names such as `["item_id", "cate_id"]`. | Do not include `hist_` prefixes. DIN derives history names as `hist_` + target name. |
| `att_hidden_size` | Attention MLP hidden units. | Use small values for smoke tests; larger values for production. |
| `att_activation` | Attention MLP activation. | Default `"Dice"`; `"relu"` is simpler for tiny debugging batches. |
| `att_weight_normalization` | Whether attention scores are softmax-normalized over valid timesteps. | `True` is often easier to reason about; default is `False`. |
| `task` | `"binary"` or `"regression"`. | Most DIN CTR workflows use `"binary"`. |

DIN attention uses `AttentionSequencePoolingLayer` with the target query embedding shape `(batch, 1, behavior_embedding_dim)` and history key embedding shape `(batch, maxlen, behavior_embedding_dim)`.

## DIEN

```python
DIEN(
    dnn_feature_columns,
    history_feature_list,
    gru_type="GRU",
    use_negsampling=False,
    alpha=1.0,
    use_bn=False,
    dnn_hidden_units=(256, 128),
    dnn_activation="relu",
    att_hidden_units=(64, 16),
    att_activation="relu",
    att_weight_normalization=True,
    l2_reg_dnn=0,
    l2_reg_embedding=1e-6,
    dnn_dropout=0,
    init_std=0.0001,
    seed=1024,
    task="binary",
    device="cpu",
    gpus=None,
)
```

| Parameter | Meaning | Practical guidance |
| --- | --- | --- |
| `history_feature_list` | Target behavior feature names. | Same naming contract as DIN. |
| `gru_type` | Interest evolution variant. | Supported values are `"GRU"`, `"AIGRU"`, `"AGRU"`, and `"AUGRU"`. Names are case-sensitive. |
| `use_negsampling` | Enables auxiliary loss from positive vs negative next behavior. | When `True`, add every required `neg_hist_*` feature column and input array. |
| `alpha` | Auxiliary-loss weight. | Increase/decrease to tune negative-sampling contribution. |
| `att_hidden_units` | Attention hidden units in interest evolution. | DIEN uses the plural parameter name. |
| `att_activation` | Attention activation. | Default `"relu"`. |
| `att_weight_normalization` | Whether attention scores are softmax-normalized. | Default `True` for DIEN. |

DIEN's internal flow is embedding lookup -> `InterestExtractor` GRU -> optional auxiliary loss -> `InterestEvolving` (`GRU`, `AIGRU`, `AGRU`, or `AUGRU`) -> DNN -> prediction.

## Behavior-name expansion

For `history_feature_list = ["item_id", "cate_id"]`, the model derives:

| Derived list | Values | Used by |
| --- | --- | --- |
| Target query features | `item_id`, `cate_id` | `embedding_lookup` over sparse features. |
| Positive history features | `hist_item_id`, `hist_cate_id` | `embedding_lookup` over `VarLenSparseFeat` columns. |
| Negative history features | `neg_hist_item_id`, `neg_hist_cate_id` | DIEN only when `use_negsampling=True`. |

The target and histories are concatenated along embedding dimension, so every behavior field contributes its embedding dimension to the total interest dimension.

## Sequence and attention layers

| API | Inputs | Outputs | Notes |
| --- | --- | --- | --- |
| `SequencePoolingLayer(mode="mean", supports_masking=False, device="cpu")` | `[seq_value, seq_len]` when `supports_masking=False`, or `[seq_value, mask]` when `True` | `(batch, 1, embedding_dim)` | `mode` must be `sum`, `mean`, or `max`. |
| `AttentionSequencePoolingLayer(att_hidden_units=(80, 40), att_activation="sigmoid", weight_normalization=False, return_score=False, supports_masking=False, embedding_dim=4)` | `query` `(batch, 1, E)`, `keys` `(batch, T, E)`, `keys_length` `(batch, 1)` or `(batch,)` | `(batch, 1, E)` unless `return_score=True`, then `(batch, 1, T)` | Used by DIN and DIEN. Invalid timesteps are masked before weighted sum or score return. |
| `LocalActivationUnit(hidden_units=(64, 32), embedding_dim=4, activation="sigmoid", ...)` | query `(batch, 1, E)`, behavior `(batch, T, E)` | `(batch, T, 1)` | Builds attention features `[query, key, query-key, query*key]`. |

## Compile/fit notes

DIN and DIEN inherit the same `compile`, `fit`, `predict`, `evaluate`, save/load, and callback behavior as other single-output models. Use normal binary or regression losses. DIEN's auxiliary negative-sampling loss is added internally when `use_negsampling=True`; do not add a second target for it.
