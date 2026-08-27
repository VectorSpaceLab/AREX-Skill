# Retrieval and QA model catalog

This catalog covers DeepPavlov workflows whose primary objects are questions, contexts, documents, indexes, candidate responses, or knowledge-base queries. For generic config mechanics, use [../../pipelines/SKILL.md](../../pipelines/SKILL.md).

## Config aliases to normalize

Prefer canonical config names in task notes. Common compatibility aliases include:

- `squad`, `squad_torch_bert`, `squad_bert_infer` -> `squad_bert`
- `squad_ru`, `squad_ru_rubert`, `squad_ru_bert_infer` -> `squad_ru_bert`
- `multi_squad_noans`, `multi_squad_retr_noans` -> `qa_squad2_bert`
- `kbqa_cq`, `kbqa_cq_online` -> `kbqa_cq_en`
- `kbqa_cq_rus` -> `kbqa_cq_ru`
- `ru_odqa_infer_wiki_rubert` -> `ru_odqa_infer_wiki`

## Family map

| Family | Use when | Canonical configs | Main input shape | Main output shape | Notes |
| --- | --- | --- | --- | --- | --- |
| `doc_retrieval` | Return document IDs/titles and ranking scores from a local or downloaded document collection. | `doc_retrieval/en_ranker_tfidf_wiki.json`, `doc_retrieval/en_ranker_pop_wiki.json`, `doc_retrieval/ru_ranker_tfidf_wiki.json` | Batch of question/query strings under `docs` in the chainer. Training also uses `docs`, `doc_ids`, `doc_nums`. | `tfidf_doc_ids` plus internal `tfidf_doc_scores`; popularity config exposes `pop_doc_ids` and `pop_doc_scores`. | Uses `odqa_reader`, `sqlite_iterator`, `hashing_tfidf_vectorizer`, `tfidf_ranker`, and optionally `pop_ranker`. |
| `ranking` | Rank candidate utterances, relations, or paths rather than extracting an answer span. | `ranking/ranking_ubuntu_v2_torch_bert_uncased.json`, `ranking/rel_ranking_roberta_en.json`, `ranking/rel_ranking_nll_bert_ru.json`, `ranking/path_ranking_nll_roberta_en.json` | Response ranking uses `x` as a list whose first item is the context/query and the rest are candidates. Relation/path ranking uses `question` plus `rel_list` or `rels`. | Response scores under `predictions`; relation labels/probabilities under `y_pred_labels`, `y_pred_probas`, or `model_output`. | Treat relation/path configs as KBQA components unless the user explicitly wants standalone relation ranking. |
| `squad` | Find an answer span in a provided context. | `squad/squad_bert.json`, `squad/qa_squad2_bert.json`, `squad/qa_nq_psgcls_bert.json`, `squad/qa_multisberquad_bert.json`, `squad/squad_ru_bert.json`, `squad/squad_ru_convers_distilrubert_2L.json`, `squad/squad_ru_convers_distilrubert_6L.json` | Two equally sized batches: `context_raw` and `question_raw`; Python examples call `model(contexts, questions)`. | `ans_predicted`, `ans_start_predicted`, and `scores`; Python examples unpack answer text, start character, and logit/score. | `qa_squad2_bert` supports no-answer examples and may return an empty answer. Most configs require PyTorch/Transformers assets. |
| `odqa` | Answer a question without an explicit context by retrieving documents first. | `odqa/en_odqa_infer_wiki.json`, `odqa/en_odqa_pop_infer_wiki.json`, `odqa/ru_odqa_infer_wiki.json` | Batch of question strings under `question_raw`; Python examples call `model(questions)`. | English configs return `answer`, `answer_score`, and `answer_place`; the Russian config exposes `best_answer` by default. | English ODQA chains TF-IDF retrieval, BPR retrieval, SQLite document lookup, and a reader; the popularity variant uses the popularity reranker. Russian ODQA uses TF-IDF retrieval plus a reader. |
| `kbqa` | Answer factoid or complex natural-language questions against Wikidata-style graph assets. | `kbqa/kbqa_cq_en.json`, `kbqa/kbqa_cq_ru.json`, `kbqa/wiki_parser.json` | Batch of questions under `x`; standalone wiki parser calls use parser-specific `parser_info` and `query` inputs. | `answers`, `answer_ids`, and generated `query`. | Pipelines combine question validation, entity detection/linking, answer-type extraction, relation/path ranking, template matching, wiki parsing, and query generation. |
| `faq` | Map user questions to FAQ categories/answers using the fastText/logistic-regression path or a simple CSV FAQ corpus. | `faq/fasttext_logreg.json`; custom configs may use `faq_reader`. | `text` batch for the shipped config; custom CSV FAQ reader defaults to columns `x` for question and `y` for answer/category. | `y_pred_category` for the shipped config; custom FAQ configs usually output labels/categories. | `fasttext_logreg` uses `stream_spacy_tokenizer`, `fasttext`, `simple_vocab`, `sklearn_component`, and `proba2labels`; `LANGUAGE` and `SPACY_MODEL` can be changed for Russian. |

## Family-specific reminders

### Document retrieval and ODQA

- `tfidf_ranker` returns both document IDs and document scores. If a top-level config only exposes IDs, inspect the ranker step before assuming scores are unavailable.
- `pop_ranker` is not a standalone retriever; it reranks IDs and scores produced by `tfidf_ranker` using page popularity features and a logistic-regression model.
- ODQA English configs include nested document-retrieval configs and a BPR component; BPR adds FAISS/PyTorch/Transformers requirements and large model/index downloads.
- ODQA Russian config exposes only `best_answer` at the top level; expose the internal score explicitly if the downstream task needs confidence.

### Ranking

- `ranking_ubuntu_v2_torch_bert_uncased.json` is a response-selection model: one query/context plus multiple candidate utterances yields candidate relevance scores.
- `rel_ranking_roberta_en.json`, `rel_ranking_nll_bert_ru.json`, and `path_ranking_nll_roberta_en.json` are mainly KBQA relation/path rankers. Their direct input arity differs from response ranking.
- If the user wants sentiment, topic, paraphrase labels, or generic classification not tied to retrieval/QA, route to [../../text-models/SKILL.md](../../text-models/SKILL.md).

### SQuAD

- SQuAD configs solve answer-span extraction from explicit contexts, not document retrieval. Use ODQA when no context is provided.
- Training/evaluation datasets must keep answer text and `answer_start` offsets consistent with the exact context string.
- No-answer behavior belongs to SQuAD v2-style configs; do not expect all SQuAD v1-style configs to return empty answers.

### KBQA

- English KBQA uses template classification, entity detection, entity linking, Wikidata parsing, relation ranking, query generation, and path ranking.
- Russian KBQA additionally uses chunking/entity-detection parsers, syntax parsing, adjective-to-noun normalization, and tree-to-SPARQL conversion.
- Treat KBQA as a graph-asset workflow. Missing HDT files, entity-linking databases, templates, or relation dictionaries are data/index problems, not ordinary text-model bugs.

### FAQ

- The shipped `fasttext_logreg` config uses `basic_classification_reader` over train/valid/test files and predicts `y_pred_category`.
- `faq_reader` is useful for a simple CSV with question column `x` and answer/category column `y`; it returns populated training data and empty validation/test splits unless the config adds another reader or split strategy.
- For few-shot FAQ experiments, inspect the `basic_classification_iterator` `shot` value before changing model hyperparameters.
