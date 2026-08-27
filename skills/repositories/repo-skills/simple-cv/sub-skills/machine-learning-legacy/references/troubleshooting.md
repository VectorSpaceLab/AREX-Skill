# Legacy ML Troubleshooting

## Classifier warns that Orange is missing

**Symptoms**

- A classifier constructor logs that the required Orange machine-learning library is not installed.
- Training fails around `orange.Domain`, `orange.ExampleTable`, or learner objects.

**Cause**

SimpleCV's bundled KNN, NaiveBayes, Tree, and SVM wrappers are Orange-backed legacy classes.

**Recovery**

- If the user needs SimpleCV classifiers, install a Python-2-compatible Orange stack and verify `SimpleCV.base.ORANGE_ENABLED`.
- If Orange is unavailable, keep SimpleCV for image/feature extraction and use an external classifier outside SimpleCV.
- Do not claim `SVMClassifier` is runnable until Orange is verified.

## No features extracted

**Symptoms**

- Training returns `None` or logs that no features were extracted.
- Feature vectors have inconsistent lengths.

**Causes**

- `extract(img)` returned `None` for some images.
- `getFieldNames()` does not match the length of feature vectors.
- Images are empty or preprocessing differs between train and classify steps.

**Recovery**

Run a dry feature table first. Check every extractor on one image per class and assert the returned list length equals `getNumFields()`.

## Class names do not match data

**Symptoms**

- Predictions appear swapped or confusion matrix is nonsensical.

**Cause**

`images` and `classNames` are aligned by position.

**Recovery**

Print the directory/ImageSet and class name pair before training. Keep one image collection per class and a stable order.

## Original ML example wants network or display

**Symptoms**

- The nuts-vs-bolts example tries to download a zip file.
- A display window is required for prediction output.

**Recovery**

Ask for a local dataset or explicit download approval. Replace display writes with file output or printed metrics. Use the bundled `ml_recipe.py` to validate feature extraction without network access.

## Saved classifier fails to load

**Causes**

- Orange or feature extractor classes are missing.
- Pickled feature extractors are incompatible with the runtime.
- Field order changed after training.

**Recovery**

Load in the same compatible Python 2/Orange runtime. Recreate the exact feature extractors and field order before classifying. If state cannot be trusted, retrain from the original local dataset.
