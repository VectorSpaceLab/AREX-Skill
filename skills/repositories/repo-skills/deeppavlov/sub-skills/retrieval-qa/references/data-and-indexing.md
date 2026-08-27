# Data and indexing workflows

Use this reference to prepare local data and indexes for DeepPavlov retrieval/QA configs without reopening the source checkout. For generic JSON config editing, nested configs, and `overwrite` syntax, use [../../pipelines/SKILL.md](../../pipelines/SKILL.md).

## Safe local document retrieval template

Generate a minimal two-document TF-IDF retrieval config with the bundled script, resolving the script path relative to this sub-skill directory if your current working directory is elsewhere:

```bash
python scripts/tiny_retrieval_config.py --output-dir ./tiny-retrieval-smoke
```

The script writes sample `.txt` documents, a sample query file, and a local JSON config that uses `odqa_reader`, `sqlite_iterator`, `hashing_tfidf_vectorizer`, and `tfidf_ranker`. It never downloads data or model weights. The generated config still expects an already installed spaCy model because DeepPavlov's TF-IDF vectorizer stores the tokenizer `ngram_range` from `stream_spacy_tokenizer`.

Typical follow-up commands after the user's environment is already prepared:

```bash
python -m deeppavlov train ./tiny-retrieval-smoke/tiny_retrieval_config.json
python -m deeppavlov predict ./tiny-retrieval-smoke/tiny_retrieval_config.json -f ./tiny-retrieval-smoke/sample_queries.txt
```

Use Python APIs instead when the task needs exact output objects:

```python
from deeppavlov import train_model, build_model

config_path = "./tiny-retrieval-smoke/tiny_retrieval_config.json"
train_model(config_path, download=False, install=False)
model = build_model(config_path, load_trained=True, download=False, install=False)
doc_ids, doc_scores = model(["What is DeepPavlov?"])
```

## Document retrieval index lifecycle

The `doc_retrieval` configs combine a reader, SQLite iterator, TF-IDF vectorizer, and ranker.

1. **Reader**: `odqa_reader` builds a SQLite database from local text/wiki/json files or, if a `db_url` is supplied, downloads an existing database. For offline local work, omit `db_url`.
2. **Database marker**: after successful local DB creation, DeepPavlov creates a marker beside the DB using the database suffix plus `.done`. If both the DB and marker exist, the reader skips rebuilds.
3. **Iterator**: `sqlite_iterator` opens the DB, reads document IDs, maps IDs to integer positions, and yields document texts plus `(doc_id, doc_num)` pairs for fitting.
4. **Vectorizer**: `hashing_tfidf_vectorizer` fits on `docs`, `doc_ids`, and `doc_nums`, then saves an `.npz` TF-IDF matrix. Keep `save_path` and `load_path` aligned for fit-then-infer cycles.
5. **Ranker**: `tfidf_ranker` accepts query strings and returns top document IDs and scores. `pop_ranker` reranks TF-IDF IDs/scores with popularity features and a logistic-regression classifier.

### `odqa_reader` input formats

| `dataset_format` | Expected local files | Document ID used by SQLite |
| --- | --- | --- |
| `txt` | A file or folder tree of `.txt` files. | Each file name. |
| `json` | JSON-lines style files where each line is a JSON list of dicts containing `title` and `text`. | Each dict's `title`. |
| `wiki` | WikiExtractor-style JSON-lines files where each line is a dict containing `title` and `text`. | Each dict's `title`. |

Use `txt` for the quickest local smoke and for small internal knowledge bases. Use `wiki` only after a wiki dump has already been extracted to JSON lines.

### Local TF-IDF config fields to inspect

- `dataset_reader.data_path`: folder or file used to build the DB.
- `dataset_reader.save_path`: DB file to create or reuse.
- `dataset_reader.dataset_format`: one of `txt`, `json`, or `wiki`.
- `dataset_iterator.load_path`: DB file consumed during fitting.
- `chainer.in`: usually `docs`, meaning the same model call accepts a list of query strings at inference time.
- `chainer.in_y`: must include `doc_ids` and `doc_nums` when fitting.
- Vectorizer `fit_on`: should match `docs`, `doc_ids`, and `doc_nums`.
- Vectorizer `save_path`/`load_path`: the `.npz` index path.
- Ranker `top_n` and `active`: `top_n` limits returned IDs when `active` is true; inactive rankers can return all IDs.

## SQuAD-style context QA

Use SQuAD configs when the caller supplies a context for every question.

