# Machine Learning and AI Workflows

These workflows are distilled for runtime use. They intentionally avoid any dependency on the source checkout and route non-ML responsibilities to sibling geemap sub-skills.

## Local scikit-learn forest to Earth Engine classifier

Use this when the user has local tabular training data and wants to apply a fitted scikit-learn tree ensemble in Earth Engine.

### Preconditions

- `scikit-learn`, `numpy`, and `pandas` are installed.
- The model is already fitted.
- The estimator exposes scikit-learn tree attributes used by geemap: a decision tree has `tree_`; an ensemble has `estimators_`, `classes_` for classifiers, and a recognizable `criterion` when `output_mode="INFER"` is used.
- `feature_names` exactly match the band/property order used to train the model and later passed to `image.select(feature_names)` or equivalent.

### Minimal conversion recipe

```python
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
import geemap.ml as ml

X = [[0.05, 0.10], [0.80, 0.70], [0.20, 0.85], [0.90, 0.20]]
y = [0, 1, 1, 0]
feature_names = ["red", "nir"]

rf = RandomForestClassifier(n_estimators=3, max_depth=2, random_state=42)
rf.fit(X, y)

trees = ml.rf_to_strings(
    rf,
    feature_names=feature_names,
    processes=1,
    output_mode="CLASSIFICATION",
)
assert trees and trees[0].startswith("1) root")

ml.trees_to_csv(trees, "rf_trees.csv")
classifier = ml.strings_to_classifier(trees)
# Later, with an initialized Earth Engine image:
# classified = image.select(feature_names).classify(classifier)
```

For a deterministic local smoke test, run:

```bash
python sub-skills/machine-learning-and-ai/scripts/rf_tree_smoke.py --output-csv rf_trees.csv
```

If scikit-learn is not installed, the script reports that the optional dependency is missing and skips the conversion without contacting Earth Engine.

## Single decision tree conversion

Use `tree_to_string` when the user has a fitted `DecisionTreeClassifier` or `DecisionTreeRegressor` instead of an ensemble.

```python
from sklearn.tree import DecisionTreeClassifier
import geemap.ml as ml

clf = DecisionTreeClassifier(max_depth=2, random_state=42).fit(X, y)
tree = ml.tree_to_string(
    clf,
    feature_names=["red", "nir"],
    output_mode="CLASSIFICATION",
)
classifier = ml.strings_to_classifier([tree])
```

Use `output_mode="REGRESSION"` for tree regressors. Use `output_mode="PROBABILITY"` only for binary classifiers; multiprobability is not implemented.

## Persist classifier trees locally as CSV

Use local CSV persistence when the user wants a portable tree-string file without starting an Earth Engine export task.

```python
import geemap.ml as ml

ml.trees_to_csv(trees, "rf_trees.csv")
classifier = ml.csv_to_classifier("rf_trees.csv")
if classifier is None:
    raise FileNotFoundError("rf_trees.csv was not found")
```

CSV rows contain one tree each. Newlines in tree strings are encoded as `#` on write; loading reconstructs a FeatureCollection-style classifier path internally.

## Persist classifier trees as an Earth Engine FeatureCollection asset

Use this only when the user explicitly needs an Earth Engine asset containing the converted trees. This starts a remote Earth Engine table export task.

```python
import ee
import geemap.ml as ml

ee.Initialize(project="your-ee-project")
asset_id = "users/your_name/rf_trees"

ml.export_trees_to_fc(trees, asset_id=asset_id, description="rf_tree_export")
# Wait for the Earth Engine export task to finish, then reload:
rf_fc = ee.FeatureCollection(asset_id)
classifier = ml.fc_to_classifier(rf_fc)
```

Route general export monitoring, Drive/Cloud Storage exports, or non-classifier table export design to [../../conversion-and-io/SKILL.md](../../conversion-and-io/SKILL.md).

## Earth Engine supervised classification pattern

Use this when the model is trained inside Earth Engine rather than in scikit-learn.

```python
import ee

ee.Initialize(project="your-ee-project")

bands = ["B1", "B2", "B3", "B4", "B5", "B6", "B7"]
label = "landcover"

# `image` is an ee.Image and `points` is an ee.FeatureCollection with labels.
training = image.select(bands).sampleRegions(
    collection=points,
    properties=[label],
    scale=30,
)
classifier = ee.Classifier.smileCart().train(training, label, bands)
classified = image.select(bands).classify(classifier)
```

Display `classified` with [../../interactive-earth-engine-maps/SKILL.md](../../interactive-earth-engine-maps/SKILL.md). Render palettes, legends, or accuracy charts with [../../visualization-and-charts/SKILL.md](../../visualization-and-charts/SKILL.md).

## Earth Engine unsupervised classification pattern

Use this for clustering an image with Earth Engine clusterers.

```python
training = image.sample(
    region=region,
    scale=30,
    numPixels=5000,
    seed=0,
    geometries=True,
)
clusterer = ee.Clusterer.wekaKMeans(5).train(training)
classified = image.cluster(clusterer)
```

This is Earth Engine ML rather than a `geemap.ml` conversion helper. It still belongs here because the task is classification; route display and export to sibling sub-skills.

## Training samples from drawn regions

If a workflow starts from user-drawn map regions, obtain or validate the drawn FeatureCollection with the map sub-skill, then continue here only after a valid label property and feature/band list are known.

```python
# From a geemap Map where the user drew training polygons:
training_samples = Map.user_rois
```

Route drawing controls and map widget behavior to [../../interactive-earth-engine-maps/SKILL.md](../../interactive-earth-engine-maps/SKILL.md).

## Optional AI dataset discovery

Use `geemap.ai` only when optional AI dependencies and credentials are present. Typical surfaces include:

- `DatasetExplorer(project_id="GOOGLE_PROJECT_ID", google_api_key="GOOGLE_API_KEY", ...)` for an interactive dataset-search widget.
- `DatasetExplorer().show("datasets for urban heat island analysis")` to create the widget query UI.
- `Genie(project=..., google_api_key=...)` for an LLM-assisted map/dataset exploration widget.
- `Catalog`, `CollectionList`, `EarthEngineDatasetIndex`, `make_langchain_index`, `explain_relevance`, and `fix_ee_python_code` for lower-level dataset search and code-repair components.

AI workflows require the `geemap[ai]` dependency set, Google API key, Google Cloud project, Earth Engine initialization, network access, Google Cloud Storage access to Earth Engine catalog assets, notebook/widget display, and compatible Gemini/Vertex/LangChain packages. If any of those are missing, do not treat the base ML conversion workflow as broken; route to [references/troubleshooting.md](troubleshooting.md#ai-extra-and-credential-failures).
