# API Reference: geemap ML and Optional AI

## `geemap.ml` classifier conversion APIs

Import pattern:

```python
import geemap.ml as ml
```

### `tree_to_string(estimator, feature_names, labels=None, output_mode="INFER") -> str`

Converts one fitted scikit-learn decision-tree estimator into the string format accepted by Earth Engine decision tree ensembles.

Inputs:

- `estimator`: fitted decision tree object with a `tree_` attribute, such as `DecisionTreeClassifier` or `DecisionTreeRegressor`.
- `feature_names`: ordered list of band/property names used during training.
- `labels`: optional numeric label mapping for classification leaves.
- `output_mode`: `"INFER"`, `"CLASSIFICATION"`, `"REGRESSION"`, or `"PROBABILITY"`.

Behavior and edge cases:

- `"INFER"` infers classification from two-dimensional tree values and regression from one-dimensional tree values.
- `"PROBABILITY"` is binary-classification only.
- `"MULTIPROBABILITY"` is not implemented.
- Unknown output modes raise a runtime error.
- The returned string begins with an Earth Engine-style root line such as `1) root ...`.

### `rf_to_strings(estimator, feature_names, processes=2, output_mode="INFER") -> list[str]`

Converts a fitted scikit-learn forest/ensemble into a list of Earth Engine tree strings.

Inputs:

- `estimator`: fitted ensemble with `estimators_`. The tested path covers `RandomForestClassifier`, `RandomForestRegressor`, and similar tree ensembles.
- `feature_names`: ordered list of input band/property names.
- `processes`: number of worker processes used for conversion. Use `1` for small deterministic workflows.
- `output_mode`: same modes as `tree_to_string`, except invalid modes raise `ValueError` before per-tree conversion.

Behavior and edge cases:

- `output_mode` is uppercased and validated against `INFER`, `CLASSIFICATION`, `REGRESSION`, `PROBABILITY`.
- In `INFER`, classifier criteria such as `gini` or `entropy` use `estimator.classes_`; regressor criteria such as `mse` or `mae` are treated as regression. Newer scikit-learn names may require explicit `output_mode` if inference fails.
- For large forests, conversion cost scales with the number and depth of trees.
- The converted tree strings are local Python strings; no Earth Engine network call is needed until a classifier is used remotely.

### `strings_to_classifier(trees: list[str]) -> ee.Classifier`

Builds an Earth Engine classifier from in-memory tree strings.

```python
classifier = ml.strings_to_classifier(trees)
```

The function wraps each tree string as an `ee.String` and passes the list to `ee.Classifier.decisionTreeEnsemble`. Constructing the object is local client setup; using it with images, requesting results, or exporting outputs requires Earth Engine initialization and network access.

### `trees_to_csv(trees: list[str], out_csv: str) -> None`

Writes one converted tree per line to a local CSV-like text file.

- Newline characters inside each tree string are encoded as `#`.
- The parent directory must exist and be writable.
- This is the simplest persistence path when the user does not need an Earth Engine asset.

### `csv_to_classifier(in_csv: str) -> ee.Classifier | None`

Loads local tree strings and returns an Earth Engine classifier.

- If the file is missing, the function prints a clear `could not be found` message and returns `None` instead of raising.
- Callers should check for `None` and raise or recover explicitly.
- The function internally builds an Earth Engine FeatureCollection-like structure and delegates to `fc_to_classifier`.

### `export_trees_to_fc(trees, asset_id, description="geemap_rf_export") -> None`

Starts an Earth Engine table export task that writes tree strings to a FeatureCollection asset.

- Each feature stores a `tree` property, with newlines encoded as `#`.
- Requires Earth Engine authentication, initialization, a writable asset path, network access, and permission to start export tasks.
- The function starts the task but does not wait for completion.
- Use this only for classifier-tree persistence. Route generic export task design and monitoring to [../../conversion-and-io/SKILL.md](../../conversion-and-io/SKILL.md).

### `fc_to_classifier(fc) -> ee.Classifier`

Converts a FeatureCollection created by `export_trees_to_fc` back into a decision-tree ensemble classifier.

