# Integrated TFLearn Recipes

Use this reference when a task crosses multiple sub-skills. It keeps the root skill router-like while giving future agents one safe composition pattern.

## Offline Tabular Classifier with Checkpoint Save/Load

This recipe combines:

- CSV validation from [`data-input-pipelines`](../sub-skills/data-input-pipelines/SKILL.md)
- Layer and `regression` wiring from [`layers-and-ops`](../sub-skills/layers-and-ops/SKILL.md)
- Named feeds and checkpoint stems from [`training-and-persistence`](../sub-skills/training-and-persistence/SKILL.md)

Scenario: a Titanic-style CSV has columns:

```text
survived,pclass,name,sex,age,sibsp,parch,ticket,fare
```

The target is original column `0`, and text columns `name` and `ticket` are ignored by original column indices `2,7`. The remaining `sex` column must be encoded before converting features to `np.float32`.

### 1. Validate the CSV plan

From the root skill directory or another directory with the skill path available:

```bash
python sub-skills/data-input-pipelines/scripts/validate_tflearn_tabular_data.py \
  --csv data.csv \
  --target-column 0 \
  --ignore-columns 2,7 \
  --categorical-labels \
  --n-classes 2
```

Expected interpretation:

- `survived` is the target.
- `name` and `ticket` are ignored.
- Final features should be `pclass`, encoded `sex`, `age`, `sibsp`, `parch`, and `fare`.
- Feature count is `6`, so the graph input shape is `[None, 6]`.

If the validator reports conversion issues for `sex`, encode it before training:

```python
row["sex"] = 1.0 if row["sex"] == "female" else 0.0
```

### 2. Build, train, save, and reload

```python
import os
import tempfile
import numpy as np
import tensorflow.compat.v1 as tf
import tflearn
from tflearn.data_utils import load_csv

tf.disable_v2_behavior()

CSV_PATH = "data.csv"
MODEL_DIR = tempfile.mkdtemp(prefix="tflearn-tabular-")
CHECKPOINT_STEM = os.path.join(MODEL_DIR, "tabular_classifier.tflearn")


def encode_rows(rows):
    encoded = []
    for row in rows:
        # After load_csv removes target column 0 and ignores original columns 2,7,
        # the remaining row order is pclass, sex, age, sibsp, parch, fare.
        row = list(row)
        row[1] = 1.0 if row[1] == "female" else 0.0
        encoded.append(row)
    return np.asarray(encoded, dtype=np.float32)


data, labels = load_csv(
    CSV_PATH,
    target_column=0,
    columns_to_ignore=[2, 7],
    categorical_labels=True,
    n_classes=2,
)
X = encode_rows(data)
Y = np.asarray(labels, dtype=np.float32)

with tf.Graph().as_default():
    net = tflearn.input_data(shape=[None, 6], name="input")
    net = tflearn.fully_connected(net, 16, activation="relu", name="dense1")
    net = tflearn.fully_connected(net, 2, activation="softmax", name="output")
    net = tflearn.regression(
        net,
        optimizer="adam",
        loss="categorical_crossentropy",
        learning_rate=0.001,
        name="target",
    )
    model = tflearn.DNN(net, tensorboard_verbose=0)
    model.fit(
        {"input": X},
        {"target": Y},
        n_epoch=2,
        batch_size=min(16, len(X)),
        snapshot_epoch=False,
        run_id="tabular_classifier_smoke",
    )
    before = model.predict(X[:2])
    model.save(CHECKPOINT_STEM)

with tf.Graph().as_default():
    net = tflearn.input_data(shape=[None, 6], name="input")
    net = tflearn.fully_connected(net, 16, activation="relu", name="dense1")
    net = tflearn.fully_connected(net, 2, activation="softmax", name="output")
    net = tflearn.regression(
        net,
        optimizer="adam",
        loss="categorical_crossentropy",
        learning_rate=0.001,
        name="target",
    )
    restored = tflearn.DNN(net, tensorboard_verbose=0)
    restored.load(CHECKPOINT_STEM)
    after = restored.predict(X[:2])

print("checkpoint stem:", CHECKPOINT_STEM)
print("before shape:", before.shape, "after shape:", after.shape)
```

### 3. Validation checklist

- Run the CSV validator before `load_csv` if the target/ignore plan is new.
- Use a fresh `tf.Graph()` for the original and restored model.
- Use named feeds: `{"input": X}` and `{"target": Y}`.
- Load the checkpoint stem (`tabular_classifier.tflearn`), not `.index`.
- Keep `MODEL_DIR` explicit and temporary/experiment-scoped.
- Treat this as an offline smoke. It verifies route/API/checkpoint behavior, not model quality.

### 4. Where to go deeper

- If column conversion or label shape fails, use [`data-input-pipelines/references/troubleshooting.md`](../sub-skills/data-input-pipelines/references/troubleshooting.md).
- If layer shape, activation, or `regression` wiring fails, use [`layers-and-ops/references/troubleshooting.md`](../sub-skills/layers-and-ops/references/troubleshooting.md).
- If `fit`, feed names, TensorBoard, save, or restore fails, use [`training-and-persistence/references/troubleshooting.md`](../sub-skills/training-and-persistence/references/troubleshooting.md).
