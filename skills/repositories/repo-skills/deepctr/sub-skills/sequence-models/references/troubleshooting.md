# Sequence Model Troubleshooting

Use this guide when a DeepCTR DIN, BST, DIEN, or DSIN task fails to build, ignores history, or produces sequence shape errors.

## History feature not found or ignored

Symptom:

- User says `behavior_feature_list=["item_id"]`, but their history column is `item_id_hist`.
- Model builds but the intended history field is pooled as a generic `VarLenSparseFeat` instead of used as attention history.

Cause:

- DIN, BST, and DIEN select history fields by exact name `hist_` + behavior feature. They do not discover names by suffix or semantic similarity.

Fix:

```python
behavior_feature_list = ["item_id"]

# wrong for DIN/BST/DIEN attention history
VarLenSparseFeat(SparseFeat("item_id_hist", item_count + 1, embedding_dim=8), maxlen=4)

# correct
VarLenSparseFeat(
    SparseFeat("hist_item_id", item_count + 1, embedding_dim=8, embedding_name="item_id"),
    maxlen=4,
    length_name="seq_length",
)
```

If the task is generic pooled multi-value features rather than candidate-to-history attention, route to `data-and-feature-columns`.

## Embeddings are not shared between candidate and history

Symptom:

- Attention shape errors, unexpectedly separate item/history embeddings, or poor behavior in a tiny reproduction.

Cause:

- Candidate `item_id` and history `hist_item_id` represent the same dictionary but use different embedding tables.

Fix:

```python
SparseFeat("item_id", item_count + 1, embedding_dim=8)
VarLenSparseFeat(
    SparseFeat("hist_item_id", item_count + 1, embedding_dim=8, embedding_name="item_id"),
    maxlen=4,
    length_name="seq_length",
)
```

When multiple feature columns share the same `embedding_name`, keep `vocabulary_size`, `embedding_dim`, and `trainable` consistent. DeepCTR validates these compatibility constraints.

## `0` is used as a valid id

Symptom:

- Valid categories disappear from histories/sessions.
- Sequence pooling or attention acts as though early ids are padding.

Cause:

- `0` is the padding/mask id for sequence/session arrays. Several sequence paths also use `mask_zero=True` for shared embeddings.

Fix:

- Re-encode valid categorical ids from `1` upward.
- Set `vocabulary_size` to at least `max_valid_id + 1`.
- Keep padded entries as `0`.

## Missing `seq_length`

Symptom:

- Keras complains about missing input `seq_length`.
- BST fails immediately because `features["seq_length"]` is missing.
- DIEN fails because it reads `user_behavior_length = features["seq_length"]`.

Fix:

```python
VarLenSparseFeat(SparseFeat("hist_item", 4, embedding_dim=8, embedding_name="item"), maxlen=4, length_name="seq_length")
x["seq_length"] = np.array([3, 3, 2])
```

Use one `seq_length` per row for the flat history length. It may be shape `(batch,)` or `(batch, 1)`.

## Missing `sess_length` in DSIN

Symptom:

- DSIN builds a model that expects an input named `sess_length`, but the input dict was built only from `get_feature_names(feature_columns)`.

Cause:

- DSIN creates `sess_length` as a separate Keras `Input`; it is not represented by a `VarLenSparseFeat` and is not returned by `get_feature_names(feature_columns)`.

Fix:

```python
x = {name: feature_dict[name] for name in get_feature_names(feature_columns)}
x["sess_length"] = np.array([2, 1, 0])
```

`sess_length` is the number of valid sessions in the row, not the number of valid events inside each session.

## DSIN field names are incomplete

Symptom:

- DSIN raises a key error for `sess_1_item`, `sess_0_cate_id`, or similar.

Cause:

- For every index from `0` to `sess_max_count - 1` and every name in `sess_feature_list`, DSIN looks up `sess_<index>_<feature>`.

Fix checklist:

```text
sess_feature_list = ["item", "cate_id"]
sess_max_count = 2
required fields:
  sess_0_item
  sess_0_cate_id
  sess_1_item
  sess_1_cate_id
  sess_length
```

Pad absent sessions with all-zero arrays and reduce `sess_length` for that row.

## DSIN `hist_emb_size` mismatch

Symptom:

```text
ValueError: hist_emb_size must equal to att_embedding_size * att_head_num
```

Cause:

- DSIN sums the embedding dimensions of base sparse features listed in `sess_feature_list` and requires that total width to equal `att_embedding_size * att_head_num`.

Fix examples:

- If `SparseFeat("item", ..., embedding_dim=4)` and `SparseFeat("cate_id", ..., embedding_dim=4)`, then `hist_emb_size = 8`.
- Compatible DSIN choices include `att_embedding_size=2, att_head_num=4` or `att_embedding_size=1, att_head_num=8`.
- If only `item` is in `sess_feature_list` with embedding dim `4`, use `att_embedding_size=1, att_head_num=4` or `att_embedding_size=2, att_head_num=2`.

## DIN/DIEN Dice activation failures on newer TensorFlow

Symptom:

- A small model build, save/load, or smoke check fails in the Dice activation path.

Cause:

- DeepCTR 0.9.4 defaults several sequence attention activations to `"dice"`. The native tests already switch DIN to `"sigmoid"` on newer TensorFlow for compatibility.

Fix:

```python
model = DIN(feature_columns, behavior_feature_list, att_activation="sigmoid")
model = DIEN(feature_columns, behavior_feature_list, att_activation="sigmoid")
```

Use Dice only when required by the experiment and verified in the target TensorFlow runtime. Use the Keras workflow skill for save/load custom-object details.

## DIEN GRU and negative-sampling caveats

Symptom:

- DIEN returns early in TF2 native-style checks, or `AUGRU`/negative sampling is unstable.

Cause:

- DIEN depends on custom dynamic GRU utilities and contains legacy/session-initialization code. Negative sampling adds `neg_hist_` inputs and an auxiliary loss.

Fix path:

1. Start with `gru_type="GRU"`, `use_negsampling=False`, and a tiny dataset.
2. Confirm `hist_` names and `seq_length` first.
3. Add `AIGRU` or `AGRU` only after GRU works in the target runtime.
4. For `AUGRU` with `use_negsampling=True`, add every `neg_hist_<feature>` field with the same maxlen and compatible embedding_name as its positive history field.

## Nested VarLen of VarLen unsupported

Symptom:

- User wants `hist_item_categories` shaped like `(batch, history_len, categories_per_item)` for DIN attention.

Cause:

- DeepCTR's `VarLenSparseFeat` represents one padded vector per row, not a nested 3D sequence of multi-value behaviors. DIN/BST/DIEN attention expects candidate behavior sparse ids and flat padded history sequences.

Fix options:

- Pick one representative category per behavior.
- Map each category set to a single categorical id before model input.
- Pre-pool category sets outside the model and build a custom model.
- Route generic multi-value feature encoding to `data-and-feature-columns` if there is no candidate-to-history attention requirement.

## Minimal debug order

1. Print `get_feature_names(feature_columns)` and compare to `x.keys()`.
2. Check all sequence arrays have shape `(batch, maxlen)`.
3. Check length arrays have one value per row.
4. Check padding ids are `0` and valid ids are `>= 1`.
5. Check `embedding_name` sharing for behavior/history/session pairs.
6. Run the bundled tiny smoke script for a known-good DIN/BST/DSIN baseline.
