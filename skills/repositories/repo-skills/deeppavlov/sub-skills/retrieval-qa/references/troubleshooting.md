# Retrieval/QA troubleshooting

This file covers workflow-specific failures for `doc_retrieval`, `ranking`, `squad`, `odqa`, `kbqa`, and `faq`. For generic package import, CLI, cache root, backend, or installation issues, use [../../../references/troubleshooting.md](../../../references/troubleshooting.md).

## Quick triage

1. Identify the family in [model-catalog.md](model-catalog.md).
2. Inspect the selected config's `chainer.in`, `chainer.out`, nested `config_path`, `dataset_reader`, and `dataset_iterator` before changing code.
3. Check local data/index paths and `.done` markers with [data-and-indexing.md](data-and-indexing.md).
4. Run the bundled two-document template before attempting Wikipedia, ODQA, BERT, or KBQA assets.
5. Route service startup, REST payload, and socket framing problems to [../../serving/SKILL.md](../../serving/SKILL.md).

## Common symptoms

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Config name or alias is not found. | Alias mismatch or wrong family. | Normalize to canonical names in [model-catalog.md](model-catalog.md). Use full `category/config.json` names when in doubt. |
| `odqa_reader` raises a missing `save_path` or `dataset_format` error. | Required reader fields are absent in a custom doc-retrieval config. | Add `dataset_reader.save_path` and `dataset_reader.dataset_format` (`txt`, `json`, or `wiki`). |
| SQLite iterator cannot open DB or says the DB is empty/invalid. | `dataset_iterator.load_path` points to the wrong DB, the reader never ran, or the source format was wrong. | Align reader `save_path` and iterator `load_path`; verify local files match the declared `dataset_format`; rebuild the DB. |
| Local document changes are ignored. | Existing DB plus `.db.done` marker makes `odqa_reader` skip rebuild. | Delete both the DB and its `.done` marker, or write to a new `save_path`/`load_path`. |
| TF-IDF ranker returns unexpected IDs or no useful scores. | Vectorizer was fitted on different docs, `save_path`/`load_path` mismatch, or `top_n` hides expected documents. | Refit with matching `docs`, `doc_ids`, `doc_nums`; use the same `.npz` path for save/load; lower `top_n` only after confirming retrieval. |
| `stream_spacy_tokenizer` cannot load a model. | Missing or wrong spaCy model for the config language. | Install/use the matching small model (`en_core_web_sm` or `ru_core_news_sm`) in the prepared environment, or choose another verified tokenizer component and update the config consistently. |
| SQuAD call fails with arity or batch-length errors. | SQuAD expects paired `contexts` and `questions`. | Call `model(contexts, questions)` with equal-length lists, or send two fields through CLI/API according to `chainer.in`. |
| ODQA call fails after switching from SQuAD. | ODQA expects only questions; SQuAD expects contexts plus questions. | Check `chainer.in`: ODQA uses `question_raw`; SQuAD uses `context_raw` and `question_raw`. |
| English ODQA reports missing BPR/FAISS/Transformer components. | English ODQA includes dense retrieval in addition to TF-IDF. | Install/verify optional FAISS, PyTorch, Transformers, and model/index assets only if the user accepts heavy downloads. For local verification, start with TF-IDF doc retrieval. |
| Popularity ranker fails to load popularity JSON or logistic-regression model. | `pop_ranker` requires popularity data and a trained logistic-regression file in addition to TF-IDF index files. | Use `en_ranker_tfidf_wiki` or a local TF-IDF config unless the popularity assets are deliberately present. |
| KBQA loads text components but cannot answer or raises graph lookup errors. | Wikidata HDT, entity-linking DBs, templates, relation dictionaries, or query maps are missing. | Treat this as a data/index asset problem; verify KBQA assets for the selected language before debugging model outputs. |
| KBQA import errors mention `hdt`, `rapidfuzz`, `whapi`, spaCy, Slovnet, `razdel`, `udapi`, PyTorch, or Transformers. | Language-specific KBQA and relation-ranking optional dependencies are absent. | Install only the component requirement set needed by the selected config; avoid KBQA for tiny offline smokes. |
| FAQ custom CSV is read but no validation/test examples exist. | `faq_reader` populates `train` and leaves `valid`/`test` empty. | Use `basic_classification_reader` with explicit train/valid/test files, or add a split step in the custom config. |
| FAQ Russian adaptation tokenizes with English rules. | `LANGUAGE` changed without changing `SPACY_MODEL`, or vice versa. | Change both variables consistently (`ru` with `ru_core_news_sm`, `en` with `en_core_web_sm`). |
| `predict` is awkward for ranking candidates. | Some ranking configs expect nested candidate lists rather than single text lines. | Prefer Python API calls for response/relation ranking; use CLI `predict -f` only after confirming serialized input shape. |
| REST `/model` payload fails after local inference works. | Deployment payload keys or batch lengths do not match `chainer.in`. | Route to [../../serving/SKILL.md](../../serving/SKILL.md) and compare `/api` schema with config inputs. |

## Input shape checklist

- **Document retrieval**: one list of query strings; returns document IDs and scores if exposed by `chainer.out`.
- **SQuAD**: two same-length lists, contexts first and questions second; returns answer text, answer start, and score/logit.
- **ODQA**: one list of questions; English returns answer/score/place, while Russian exposes best answer by default.
- **KBQA**: one list of questions; returns answers, answer IDs, and generated queries.
- **Response ranking**: nested candidate lists or model-specific pair inputs; inspect `chainer.in` before choosing CLI vs Python.
- **FAQ**: one list of texts for inference; custom CSVs map question text to answer/category columns.

## Large-download and disk placement notes

- Wikipedia document-retrieval, ODQA, SQuAD-BERT, Transformer ranking, and KBQA configs are not safe smoke tests; they can require large model/index downloads.
- Put model/data roots on a disk with enough space before running `download=True`, CLI `-d`, or `python -m deeppavlov download <config>`.
- Use the root installation/troubleshooting reference for `DP_ROOT_PATH`, `DP_CONFIGS_PATH`, and related environment variable behavior.
- Do not start REST/socket serving until the selected config can run local inference with the intended input shape.

## Minimal local recovery path

When a retrieval task is failing and the user does not require pretrained Wikipedia assets:

1. Generate a tiny config with `scripts/tiny_retrieval_config.py`.
2. Train it locally with `download=False` and `install=False` after the package environment is ready.
3. Confirm the generated SQLite DB and `.npz` index exist.
4. Call the model from Python and verify the expected document filename appears in the returned IDs.
5. Only then port the same `data_path`, `save_path`, `load_path`, `fit_on`, `top_n`, and tokenizer choices into the user's larger config.
