# Legacy Machine-Learning Workflows

## When to read this

Read this when a task uses SimpleCV's ML wrappers, feature extractors, image-set class layouts, or original machine-learning examples.

## Classifier map

| Class | Verified constructor | Dependency note |
|---|---|---|
| `KNNClassifier` | `KNNClassifier(featureExtractors, k=1, dist=None)` | Orange-backed. |
| `NaiveBayesClassifier` | `NaiveBayesClassifier(featureExtractors)` | Orange-backed. |
| `TreeClassifier` | `TreeClassifier(featureExtractors=[], flavor='Tree', flavorDict=None)` | Orange-backed. |
| `SVMClassifier` | `SVMClassifier(featureExtractors, properties=None)` | Orange-backed; supports legacy kernel/SVM property maps. |

The classes can import even when Orange is absent, but useful training and classification require `SimpleCV.base.ORANGE_ENABLED` to be true.

## Feature extractor contract

A usable feature extractor must provide:

```python
extract(img)          # returns a flat list of feature values or None
getFieldNames()       # returns names in the same order as extract()
getNumFields()        # returns the number of fields
```

Built-in feature extractors include bag-of-features, edge histogram, Haar-like, hue histogram, and morphology extractors. Use feature-detection sub-skill guidance when a feature vector is derived from blobs or keypoints.

## Training data layout

Classifiers accept `images` aligned with `classNames`:

```python
images = [ImageSet('/data/bolts'), ImageSet('/data/nuts')]
class_names = ['bolt', 'nut']
classifier.train(images, class_names)
```

Each path or `ImageSet` corresponds to one class. Keep the order stable.

## Safe dry-run before training

Before invoking an Orange-backed classifier, validate feature extraction on a tiny local sample:

```bash
python scripts/ml_recipe.py --output /tmp/simplecv-ml.tsv
```

The helper writes a TSV-like feature table and reports whether Orange is available. This confirms the feature interface without requiring network datasets or live displays.

## Adapting the nuts-vs-bolts example

The original example downloads `nuts_bolts.zip`, uses scikit-learn, and writes to a display. For reproducible use:

1. Ask the user for an already-local dataset or permission to download.
2. Use SimpleCV to load images and extract blob measurements.
3. Keep classifier choice explicit: SimpleCV Orange wrappers vs external scikit-learn classifiers.
4. Save predictions or metrics to files instead of display windows.

## SVM/Orange property planning

`SVMClassifier` exposes legacy properties including kernel type, SVM type, `nu`, `c`, `degree`, `coef`, and `gamma`. Do not tune these until Orange is installed and a small train/test set runs.

## Save/load rules

- Save only after the feature extractors are stable.
- When loading, recreate or unpickle compatible feature extractor objects.
- Use identical feature field order between training, testing, and classification.
- If classifier state was trained with Orange, loading requires Orange too.

## Source example replacement map

| Source repo artifact | Runtime replacement |
|---|---|
| `examples/machine-learning/machine-learning_nuts-vs-bolts.py` | Reference workflow here; no automatic network download. |
| `examples/machine-learning/color_cluster.py` | Distill feature extraction/color clustering pattern; verify with local samples only. |
| `MachineLearning/*Classifier.py` | API/signature references and Orange compatibility notes. |
| ShapeContext tests | Optional native candidates if dependencies and runtime support them. |

## Validation checklist

- Is Orange available if a SimpleCV classifier wrapper is required?
- Do all feature extractors return a flat list of the declared length?
- Do `classNames` and image collections align?
- Is the dataset local and approved?
- Are display and network side effects removed from the adapted workflow?
