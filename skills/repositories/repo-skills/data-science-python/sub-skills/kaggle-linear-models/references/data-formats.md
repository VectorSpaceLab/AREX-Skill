# Data formats

This sub-skill covers three related tabular layouts. Pick the route that matches the data you have, not the route that looks easiest to adapt.

## 1) Dense numeric matrix + label vector

Use this format with `scripts/sklearn_svm_submission.py`.

### Files

- `train.csv`: headerless numeric matrix, one sample per row.
- `train_labels.csv`: one integer label per row, in the same order as `train.csv`.
- `test.csv`: headerless numeric matrix with the same feature count as `train.csv`.

### Expectations

- All values should be numeric.
- Labels should be integer-coded class values, such as `0` and `1`.
- The script does not guess a header row; if a file has headers, strip them first.

### Output

- One predicted class per line.
- No submission header is written by default.

### Example row

```text
0.20,-1.10,3.40,0.00
```

## 2) Criteo-like hashed CSV

Use this format with `scripts/hashed_logistic_sgd.py`.

### Files

- `train.csv`: header row with at least `Id` and `Label`, plus any number of feature columns.
- `test.csv`: header row with `Id` and the feature columns.

### Expectations

- Feature columns may contain numeric strings, categorical strings, or blanks.
- The helper treats every non-label, non-id field as a categorical token.
- A blank cell becomes the configured missing token instead of being dropped.
- The label column should be binary or at least reducible to binary.

### Output

- CSV with the header `Id,Predicted`.
- `Predicted` is a probability in the open interval `(0, 1)`.

### Example header

```text
Id,Label,I1,I2,C1,C2,C3
```

### Example row

```text
1,1,357,,red,small,east
```

## 3) Amazon-style categorical CSV

Use this format with `scripts/categorical_logistic_submission.py`.

### Files

- `train.csv`: header row with a label column, usually `ACTION`, and an id column, usually `id`.
- `test.csv`: header row with the same feature columns and usually the same id column.

### Expectations

- The helper selects every non-label, non-id column as a categorical feature.
- Feature columns can be strings or numbers; the script coerces them into a consistent categorical representation.
- Test-time categories that never appeared in training are fine because the encoder ignores them.
- Missing feature cells are filled with a placeholder token.

### Output

- CSV with the original id column and the label column name.
- By default the output header is `id,ACTION`.

### Example header

```text
id,ACTION,role,department,site,grade
```

### Example row

```text
101,1,analyst,sales,east,G1
```

## Layout selection guide

- Use the dense route when the data is already numeric and compact.
- Use the hashed route when the feature space is large, sparse, or mixed string/numeric and you want a fixed-size hash trick.
- Use the categorical route when the feature set is tabular and one-hot encoding is still practical.

## Output conventions

- Dense SVC helper: raw class predictions, one per line.
- Hashed logistic helper: `Id,Predicted` probabilities.
- Categorical logistic helper: id column plus the label column name, usually `id,ACTION`.

## Column alignment rules

- Dense matrices must keep the same feature count in train and test.
- Hashed CSVs must keep the same named feature columns in train and test whenever possible, but the helper ignores the label and id columns by name.
- Categorical CSVs are reindexed to the training feature columns before encoding, so missing or extra test columns do not break the route.

If your data does not match one of these layouts, stop and normalize the files before fitting a model.