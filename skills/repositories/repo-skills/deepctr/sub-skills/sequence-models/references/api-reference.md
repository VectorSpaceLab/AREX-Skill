# Sequence Model API Reference

These are the DeepCTR 0.9.4 public model builders. Import model builders from `deepctr.models` where available, and use `deepctr.feature_column` for feature columns.

## Common conventions

Each builder returns a TensorFlow/Keras `Model`. `dnn_feature_columns` is the complete set of candidate, context, dense, and sequence/session columns consumed by the model. `task` is `"binary"` by default and may be `"regression"`.

Use the feature-column and input contracts in [sequence-inputs.md](sequence-inputs.md) before applying these signatures.

## DIN

```python
from deepctr.models import DIN

model = DIN(
    dnn_feature_columns,
    history_feature_list,
    dnn_use_bn=False,
    dnn_hidden_units=(256, 128, 64),
    dnn_activation="relu",
    att_hidden_size=(80, 40),
    att_activation="dice",
    att_weight_normalization=False,
    l2_reg_dnn=0,
    l2_reg_embedding=1e-6,
    dnn_dropout=0,
    seed=1024,
    task="binary",
)
```

Parameter notes:

- `history_feature_list` contains candidate/base names, such as `["item_id", "cate_id"]`; do not put `hist_` prefixes here.
- `att_activation` controls the local activation unit. The shipped default is `"dice"`; use `"sigmoid"` for a compatibility smoke on newer TensorFlow when Dice construction/serialization fails.
- `att_weight_normalization=True` normalizes attention scores across valid history positions; it is useful when inspecting weighted attention behavior.
- `dnn_hidden_units=()` is a valid minimal DNN choice when a tiny build needs fewer parameters.

## BST

```python
from deepctr.models import BST

model = BST(
    dnn_feature_columns,
    history_feature_list,
    transformer_num=1,
    att_head_num=8,
    use_bn=False,
    dnn_hidden_units=(256, 128, 64),
    dnn_activation="relu",
    l2_reg_dnn=0,
    l2_reg_embedding=1e-6,
    dnn_dropout=0.0,
    seed=1024,
    task="binary",
)
```

Parameter notes:

- BST uses the same `hist_` + behavior naming and `seq_length` input as DIN.
- `att_head_num` is the number of Transformer heads. The implementation derives each transformer's per-head embedding size from the concatenated history embedding width; choose an embedding width divisible by the head count.
- Increase `transformer_num` only after a one-layer build works. Keep the smoke configuration small.

## DIEN

```python
from deepctr.models import DIEN

model = DIEN(
    dnn_feature_columns,
    history_feature_list,
    gru_type="GRU",
    use_negsampling=False,
    alpha=1.0,
    use_bn=False,
    dnn_hidden_units=(256, 128, 64),
    dnn_activation="relu",
    att_hidden_units=(64, 16),
    att_activation="dice",
    att_weight_normalization=True,
    l2_reg_dnn=0,
    l2_reg_embedding=1e-6,
    dnn_dropout=0,
    seed=1024,
    task="binary",
)
```

Parameter notes:

- Supported `gru_type` strings in this version are `"GRU"`, `"AIGRU"`, `"AGRU"`, and `"AUGRU"`.
- `use_negsampling=True` adds an auxiliary loss and requires `neg_hist_<feature>` fields for every history behavior feature. Use `alpha` to weight that loss.
- The implementation's DIEN RNN path is sensitive to TensorFlow generation. The native test matrix treats several DIEN paths as legacy/version-sensitive; start with `gru_type="GRU"`, `use_negsampling=False`, and `att_activation="sigmoid"` for a bounded check.
- A full negative-sampling training run is outside this tiny helper. Do not invent negative-history fields with mismatched lengths or embedding names.

## DSIN

```python
from deepctr.models import DSIN

model = DSIN(
    dnn_feature_columns,
    sess_feature_list,
    sess_max_count=5,
    bias_encoding=False,
    att_embedding_size=1,
    att_head_num=8,
    dnn_hidden_units=(256, 128, 64),
    dnn_activation="relu",
    dnn_dropout=0,
    dnn_use_bn=False,
    l2_reg_dnn=0,
    l2_reg_embedding=1e-6,
    seed=1024,
    task="binary",
)
```

Parameter notes:

- `sess_feature_list` contains the base names, for example `["item", "cate_id"]`; the input columns are generated as `sess_0_item`, `sess_0_cate_id`, and so on.
- `sess_max_count` must match the number of session index groups prepared in `dnn_feature_columns` and in the input dictionary.
- `sess_length` is a separate model input and gives the number of valid sessions per row. It is not a sequence length per session.
- DSIN validates that the concatenated embedding width of the base `sess_feature_list` equals `att_embedding_size * att_head_num`. For two 4-wide behavior embeddings, `hist_emb_size=8`, so `att_embedding_size=2, att_head_num=4` is compatible; `1 * 8` is also compatible.
- `bias_encoding=True` uses session bias encoding; `False` uses positional encoding in the Transformer.

## Task and shape expectations

```python
model.compile("adam", "binary_crossentropy", metrics=["binary_crossentropy"])
pred = model.predict(x, batch_size=len(next(iter(x.values()))), verbose=0)
assert pred.shape == (batch_size, 1)
```

The model builders do not preprocess raw sequences, split sessions, or infer a missing length field. Prepare those tensors before model construction. Generic compile/fit/save/load details belong to the Keras workflow skill; the bundled tiny script only uses one bounded `fit` call as a smoke.
