# DIN and DIEN sequence workflows

This reference covers behavior-history models where each candidate target feature is paired with one or more padded history sequences.

## Choose the model

| Need | Use | Notes |
| --- | --- | --- |
| Attention over a user's historical behavior conditioned on the current candidate item/category | `DIN` | Simpler; attention directly pools `hist_*` embeddings against the target embedding. |
| Temporal interest extraction/evolution over the history before target-conditioned attention | `DIEN` | Adds GRU-based interest extractor/evolution layers and optional auxiliary negative-sampling loss. |
| A non-target-conditioned multi-value feature such as movie genres | Any compatible single-task model with `VarLenSparseFeat` | Use [sequence-feature-shapes.md](sequence-feature-shapes.md); route non-sequence model details to `single-task-modeling`. |

## Behavior feature naming contract

`history_feature_list` (also called `behavior_feature_list` in examples) contains the **target feature names**:

```python
behavior_feature_list = ["item_id", "cate_id"]
```

For each target name `x`, the model expects:

| Role | Required name | Feature-column type | Important setting |
| --- | --- | --- | --- |
| Current target item/category | `x` | `SparseFeat` | Normal candidate feature. |
| Positive behavior history | `hist_` + `x` | `VarLenSparseFeat(SparseFeat(...))` | Set `embedding_name=x`, same embedding dimension, same event order. |
| DIEN negative history when `use_negsampling=True` | `neg_hist_` + `x` | `VarLenSparseFeat(SparseFeat(...))` | Set `embedding_name=x`, same `maxlen` and `length_name`. |

Concrete pair:

```python
from deepctr_torch.inputs import SparseFeat, VarLenSparseFeat

target_item = SparseFeat("item_id", vocabulary_size=10001, embedding_dim=8)
history_item = VarLenSparseFeat(
    SparseFeat(
        "hist_item_id",
        vocabulary_size=10001,
        embedding_dim=8,
        embedding_name="item_id",  # share target/history embedding table
    ),
    maxlen=50,
    length_name="seq_length",
)
```

For a multi-field behavior event, keep every history row aligned by timestep: `hist_item_id[i, t]` and `hist_cate_id[i, t]` must describe the same historical event.

## DIN recipe

1. Define ordinary user/context/target sparse and dense features.
2. Add one `VarLenSparseFeat` named `hist_` + target feature for each behavior feature.
3. Use one shared behavior length column such as `seq_length`; post-pad sequence arrays to `maxlen`.
4. Build model input with `get_feature_names(feature_columns)` so the dictionary includes the generated length column.
5. Instantiate `DIN(feature_columns, behavior_feature_list, ...)` and compile like other single-output models.

Minimal structure:

```python
from deepctr_torch.inputs import DenseFeat, SparseFeat, VarLenSparseFeat, get_feature_names
from deepctr_torch.models import DIN

feature_columns = [
    SparseFeat("user_id", 1000, embedding_dim=4),
    SparseFeat("item_id", 10001, embedding_dim=8),
    SparseFeat("cate_id", 100, embedding_dim=4),
    DenseFeat("price_score", 1),
    VarLenSparseFeat(SparseFeat("hist_item_id", 10001, embedding_dim=8, embedding_name="item_id"), 50, length_name="seq_length"),
    VarLenSparseFeat(SparseFeat("hist_cate_id", 100, embedding_dim=4, embedding_name="cate_id"), 50, length_name="seq_length"),
]
behavior_feature_list = ["item_id", "cate_id"]
feature_names = get_feature_names(feature_columns)
model_input = {name: arrays[name] for name in feature_names}

model = DIN(
    feature_columns,
    behavior_feature_list,
    att_hidden_size=(64, 16),
    att_activation="Dice",
    att_weight_normalization=True,
    device="cpu",
)
model.compile("adagrad", "binary_crossentropy", metrics=["binary_crossentropy"])
```

Run the bundled DIN smoke from this sub-skill when you need a quick end-to-end sanity check:

```bash
python scripts/din_sequence_smoke.py --epochs 1
```

## DIEN recipe

DIEN uses the same target/history naming contract as DIN, then adds GRU-based interest extraction/evolution.

Base DIEN without negative sampling:

```python
from deepctr_torch.models import DIEN

model = DIEN(
    feature_columns,
    behavior_feature_list,
    gru_type="GRU",      # one of GRU, AIGRU, AGRU, AUGRU
    use_negsampling=False,
    dnn_hidden_units=(64, 32),
    att_weight_normalization=True,
    device="cpu",
)
model.compile("adam", "binary_crossentropy", metrics=["binary_crossentropy"])
```

DIEN with auxiliary negative sampling:

```python
feature_columns += [
    VarLenSparseFeat(SparseFeat("neg_hist_item_id", 10001, embedding_dim=8, embedding_name="item_id"), 50, length_name="seq_length"),
    VarLenSparseFeat(SparseFeat("neg_hist_cate_id", 100, embedding_dim=4, embedding_name="cate_id"), 50, length_name="seq_length"),
]
model_input["neg_hist_item_id"] = neg_hist_item_id_array
model_input["neg_hist_cate_id"] = neg_hist_cate_id_array

model = DIEN(
    feature_columns,
    behavior_feature_list,
    gru_type="AUGRU",
    use_negsampling=True,
    alpha=1.0,
    dnn_hidden_units=(64, 32),
    device="cpu",
)
```

Negative history arrays must have the same shape, padding direction, and `seq_length` as the positive `hist_*` arrays. A practical sampler chooses an item/category not clicked at that timestep and writes `0` in padded positions.

## GRU and attention options

| Option | Applies to | Values/defaults | Guidance |
| --- | --- | --- | --- |
| `gru_type` | DIEN | `"GRU"`, `"AIGRU"`, `"AGRU"`, `"AUGRU"`; default `"GRU"` | `AUGRU` is the attention-update variant used in the package DIEN example; use uppercase names. |
| `use_negsampling` | DIEN | `False` by default | When `True`, include all `neg_hist_*` columns and arrays. |
| `alpha` | DIEN | `1.0` by default | Weight for auxiliary negative-sampling loss. |
| `att_hidden_size` | DIN | `(64, 16)` by default | Attention MLP hidden units. |
| `att_hidden_units` | DIEN | `(64, 16)` by default | Same concept as DIN's `att_hidden_size`; parameter name differs. |
| `att_activation` | DIN/DIEN | DIN default `"Dice"`; DIEN default `"relu"` | For tiny debugging batches, `"relu"` avoids Dice/BatchNorm sensitivity. |
| `att_weight_normalization` | DIN/DIEN | DIN default `False`; DIEN default `True` | `True` applies softmax over valid timesteps; `False` masks invalid timesteps with zeros. |

## Native validation candidates

After editing a workflow, the closest package-level checks are the package DIN example, the package DIEN example, and focused DIN/DIEN model tests. For fast manual validation, set epochs to `1`, disable external dataset dependencies, and prefer metrics that do not require both classes in a tiny validation split.
