# Troubleshooting DIN/DIEN and sequence inputs

Use this guide when a sequence-interest model fails at construction, fitting, prediction, or produces suspicious history behavior.

## Symptom-to-fix table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: please add max length column for VarLenSparseFeat of DIN/DIEN input` | DIN/DIEN behavior histories were defined without `length_name`, or no length column is present in `dnn_feature_columns`. | Add `length_name="seq_length"` to every behavior `VarLenSparseFeat`, include `model_input["seq_length"]`, and build inputs from `get_feature_names(feature_columns)`. |
| `torch.cat(): expected a non-empty list` or empty attention inputs | `history_feature_list` names do not match target `SparseFeat` names, or the history columns are not named `hist_` + target name. | For `history_feature_list=["item_id"]`, define target `SparseFeat("item_id", ...)` and history `VarLenSparseFeat(SparseFeat("hist_item_id", ...), ...)`. |
| Tensor size mismatch in attention/local activation | Target and history embedding dimensions do not align, history fields have different `maxlen`, or a behavior field is missing from one side. | Share embeddings with `embedding_name`, keep dimensions consistent, and use the same `maxlen` for all behavior-history columns. |
| Model runs but target/history behavior seems unrelated | History `SparseFeat` forgot `embedding_name` and created a separate embedding table. | Set `embedding_name` on `hist_*` and `neg_hist_*` `SparseFeat` objects to the corresponding target feature name. |
| `KeyError: 'seq_length'` or another missing input key | The input dictionary was hand-written and omitted a generated length column. | Use `feature_names = get_feature_names(feature_columns)` then build `{name: arrays[name] for name in feature_names}`. |
| DIEN with `use_negsampling=True` errors around negative history lookup or empty tensors | Required `neg_hist_*` feature columns or arrays are missing. | For every `x` in `history_feature_list`, add `VarLenSparseFeat(SparseFeat("neg_hist_" + x, ..., embedding_name=x), maxlen, length_name="seq_length")` and `model_input["neg_hist_" + x]`. |
| Valid category id `0` disappears from sequence pooling | `length_name=None` mode treats `0` as padding. | Reserve `0` for padding and encode valid ids from `1`, or provide a `length_name` and ensure downstream model semantics support it. |
| Histories look shifted or latest events are ignored | Pre-padding was used with `length_name`; masks select the first `seq_length` positions. | Post-pad behavior sequences: `[valid, valid, 0, 0]`, not `[0, 0, valid, valid]`. |
| `gru_type` unsupported | DIEN GRU type is misspelled or lower-case. | Use exactly `"GRU"`, `"AIGRU"`, `"AGRU"`, or `"AUGRU"`. |
| Hash feature warning, no real hashing behavior | `use_hash=True` is not implemented on the fly in the torch version. | Pre-hash or label-encode ids yourself before passing arrays; keep ids within `vocabulary_size`. |
| DIEN fails on very short/all-empty history batches | GRU packing and DIEN's all-zero-length path need at least one positive sequence in a batch. | Filter all-empty histories, batch them with positive-length rows, or set zero-history rows aside for a non-sequence fallback. |
| Tiny smoke with Dice or AUC is unstable | Dice uses batch statistics; AUC needs both classes. | For tiny tests, use batch size greater than one, `validation_split=0`, and `metrics=["binary_crossentropy"]`; use `att_activation="relu"` if isolating shape issues. |

## Difficult case 1: `hist_item_id` forgot `embedding_name="item_id"`

Bad pattern:

```python
SparseFeat("item_id", vocabulary_size=n_items, embedding_dim=8)
VarLenSparseFeat(
    SparseFeat("hist_item_id", vocabulary_size=n_items, embedding_dim=8),
    maxlen=50,
    length_name="seq_length",
)
```

What happens:

- The target table is named `item_id`.
- The history table defaults to `hist_item_id`.
- If dimensions differ, attention fails with a tensor shape error.
- If dimensions match, the model may run but target and history ids no longer share embedding semantics.

Fix:

```python
SparseFeat("item_id", vocabulary_size=n_items, embedding_dim=8)
VarLenSparseFeat(
    SparseFeat(
        "hist_item_id",
        vocabulary_size=n_items,
        embedding_dim=8,
        embedding_name="item_id",
    ),
    maxlen=50,
    length_name="seq_length",
)
```

Apply the same fix to paired categories and DIEN negative histories:

```python
VarLenSparseFeat(
    SparseFeat("neg_hist_item_id", vocabulary_size=n_items, embedding_dim=8, embedding_name="item_id"),
    maxlen=50,
    length_name="seq_length",
)
```

## Difficult case 2: DIEN negative sampling enabled but `neg_hist_*` fields omitted

Bad pattern:

```python
behavior_feature_list = ["item_id", "cate_id"]
model = DIEN(feature_columns, behavior_feature_list, use_negsampling=True)
```

If `feature_columns` only contains `hist_item_id` and `hist_cate_id`, DIEN cannot build `neg_keys_emb`.

Required mapping:

| Target behavior `x` | Positive history | Required negative history | Shared embedding name |
| --- | --- | --- | --- |
| `item_id` | `hist_item_id` | `neg_hist_item_id` | `item_id` |
| `cate_id` | `hist_cate_id` | `neg_hist_cate_id` | `cate_id` |

Fix pattern:

```python
feature_columns += [
    VarLenSparseFeat(SparseFeat("neg_hist_item_id", n_items, embedding_dim=8, embedding_name="item_id"), maxlen, length_name="seq_length"),
    VarLenSparseFeat(SparseFeat("neg_hist_cate_id", n_cates, embedding_dim=4, embedding_name="cate_id"), maxlen, length_name="seq_length"),
]
arrays["neg_hist_item_id"] = neg_hist_item_id
arrays["neg_hist_cate_id"] = neg_hist_cate_id
```

The negative arrays must be the same shape as the positive histories and must use `0` in padded positions.

## Fast pre-fit assertions

```python
for name in ["hist_item_id", "hist_cate_id"]:
    assert arrays[name].ndim == 2
    assert arrays[name].shape[1] == maxlen
assert arrays["hist_item_id"].shape == arrays["hist_cate_id"].shape
assert arrays["seq_length"].max() <= maxlen
assert arrays["seq_length"].min() >= 0
assert set(["item_id", "cate_id"]).issubset({fc.name for fc in feature_columns if hasattr(fc, "name")})
```

When negative sampling is enabled:

```python
for name in ["neg_hist_item_id", "neg_hist_cate_id"]:
    assert name in arrays
    assert arrays[name].shape == arrays["hist_item_id"].shape
```