- The FeatureCollection must have a `tree` property on each feature.
- Encoded `#` characters are converted back to newline characters.
- If the asset export has not finished or the asset id is wrong, Earth Engine operations against the FeatureCollection will fail when evaluated.

## Earth Engine classifier/clusterer surfaces used with geemap

These are Earth Engine client APIs, not geemap-owned functions, but geemap workflows commonly combine them with maps and conversion helpers.

- `ee.Classifier.smileCart().train(training, label, bands)` for CART classification.
- `ee.Classifier.smileRandomForest(numberOfTrees).train(...)` for Earth Engine-hosted random forest training.
- `ee.Clusterer.wekaKMeans(n_clusters).train(training)` for unsupervised clustering.
- `image.select(bands).sampleRegions(collection=points, properties=[label], scale=...)` for supervised training samples.
- `image.sample(region=..., scale=..., numPixels=..., seed=..., geometries=True)` for unsupervised training samples.
- `image.select(feature_names).classify(classifier)` or `image.cluster(clusterer)` for applying the model.

Route result display to the interactive map sub-skill and accuracy visualization to the charts sub-skill.

## Optional `geemap.ai` surfaces

Import pattern:

```python
from geemap.ai import DatasetExplorer, Genie
```

Important: `geemap.ai` is optional. If imports print or raise messages asking for `pip install 'geemap[ai]'`, install the AI extra only when the user explicitly wants AI-assisted dataset discovery and can provide credentials.

### `Genie(project=None, google_api_key=None, gemini_model="gemini-1.5-flash", target_score=0.8, widget_height="600px", initialize_ee=True)`

Interactive Gemini-assisted map exploration widget.

- Looks up `EE_PROJECT_ID` or `GOOGLE_PROJECT_ID` if `project` is omitted.
- Looks up `GOOGLE_API_KEY` if `google_api_key` is omitted.
- Raises `ValueError` when required project or API key is missing.
- Initializes Earth Engine by default.
- Uses Google Generative AI, Google Cloud Storage, Earth Engine map display, and notebook widgets.

### `DatasetExplorer(project_id="GOOGLE_PROJECT_ID", google_api_key="GOOGLE_API_KEY", vertex_ai_zone="us-central1", model="gemini-3-pro-preview", embeddings_cloud_path="gs://earthengine-catalog/embeddings/catalog_embeddings.jsonl")`

Interactive Earth Engine dataset explorer.

- Reads the Google Cloud project name from an environment variable whose name is supplied by `project_id`, with fallback to `EE_PROJECT_ID`.
- Reads the API key from the environment variable named by `google_api_key`.
- Authenticates and initializes Earth Engine and Vertex AI.
- Downloads precomputed catalog embeddings from Google Cloud Storage.
- Use `DatasetExplorer().show(query)` to return the query widget.

### Lower-level AI/catalog helpers

- `Catalog(storage_client)`: loads Earth Engine STAC catalog metadata from Google Cloud Storage.
- `Collection` and `CollectionList`: wrappers around STAC metadata, including id, date interval, bounding box, resolution, code sample, and DataFrame conversion helpers.
- `EarthEngineDatasetIndex(data_catalog, index, llm)`: vector-search wrapper with `find_top_matches(...)` and `find_top_matches_with_score_df(...)`.
- `make_langchain_index(embeddings_df)`: builds a LangChain vector-store index from precomputed embeddings.
- `explain_relevance(query, dataset_id, catalog, model_name=..., stream=False)` and `explain_relevance_from_stac_json(...)`: use Gemini to explain dataset-query relevance.
- `is_valid_question(question, model_name=...)`: filters non-geospatial questions.
- `fix_ee_python_code(code, ee, geemap_instance, model_name=...)`: asks Gemini to repair Earth Engine Python snippets after execution errors.
- `DatasetSearchInterface(query, collections)`: widget table/code/map interface used by `DatasetExplorer`.

These helpers can be useful for custom dataset search tools, but they are credentialed, networked, and notebook-oriented. Keep fallback plans available when the AI stack is not installed or credentials are unavailable.
