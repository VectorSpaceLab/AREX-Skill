# Modeling Troubleshooting

Use this reference for model-family selection, fit/predict/recommend mistakes, and optional backend failures. Route upstream dataframe cleaning/splitting problems to data-preparation, metric formula/column errors to evaluation, and installation/cloud/tuning projects to operations-and-tuning.

## Fast diagnosis checklist

1. Can `import recommenders` and the selected model module import?
2. Does the selected model match the data signal: interactions, text, tabular labels, sequence logs, news files, or Spark-scale data?
3. Are optional dependencies actually installed for Spark, TensorFlow/PyTorch, or experimental packages?
4. Do input dataframes contain the expected column names and numeric types?
5. Does the model output contain the expected scoring columns before evaluation?
6. For top-k workflows, were seen items removed intentionally or retained intentionally?

## Common symptoms and fixes

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: torch` or PyTorch model import fails | NCF, VAE, Wide&Deep, EmbeddingDotBias, or SASRec/SSEPT path selected without deep-learning dependencies | Do not claim the model is available. Either install/verify the optional GPU/deep-learning stack through operations-and-tuning or fall back to SAR/TF-IDF/LightGBM as appropriate. |
| `ModuleNotFoundError: tensorflow` or TensorFlow model import fails | RBM, DeepRec, or NewsRec path selected without TensorFlow | Check whether the user truly needs that family. If yes, prepare a TensorFlow-compatible environment; otherwise choose SAR/TF-IDF/LightGBM baseline. |
| GPU is visible but model still cannot import or train | Hardware exists but framework wheels, CUDA compatibility, or optional extras are missing | Treat GPU as unverified until `import torch`/`import tensorflow` and a tiny framework tensor operation pass. Route environment work to operations-and-tuning. |
| Spark ALS or Spark evaluation import/session fails | Spark extra, Java/JDK, PySpark, or Spark session missing/misconfigured | Keep Spark workflows optional/unverified. Use pandas/SAR if data fits memory, or prepare Spark backend explicitly. |
| `ModuleNotFoundError` for `surprise`, `lightfm`, `vowpalwabbit`, `xlearn`, or pymanopt-related packages | Experimental dependency not installed | Ask whether the user accepts experimental package setup. Some require native build tools; do not treat base install as sufficient. |
| SAR `ValueError: There should not be duplicates in the dataframe` | Duplicate interactions in selected fit columns | Aggregate or de-duplicate upstream. Common fixes: group by user/item and sum/count ratings for implicit feedback, or keep latest timestamp before `fit`. |
| SAR `TypeError: Rating column data type must be numeric` | Rating column contains strings/objects | Convert to numeric upstream and handle invalid values before fit. For implicit positives, set numeric `rating=1.0`. |
| SAR `Similarity type must be one of ...` | Misspelled or unsupported `similarity_type` | Use exactly one of `cooccurrence`, `cosine`, `inclusion index`, `jaccard`, `lexicographers mutual information`, `lift`, or `mutual information`. |
| SAR `Threshold cannot be < 1` | `threshold` set to 0 or negative | Set `threshold=1` for tiny data; raise it only when enough co-occurrences exist. |
| SAR scores are empty or all items vanish after `remove_seen=True` | User has interacted with every item in the training catalog, or catalog is too small for requested `top_k` | Reduce `top_k`, expand candidate item catalog, keep `remove_seen=False` only if repeated recommendations are intended, or use item/content model for cold items. |
| SAR cannot score a user | User in test data was unseen during training | SAR cannot personalize for unknown users through `score`/`recommend_k_items`. Use `get_item_based_topk` with seed items, popularity fallback, or retrain with the user. |
| SAR unseen item pair gets score 0 | `predict` received an item absent from training | This is expected for pairwise scoring. To recommend new/cold items, use content features such as TF-IDF or retrain after adding item interactions. |
| Time-decayed SAR gives unexpected scores | Timestamp scale or `time_now` inconsistent; half-life interpreted in days | Use numeric timestamps on one scale, set `time_now` deliberately for reproducibility, and remember `time_decay_coefficient` is converted from days to seconds internally. |
| TF-IDF tokenizer tries to download or stalls | Default `scibert` or `bert` tokenization needs HuggingFace tokenizer assets | For deterministic local runs use `tokenization_method="none"`. Use BERT/SciBERT only with an approved cache/network policy. |
| TF-IDF with `nltk` fails on token data | NLTK word tokenizer resource missing | Install/provide NLTK token data or use `tokenization_method="none"`. |
| TF-IDF `empty vocabulary` or poor recommendations | Text columns are empty, all stop words, or too aggressively filtered by `min_df` | Validate non-empty text, lower `min_df`, include more text columns, and inspect `get_tokens()` after fit. |
| TF-IDF `Cannot get more recommendations than there are items` | Requested `k > len(items) - 1` | Set `k <= number_of_items - 1`. |
| `get_top_k_recommendations` returns a styled object and downstream code expects a dataframe | URL formatting path returned a styler-like object | Access the underlying table through `.data` when present, or use `recommend_top_k_items` for plain tabular output. |
| Cornac `predict_ranking` output is huge | It scores every known user against every known item | Estimate `n_users * n_items` first, restrict the candidate catalog, or use top-k methods where available. |
| Cornac remove-seen output still surprises user | `remove_seen=True` removes pairs present in the dataframe passed to helper, not an arbitrary train/test state | Pass the correct training interaction dataframe as the `data` argument when removing seen items. |
| LightGBM `KeyError` in `NumEncoder` | `cate_cols`, `nume_cols`, or `label_col` do not match dataframe columns | Validate columns upstream; route schema fixes to data-preparation. |
| LightGBM validation/test encoding differs from train | Encoder was refit on validation/test or train category state was discarded | Fit `NumEncoder` once on training data, then call `transform` on validation/test. |
| Model output cannot be evaluated | Wrong prediction column names or missing true rating/relevance columns | Ensure model output has `prediction`; for ranking metrics provide user/item/prediction and true relevance data. Route metric details to evaluation. |
| Results are nondeterministic | Random seeds not set, multithreaded/GPU training, or stochastic negative sampling | Set model/package seeds where available, reduce epochs for smoke tests, and report stochasticity in evaluation notes. |

## `remove_seen` semantics

`remove_seen=True` is common for top-k recommendation because users should not be recommended items already present in training data.

- SAR: `recommend_k_items(..., remove_seen=True)` masks items found in the model's training affinity matrix for each user.
- Cornac helper: `predict_ranking(..., remove_seen=True)` removes pairs found in the dataframe passed to the helper.
- Surprise helper and several utility workflows use the same merge-with-seen-pairs pattern.

If a user wants to evaluate rating prediction for known pairs, use pairwise `predict` and keep seen rows. If a user wants novel recommendation, remove seen interactions and then evaluate ranking metrics.

## Data sparsity signals

Escalate to data-preparation when:

- Too few users/items remain after filtering.
- Many users have only one interaction and cannot support stratified splits or meaningful top-k recommendations.
- A user has consumed the entire tiny catalog, making `remove_seen=True` output empty.
- Interactions contain duplicate or conflicting labels that need aggregation.

Possible model-side fallback choices:

- Use SAR popularity fallback with `get_popularity_based_topk` for sparse users.
- Use SAR `get_item_based_topk` when user history is absent but seed items are known.
- Use TF-IDF when item text exists and interactions are too sparse.

## Optional backend guardrails

Before optional model work, require a positive import/backend check:

```python
# PyTorch-backed families
import torch
print(torch.__version__, torch.cuda.is_available())

# TensorFlow-backed families
import tensorflow as tf
print(tf.__version__)

# Spark-backed families
import pyspark
from pyspark.sql import SparkSession
spark = SparkSession.builder.master("local[*]").appName("recommenders-check").getOrCreate()
print(spark.version)
spark.stop()
```

These checks prove only local imports/session startup. They do not verify a full model notebook, dataset download, GPU memory compatibility, or cloud credentials.

## Safe bundled checks

Run these no-network smoke scripts when diagnosing a base CPU installation:

```bash
python sub-skills/modeling/scripts/sar_tiny_smoke.py --top-k 2
python sub-skills/modeling/scripts/tfidf_tiny_smoke.py --top-k 1
```

If these fail, the base install or its pandas/scikit-learn/scipy dependencies are not healthy enough for the verified CPU modeling paths.
