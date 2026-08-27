# Model Overview

This reference distills the Recommenders 1.2.1 model inventory into operating choices for future agents. It is intentionally self-contained; do not reopen the source checkout for routine model selection.

## Backend status legend

- **CPU verified**: verified in the base package inspection environment for this skill creation run.
- **CPU optional**: expected CPU path, but not a required verification gate in this run.
- **Spark optional/unverified**: needs the Spark extra plus Java/Spark/PySpark runtime; not proven here.
- **GPU/deep-learning optional/unverified**: needs TensorFlow and/or PyTorch extras and compatible accelerator/runtime; not proven here.
- **Experimental optional/unverified**: needs the experimental extra and sometimes native system dependencies; not proven here.

## Choose by data shape and backend

| User data/task | Recommended starting point | Why | Route away when |
|---|---|---|---|
| Pandas user-item interactions with ratings, counts, clicks, or implicit positives | SAR | CPU verified, quick baseline, no neural stack, supports `predict` and `recommend_k_items` | Dataset is Spark-scale, sequence-aware, or needs rich side features |
| Item descriptions, article text, metadata text, cold item-to-item similarity | TF-IDF | CPU verified utility for content-based item similarity | Need personalized ranking from user histories or neural news recommendation |
| Implicit collaborative ranking with Cornac installed | Cornac BPR/MF plus Recommenders helper functions | Base install includes Cornac; helpers convert model scores to Recommenders metric dataframes | Need pure package model with no external Cornac object, or long hyperparameter tuning |
| Click-through or ad-ranking with categorical and numeric features | LightGBM with `NumEncoder` | Base install includes LightGBM and category encoders; helper prepares dense arrays | Need collaborative top-k from user histories rather than supervised tabular labels |
| Large distributed explicit/implicit feedback | Spark ALS | Scales with PySpark ML | Spark extra/JDK/PySpark unavailable, or data fits pandas baseline |
| News recommendation with MIND-style files and titles/bodies/categories | NewsRec models such as NRMS, NAML, NPA, LSTUR | Dedicated neural news encoders and iterators | TensorFlow/data files unavailable; use TF-IDF as a lightweight text baseline |
| User-item implicit feedback where a neural model is requested | NCF, VAE, RBM, Wide&Deep, EmbeddingDotBias, LightGCN | Deep-learning model families are implemented or wrapped | PyTorch/TensorFlow not installed, no GPU/CPU budget for training, or user wants simple explainable baseline |
| Sequence/session recommendation | SASRec/SSEPT or DeepRec sequential models | Sequence-aware transformer/recurrent/convolutional families | Interactions are unordered, no sequence history, or deep-learning stack unavailable |
| Small explicit-rating matrix factorization with Surprise, LightFM, VW, xLearn, GeoIMC, RLRMC | Experimental model family | Useful when the user specifically requests the method and accepts dependency setup | Experimental extra/native dependencies not installed or task does not require that family |

## Algorithm family matrix

