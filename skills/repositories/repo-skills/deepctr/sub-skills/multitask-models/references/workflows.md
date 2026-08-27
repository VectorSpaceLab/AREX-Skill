# Workflows

## Census-style two-label preprocessing

Use this pattern when one table produces two binary labels, such as income and
marital-status style targets:

1. derive two labels from the same source table
2. encode sparse fields once
3. scale dense fields once
4. build one shared feature-column list
5. train one multitask model with output names in the intended order

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, MinMaxScaler

from deepctr.feature_column import SparseFeat, DenseFeat, get_feature_names
from deepctr.models import MMOE

# tiny census-style sample, kept fully self-contained
frame = pd.DataFrame(
    {
        "class_worker": ["Private", "Self-emp-not-inc", "Private", "State-gov"],
        "education": ["Bachelors", "HS-grad", "Masters", "Some-college"],
        "sex": [" Male", " Female", " Female", " Male"],
        "age": [25, 44, 39, 31],
        "wage_per_hour": [0, 20, 0, 8],
        "income_50k": [" - 50000.", " 50000+.", " - 50000.", " 50000+."],
        "marital_stat": [" Never married", " Married-civ-spouse", " Never married", " Married-civ-spouse"],
    }
)

frame["label_income"] = frame["income_50k"].map({" - 50000.": 0, " 50000+.": 1}).astype("int32")
frame["label_marital"] = (frame["marital_stat"] == " Never married").astype("int32")
frame = frame.drop(columns=["income_50k", "marital_stat"])

sparse_features = ["class_worker", "education", "sex"]
dense_features = ["age", "wage_per_hour"]

for name in sparse_features:
    frame[name] = LabelEncoder().fit_transform(frame[name])
frame[dense_features] = MinMaxScaler((0, 1)).fit_transform(frame[dense_features])

feature_columns = [
    SparseFeat(name, frame[name].max() + 1, embedding_dim=4)
    for name in sparse_features
] + [DenseFeat(name, 1) for name in dense_features]

feature_names = get_feature_names(feature_columns)
train, test = train_test_split(frame, test_size=0.5, random_state=2024)
train_x = {name: train[name].values for name in feature_names}
test_x = {name: test[name].values for name in feature_names}

model = MMOE(
    feature_columns,
    num_experts=2,
    expert_dnn_hidden_units=(8,),
    tower_dnn_hidden_units=(8,),
    gate_dnn_hidden_units=(),
    task_types=["binary", "binary"],
    task_names=["label_income", "label_marital"],
)

# list style: order must match model.output_names
model.compile("adam", loss=["binary_crossentropy", "binary_crossentropy"])
model.fit(
    train_x,
    [train["label_income"].values, train["label_marital"].values],
    batch_size=2,
    epochs=1,
    verbose=0,
)

# dict style: order is name-driven, so it is harder to miswire
losses = {name: "binary_crossentropy" for name in model.output_names}
targets = {
    "label_income": test["label_income"].values,
    "label_marital": test["label_marital"].values,
}
model.compile("adam", loss=losses)
model.fit(test_x, targets, batch_size=2, epochs=1, verbose=0)

preds = model.predict(test_x, batch_size=2, verbose=0)
print(model.output_names)  # ['label_income', 'label_marital']
print([p.shape for p in preds])
```

## Compile and target packing rules

- Use a list when you already know the output order.
- Use a dict when the model has many outputs or the target order is easy to get
  wrong.
- With `fit(..., y_list)`, the list length must match the number of outputs.
- With `fit(..., y_dict)`, the dict keys must match `model.output_names`.
- For binary multitask models, `binary_crossentropy` is the usual loss.
- For mixed multitask models, pair `binary_crossentropy` and
  `mean_squared_error` in the correct output order.

## Constructor choice guide

| Need | Preferred model |
|---|---|
| simplest shared trunk across tasks | `SharedBottom` |
| expert routing with shared experts | `MMOE` |
| progressive shared + task-specific experts | `PLE` |
| click/conversion style joint modeling | `ESMM` |

## ESMM-specific workflow note

ESMM is not a generic two-head multitask model. Its second output is the
`CTR × CVR` product, and the common output order is `[ctr, ctcvr]`.
Use ESMM when your problem is click-through and conversion style modeling.
If you want two independent labels, use `SharedBottom`, `MMOE`, or `PLE`
instead.

## Tiny smoke usage

Run the bundled helper when you want a very small synthetic check without any
external dataset. Invoke the model family you want to confirm:

```bash
python scripts/multitask_tiny_smoke.py --model mmoe --json
python scripts/multitask_tiny_smoke.py --model sharedbottom --json
python scripts/multitask_tiny_smoke.py --model ple --json
python scripts/multitask_tiny_smoke.py --model esmm --json
```

Use one command per model when you want to confirm output order or task wiring
for a specific architecture.

