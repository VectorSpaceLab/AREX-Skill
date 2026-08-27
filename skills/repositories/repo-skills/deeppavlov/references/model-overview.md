# Model overview

Use this page to decide which sub-skill owns a DeepPavlov task family before opening the deeper family reference.

## Route map

| Family / workflow | Owned by | Typical signals |
| --- | --- | --- |
| Config parsing, training, evaluation, nested configs, custom components, registries, and CLI orchestration | `sub-skills/pipelines/` | `build_model`, `train_model`, `evaluate_model`, `train_evaluate_model_from_config`, `parse_config`, `metadata.imports`, `metadata.variables`, `ref`, `config_path`, `crossval`, `paramsearch` |
| Text classification, NER, entity extraction, spelling correction, syntax/morphology, relation extraction, multitask, embeddings | `sub-skills/text-models/` | `classifiers/`, `ner/`, `entity_extraction/`, `spelling_correction/`, `sentence_segmentation/`, `morpho_syntax_parser/`, `relation_extraction/`, `russian_super_glue/`, `multitask/`, `embedder/` |
| Document retrieval, ranking, FAQ, SQuAD, ODQA, KBQA | `sub-skills/retrieval-qa/` | `doc_retrieval/`, `ranking/`, `faq/`, `squad/`, `odqa/`, `kbqa/` |
| REST and socket serving | `sub-skills/serving/` | `riseapi`, `risesocket`, `/probe`, `/api`, `/metrics`, `server_config.json`, `dialog_logger_config.json` |

## Installed config categories

The installed package exposes these top-level categories under `deeppavlov.configs`:

- `classifiers`
- `doc_retrieval`
- `embedder`
- `entity_extraction`
- `faq`
- `kbqa`
- `morpho_syntax_parser`
- `multitask`
- `ner`
- `odqa`
- `ranking`
- `regressors`
- `relation_extraction`
- `russian_super_glue`
- `sentence_segmentation`
- `spelling_correction`
- `squad`

## How to use the map

- If the user asks how to run, train, or inspect a config, start with `pipelines`.
- If the user asks which built-in model family to use for a text task, start with `text-models`.
- If the user wants retrieval, question answering, or KBQA, start with `retrieval-qa`.
- If the user wants to expose a selected config over HTTP or sockets, start with `serving`.

## Notes

The model-family sub-skills own the concrete input/output shapes and dependency reminders. This overview is only a routing aid.