- Inference call shape: `model(contexts, questions)` where both are same-length lists.
- Top-level config inputs: `context_raw` and `question_raw`.
- Top-level outputs: answer text, answer start character, and score/logit.
- Training/evaluation reader: `squad_dataset_reader`.
- Iterator: `squad_iterator`, which emits `((context, question), (answer_text, answer_start))` examples.

Supported reader dataset names include `SQuAD`, `SQuAD2.0`, `SberSQuAD`, and `MultiSQuAD`. SQuAD v2-style data may include unanswerable questions; these use empty answer text with `answer_start` set to `-1` in iterator output. Custom data must preserve exact `answer_start` offsets in the context string.

## ODQA data flow

Use ODQA configs when the caller supplies questions only and expects the pipeline to retrieve documents and extract answer spans.

- English `en_odqa_infer_wiki`: TF-IDF doc retrieval + BPR retrieval + ID concatenation + SQLite text lookup + question replication + reader/logit reranking.
- English `en_odqa_pop_infer_wiki`: same shape, but the nested document retriever uses popularity reranking before the reader.
- Russian `ru_odqa_infer_wiki`: TF-IDF retrieval + SQLite text lookup + question replication + a Russian/multilingual SQuAD reader. The top-level config exposes `best_answer` by default.

Important nested component parameters:

- `bpr.load_path`, `query_encoder_file`, `bpr_index`, `pretrained_model`, and `top_n` select the dense retrieval index and query encoder.
- `tfidf_ranker.top_n` controls how many document IDs feed downstream reader stages.
- `wiki_sqlite_vocab.load_path` must point to the same SQLite document database used by the retriever.
- `logit_ranker.batch_size`, `sort_noans`, `top_n`, and `return_answer_sentence` control answer-candidate batching and final answer selection.

For custom ODQA over local documents, first prove the TF-IDF retriever using the bundled tiny config or a `doc_retrieval`-style local config. Add reader and ODQA stages only after retrieval returns the intended document IDs.

## Ranking data shapes

- Response ranking (`ranking_ubuntu_v2_torch_bert_uncased.json`) expects each sample to contain a context/query followed by candidate utterances. It returns relevance scores for candidates.
- KBQA relation ranking (`rel_ranking_roberta_en.json`) expects a question and candidate relation list. Relation/path rankers are typically nested under KBQA rather than run as end-user models.
- Path-ranking NLL configs expect question plus path/relation candidates and return ranking logits/probabilities suitable for KBQA query generation.

Because these are Transformer-based workflows, separate them from the safe TF-IDF local smoke unless the user explicitly accepts model downloads and optional dependencies.

## FAQ data shapes

The shipped `faq/fasttext_logreg.json` path is a fastText vectorizer plus logistic-regression classifier.

- Default config variables include `LANGUAGE`, `SPACY_MODEL`, and a FAQ model path.
- The shipped reader is `basic_classification_reader`; it reads train/valid/test files in JSON or CSV form and maps an `x` field (default `text`) to a `y` field (default `labels`, overridden to `category` in the shipped config).
- The iterator supports few-shot sampling through `shot`; the shipped config samples a small number of examples per class for train data.
- To adapt English FAQ to Russian, change both `LANGUAGE` and `SPACY_MODEL` consistently.

For a simple FAQ CSV with question and answer/category columns, custom configs may use `faq_reader`:

- `data_path`: local CSV file path.
- `x_col_name`: question column, default `x`.
- `y_col_name`: answer/category column, default `y`.
- Output split: populated `train`, empty `valid`, empty `test` unless another split strategy is added.

## KBQA assets and indexes

KBQA configs are graph workflows, not plain text retrieval workflows.

| Component area | Typical assets/dependencies | Notes |
| --- | --- | --- |
| Entity detection/linking | Entity-linking databases, entity vocabularies, spaCy language models, `hdt`, `rapidfuzz`. | English and Russian pipelines use different entity-detection stacks and language resources. |
| Wikidata parsing | Wikidata HDT file, `wiki_parser`, relation/property dictionaries. | Missing HDT files cause graph lookup failures even if text models load. |
| Query generation | Template files, SPARQL/query maps, relation sets, `query_generator`, optional `whapi`. | Output includes the generated query alongside answer text/IDs. |
| Relation/path ranking | Transformer rankers, relation/path datasets, PyTorch/Transformers model weights. | Treat as optional heavy workflows unless required by the KBQA task. |
| Russian syntax helpers | Slovnet syntax parser, `razdel`, `udapi`, adjective-to-noun resources. | Russian KBQA has more language-specific preprocessing than English KBQA. |

Before debugging KBQA model quality, confirm that the graph files, entity-linking DBs, templates, and relation dictionaries expected by the selected language are present in the configured data root.
