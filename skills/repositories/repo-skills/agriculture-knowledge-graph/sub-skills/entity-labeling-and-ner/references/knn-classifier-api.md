# KNN classifier API

This repository's legacy classifier predicts an entity label by comparing one Hudong item to a labeled training set.

## Core objects

### `HudongItem`

Expected fields:

- `title`
- `detail`
- `image`
- `openTypeList`
- `baseInfoKeyList`
- `baseInfoValueList`
- `label`

The legacy item loader splits `openTypeList`, `baseInfoKeyList`, and `baseInfoValueList` on `##`.

### `Classifier(model_path)`

Loads a fastText model from `model_path`.

Prerequisites:

- `pyfasttext`
- a compatible Chinese fastText model file, commonly `wiki.zh.bin`
- a labeled training set from Neo4j-backed Hudong items

### `load_trainSet(HudongList)`

Builds training-set statistics from labeled items.

What it records:

- IDF-style weights for `openTypeList`
- IDF-style weights for `baseInfoKeyList`
- counts for items that have open types or base-info keys

### `set_parameter(weight, k)`

Sets the similarity weights and `k` value.

Legacy default behavior:

- `weight = [0.2, 0.2, 0.2, 0.2, 0.2]`
- `k = 10`

### Similarity helpers

- `get_title_simi(item1, item2)`
- `get_openTypeList_simi(item1, item2)`
- `get_baseInfoKeyList_simi(item1, item2)`
- `get_baseInfoValueList_simi(item1, item2)`

Feature summary:

| Feature | Uses fastText model? | Notes |
| --- | --- | --- |
| title similarity | yes | cosine similarity on titles |
| open-type similarity | yes | pairwise average over the first 10 open types |
| base-info key overlap | no | IDF-weighted overlap |
| base-info value overlap | no | IDF-weighted equality count for shared keys |

### `KNN_predict(item)`

Predicts the label for one item.

Workflow:

1. Compare the item against each labeled training item.
2. Reuse direct label when the title already appears in the training set.
3. Compute the four feature groups above.
4. Normalize the feature vectors.
5. Sort by weighted similarity.
6. Vote across the top `k` neighbors.

## Batch prediction helpers

### `predict.create_predict(HudongItem_csv)`

Reads titles from a CSV file, fetches items from Neo4j, applies the classifier, and writes `title label` lines to a prediction file.

### `create_vec.create_predict(HudongItem_csv)`

Builds a text vector dump from titles using fastText.

## Inspection notes

- The KNN path is legacy code and depends on external data rather than a clean package boundary.
- The repo ships offline prediction outputs, so label inspection can often proceed without loading the model.
- The source contains a fragile variance calculation path inside `KNN_predict`; treat live accuracy claims cautiously if you change the implementation.
- `predict_labels.txt` and `predict_labels2.txt` are different outputs and should not be confused.