| Family | Package entry points and helpers | Data assumptions | Backend/dependencies | Status in this skill | Typical output |
|---|---|---|---|---|---|
| SAR | `recommenders.models.sar.SAR` | Interaction dataframe with user, item, numeric rating, optional timestamp; no duplicate user-item-rating rows for selected training columns | Base CPU packages | CPU verified | `predict(test)` returns pair scores; `recommend_k_items(test_users, top_k, remove_seen)` returns top-k rows |
| TF-IDF | `recommenders.models.tfidf.tfidf_utils.TfidfRecommender` | Item dataframe with an id column and one or more text columns | Base CPU packages; `bert`/`scibert` tokenizers require available tokenizer assets; `nltk` may require NLTK token data | CPU verified for deterministic local tokenization workflow | item-to-item recommendation rows with rank and similarity score |
| Cornac BPR/MF/BiVAE helpers | `recommenders.models.cornac.bpr.BPR`, `recommenders.models.cornac.cornac_utils.predict`, `predict_ranking` | Cornac `Dataset.from_uir` built from user-item-rating tuples | Base install includes Cornac; BiVAE may use GPU if configured | Helper imports verified; long training optional | Recommenders-style score/ranking dataframes |
| LightGBM | `recommenders.models.lightgbm.lightgbm_utils.NumEncoder`, LightGBM package APIs | Supervised tabular labels with categorical and numeric features, e.g. click-through prediction | Base CPU includes LightGBM; GPU/Spark variants need additional runtime | Helper import/signature verified | Dense feature arrays, LightGBM predictions |
| Spark ALS | PySpark ML `ALS` used with Recommenders Spark split/evaluation helpers | Spark DataFrame with integer user/item/rating columns | `[spark]`, Java/JDK, Spark/PySpark | Optional/unverified | Spark model, transformed predictions, top-k with Spark ranking helpers |
| SARplus | Incubating Spark SAR implementation | Distributed interaction data | Spark build/runtime | Optional/unverified | Spark top-k recommendations |
| NCF | `recommenders.models.ncf.dataset.Dataset`, `recommenders.models.ncf.ncf_singlenode.NCF` | Implicit user-item interactions converted to train/test files with contiguous ids | PyTorch optional stack; GPU optional but not required by API if CPU torch installed | Optional/unverified; torch missing in base check | Scores in `[0, 1]`, top-k built over user-item candidate pool |
| Embedding Dot Bias | `recommenders.models.embdotbias` dataset/model/trainer/utils | Explicit ratings with embedding ids/classes | PyTorch optional stack | Helper tests optional; model stack unverified here | Rating predictions/top-k via utility score helper |
| Wide&Deep | `recommenders.models.wide_deep.wide_deep_utils` plus model class in package examples | User/item ids and item/user side features for both memorization and generalization | PyTorch optional stack | Optional/unverified | Rating predictions and top-k recommendations |
| VAE | `recommenders.models.vae.standard_vae.StandardVAE`, `recommenders.models.vae.multinomial_vae.MultVAE` | User-item interaction matrix, often implicit feedback | PyTorch optional stack; GPU optional | Optional/unverified | Reconstructed user-item scores |
| RBM | `recommenders.models.rbm.rbm.RBM` | Rating matrix converted to RBM visible units and possible ratings | TensorFlow optional stack | Optional/unverified | Predicted ratings for unrated items |
| SASRec/SSEPT | `recommenders.models.sasrec` model, sampler, utilities | Per-user ordered item sequences and negative samples | PyTorch optional stack | Optional/unverified | Scores for next-item candidates |
| DeepRec DKN/xDeepFM/LightGCN/sequential | `recommenders.models.deeprec` models, iterators, YAML hparams | Model-specific files for news, click-through, graph, or sequence training | TensorFlow optional stack, sometimes GPU and downloaded resources | Optional/unverified | Model-specific predictions/files |
| NewsRec LSTUR/NAML/NPA/NRMS | `recommenders.models.newsrec` models, iterators, hparams utilities | MIND-style news and behavior files with word/user dictionaries and embeddings | TensorFlow optional stack; data download/cache required | Optional/unverified | Impression-level news scores/ranked prediction file |
| Surprise SVD | `recommenders.models.surprise.surprise_utils` | Small explicit rating datasets using Surprise trainsets | Experimental extra (`scikit-surprise`) | Optional/unverified | Recommenders-style prediction/ranking dataframes |
| LightFM | `recommenders.models.lightfm.lightfm_utils` | Sparse user-item interactions and optional user/item feature matrices | Experimental extra (`lightfm`) | Optional/unverified | Precision/recall traces, similar users/items, all-prediction dataframe |
| Vowpal Wabbit | `recommenders.models.vowpal_wabbit.vw.VW` | Online/contextual features in VW format or compatible dataframe conversions | Experimental extra and VW binary/package | Optional/unverified | Online/regression predictions |
| xLearn FM/FFM | Example-level use rather than stable core module | LibFFM-style fields/features | Experimental extra, native build tools such as CMake on some platforms | Optional/unverified | FM/FFM label predictions |
| GeoIMC/RLRMC | `recommenders.models.geoimc`, `recommenders.models.rlrmc` | Matrix completion with user/item features or low-rank matrix completion | Experimental/native dependencies including pymanopt-compatible stack | Optional/unverified | Completed rating/prediction matrix |

## Practical selection heuristics

1. **Start with the simplest data-compatible baseline.** SAR is the default for user-item interactions; TF-IDF is the default for item text similarity; LightGBM is the default for supervised click labels with tabular features.
2. **Use optional families only after checking imports.** For deep learning, check `import torch` or `import tensorflow` before importing model modules. For Spark, start a Spark session and verify Java/PySpark before using ALS or Spark metrics.
3. **Separate modeling from data preparation and evaluation.** This sub-skill assumes clean training/test inputs. If columns, split strategy, downloads, or negative sampling are unresolved, route to data preparation first. If metrics are requested, produce prediction/top-k dataframes and route to evaluation.
4. **Treat notebooks as workflow evidence, not runtime dependencies.** The bundled scripts in this sub-skill provide deterministic tiny checks without network, credentials, or long training.
5. **Be explicit about unverified optional claims.** Say "can be used when the required extra/backend is installed" rather than "is verified" unless a future verification run proves that backend.
