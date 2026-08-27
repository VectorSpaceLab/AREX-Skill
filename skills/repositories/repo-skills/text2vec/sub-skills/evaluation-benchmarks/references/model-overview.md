# Model overview

This reference condenses the release tables and report findings into selection advice.

## What the source evidence says

- **CoSENT vs Sentence-BERT:** the repo report shows CoSENT is the stronger default when backbone and data are matched. It aligns training and inference through cosine ranking, while Sentence-BERT trains a classifier-style head and then switches to cosine at inference.
- **Pooling:** `MEAN` is the safest default. `FIRST_LAST_AVG` is very close. `CLS` and `POOLER` are slightly weaker in the report.
- **Temperature:** the report finds the useful range is roughly `0.01` to `0.05`. `0.05` is a practical default because it converges quickly and stays strong.
- **Batch size:** `64` is the best balance in the report; gains beyond that are small.
- **QPS:** throughput in the release tables is hardware-specific and only comparable under the same device / batch size / precision setup.

## Release-model snapshot: English STS-B / multilingual

| Family | Backbone | Release model | English STS-B |
|:--|:--|:--|:--:|
| GloVe | glove | Avg_word_embeddings_glove_6B_300d | 61.77 |
| BERT | bert-base-uncased | BERT-base-cls | 20.29 |
| BERT | bert-base-uncased | BERT-base-first_last_avg | 59.04 |
| BERT | sentence-transformers/bert-base-nli-mean-tokens | BERT-base-nli-first_last_avg-whiten | 63.65 |
| SBERT | sentence-transformers/bert-base-nli-mean-tokens | SBERT-base-nli-cls | 73.65 |
| SBERT | sentence-transformers/bert-base-nli-mean-tokens | SBERT-base-nli-first_last_avg | 77.96 |
| CoSENT | bert-base-uncased | CoSENT-base-first_last_avg | 69.93 |
| CoSENT | sentence-transformers/bert-base-nli-mean-tokens | CoSENT-base-nli-first_last_avg | 79.68 |
| CoSENT | sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 | `shibing624/text2vec-base-multilingual` | 80.12 |

Selection note: the multilingual CoSENT release is the cross-lingual choice when Chinese and English both matter. It is the safest recommendation when you need one model for mixed-language semantic matching.

## Release-model snapshot: Chinese matching

| Family | Backbone | Release model | ATEC | BQ | LCQMC | PAWSX | STS-B | SOHU-dd | SOHU-dc | Avg | QPS |
|:--|:--|:--|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Word2Vec | word2vec | `w2v-light-tencent-chinese` | 20.00 | 31.49 | 59.46 | 2.57 | 55.78 | 55.04 | 20.70 | 35.03 | 23769 |
| SBERT | xlm-roberta-base | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 18.42 | 38.52 | 63.96 | 10.14 | 78.90 | 63.01 | 52.28 | 46.46 | 3138 |
| Instructor | hfl/chinese-roberta-wwm-ext | `moka-ai/m3e-base` | 41.27 | 63.81 | 74.87 | 12.20 | 76.96 | 75.83 | 60.55 | 57.93 | 2980 |
| CoSENT | hfl/chinese-macbert-base | `shibing624/text2vec-base-chinese` | 31.93 | 42.67 | 70.16 | 17.21 | 79.30 | 70.27 | 50.42 | 51.61 | 3008 |
| CoSENT | hfl/chinese-lert-large | `GanymedeNil/text2vec-large-chinese` | 32.61 | 44.59 | 69.30 | 14.51 | 79.44 | 73.01 | 59.04 | 53.12 | 2092 |
| CoSENT | nghuyong/ernie-3.0-base-zh | `shibing624/text2vec-base-chinese-sentence` | 43.37 | 61.43 | 73.48 | 38.90 | 78.25 | 70.60 | 53.08 | 59.87 | 3089 |
| CoSENT | nghuyong/ernie-3.0-base-zh | `shibing624/text2vec-base-chinese-paraphrase` | 44.89 | 63.58 | 74.24 | 40.90 | 78.93 | 76.70 | 63.30 | 63.08 | 3066 |
| CoSENT | sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 | `shibing624/text2vec-base-multilingual` | 32.39 | 50.33 | 65.64 | 32.56 | 74.45 | 68.88 | 51.17 | 53.67 | 3138 |
| CoSENT | BAAI/bge-large-zh-noinstruct | `shibing624/text2vec-bge-large-chinese` | 38.41 | 61.34 | 71.72 | 35.15 | 76.44 | 71.81 | 63.15 | 59.72 | 844 |

## Selection guidance

### Chinese general semantic matching
Use `shibing624/text2vec-base-chinese` as the balanced default for query-question or general pair matching.

### Chinese sentence-to-sentence matching
Use `shibing624/text2vec-base-chinese-sentence` when the task is short, sentence-like, and closer to NLI or same-meaning matching.

### Chinese sentence-to-paraphrase / longer text
Use `shibing624/text2vec-base-chinese-paraphrase` when the pair often spans a sentence and a longer paraphrase, document snippet, or explanation.

### Multilingual matching
Use `shibing624/text2vec-base-multilingual` when the evaluation or application mixes Chinese and English, or you need one release model for both.

### Short-text discrimination with more compute
Use `shibing624/text2vec-bge-large-chinese` when you want stronger short-text discrimination and can afford lower throughput.

### Cold-start or lexical fallback
Use `w2v-light-tencent-chinese` when you need CPU-friendly lexical matching, a weak-data baseline, or a fallback when no stronger encoder is available.

## CoSENT vs Sentence-BERT in practice

- Choose **CoSENT** when you can select a text2vec release model or fine-tune a CoSENT-style checkpoint.
- Choose **Sentence-BERT** mainly for baseline comparison, SentenceTransformer compatibility, or when you must stay within that ecosystem.
- The report's main takeaway is that CoSENT usually gives better ranking correlation under the same backbone and settings.

## High-level tuning takeaways

| Knob | Source finding | Practical reading |
|:--|:--|:--|
| Pooling | `MEAN` ≈ `FIRST_LAST_AVG` > `CLS` / `POOLER` | Start with `MEAN`; do not overfit the pooling choice. |
| Temperature | Best zone around `0.01`–`0.05` | Start at `0.05` unless you have a reason to search lower. |
| Batch size | `64` is the best balance in the report | Increase only if memory allows and you need a small extra gain. |

## When to hand off to `similarities`

Use this sub-skill to choose and evaluate the model. For larger-scale retrieval/search, deduplication, or billion-scale matching, move the operational search layer to the separate `similarities` package after the model is chosen.
