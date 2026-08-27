# Libra API surface

## Primary object

`from libra import client` imports `libra.queries.client`. Instantiate it with a dataset path:

```python
from libra import client
c = client("data.csv")
```

Constructor behavior:

- Calls `required_installations()`, which tries to download NLTK `punkt`, `averaged_perceptron_tagger`, and `stopwords`.
- Stores the dataset path in `self.dataset`.
- Initializes `self.models = {}` and `self.latest_model = None`.

## Public `client` methods

| Method | Model key / output | Main use |
|---|---:|---|
| `neural_network_query(...)` | `regression_ANN` or `classification_ANN` | Auto-choose a feedforward ANN based on target cardinality. |
| `regression_query_ann(...)` | `regression_ANN` | Tabular regression with dynamic dense layers. |
| `classification_query_ann(...)` | `classification_ANN` | Tabular multi-class classification with one-hot targets. |
| `svm_query(...)` | `svm` | Support-vector classification. |
| `nearest_neighbor_query(...)` | `nearest_neighbor` | KNN classification over candidate neighbor counts. |
| `decision_tree_query(...)` | `decision_tree` | Decision-tree classification. |
| `kmeans_clustering_query(...)` | `k_means_clustering` | K-means clustering with optional cluster search. |
| `xgboost_query(...)` | `xgboost` | XGBoost classification. |
| `content_recommender_query(...)` | `content_recommender` | Content-based recommender over text-like feature columns. |
| `convolutional_query(...)` | `convolutional_NN` | CNN image classification from setwise/classwise/csvwise image data. |
| `gan_query(...)` | `DCGAN` | DCGAN training and generated images for a single image class folder. |
| `text_classification_query(...)` | `text_classification` | LSTM text classification. |
| `classify_text(text)` | prediction | Predicts after `text_classification_query`. |
| `summarization_query(...)` | `summarization` | Fine-tunes T5-small for summarization. |
| `get_summary(text, ...)` | summary list | Summarizes after `summarization_query`. |
| `image_caption_query(...)` | `image_caption` | InceptionV3 + encoder/decoder caption training. |
| `generate_caption(image)` | caption string | Captions after `image_caption_query`. |
| `generate_text(...)` | `text_generation` | GPT-2 generation from file contents or prefix. |
| `named_entity_query(instruction)` | `named_entity_recognition` | HuggingFace NER over a selected text column. |
| `tune(...)` | replaces selected model dict | Keras Tuner for ANN/CNN models already built in `models`. |
| `predict(data, model=None)` | predictions | Uses selected/latest model, optional preprocessor, then interpreter. |
| `recommend(search_term)` | recommendation output | Uses `content_recommender` when it is the latest model. |
| `analyze(model=None, save=True, save_model=False)` | updates model dict | Adds metrics/plots for supported models. |
| `plots(model=None, plot=None, save=False)` | plot objects | Displays/saves plots stored under a model dict. |
| `plot_names(model=None)` | printed keys | Prints available plot names. |
| `info(model=None)` | dict keys | Returns model dictionary keys. |
| `model(model=None)` | model dict | Returns the selected/latest model dictionary. |
| `operators(model=None)` | printed operator names | Prints available `plots`, `accuracy`, `losses` operators. |
| `accuracy(model=None)` | accuracy dict | Returns stored accuracy metrics. |
| `losses(model=None)` | losses dict | Returns stored loss histories. |
| `target(model=None)` | target column | Returns stored target column. |
| `vocab(model=None)` | vocabulary | Returns NLP vocabulary when available. |
| `get_models(model_requested)` | similar model key | Heuristic nearest model name; marked deprecated in source comments. |
| `dashboard()` | Streamlit process | Launches EDA dashboard via `streamlit run`. |

## Supporting modules worth knowing

- `libra.preprocessing.data_reader.DataReader`: reads `.csv`, `.xlsx`, `.json`; trims data when TensorFlow reports no GPU.
- `libra.preprocessing.data_preprocessor.initial_preprocessor`: target selection, train/test split, numeric/categorical/text preprocessing.
- `libra.data_generation.grammartree.get_value_instruction`: extracts target words from instructions with TextBlob.
- `libra.data_generation.dataset_labelmatcher.get_similar_column`: Levenshtein match from extracted target words to dataset columns.
- `libra.plotting.generate_plots.analyze`: branch-specific metric and plot generation.
- `libra.datasets.load`: downloads bundled remote datasets; requires network.

## Result dictionary conventions

Most model dictionaries include some of these keys: `id`, `model`, `target`, `num_classes`, `plots`, `preprocessor`, `interpreter`, `test_data`, `losses`, `accuracy`, `accuracy_score`, `data`, `shape`, `data_sizes`, `tokenizer`, `vocabulary`, `classes`, or generated output fields.

When writing robust downstream code, inspect `c.models[model_key].keys()` rather than assuming every query emits the same structure.
