---
name: training
description: "Use ChatterBot trainers, corpus utilities, CSV/TSV/JSON field
  maps, Ubuntu corpus handling, progress controls, and training-data export
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# ChatterBot Training

Use this sub-skill when a task asks how to teach a ChatterBot bot responses, load `chatterbot-corpus`, train from list/CSV/TSV/JSON files, export learned conversations, control training progress, or debug trainer data-format errors.

## Quick route

1. Read [references/training-api.md](references/training-api.md) for trainer signatures, input shapes, and data formats.
2. Read [references/workflows.md](references/workflows.md) for minimal list, corpus, CSV/TSV, JSON, Ubuntu corpus, and export recipes.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for field-map, corpus, optional dependency, and large download failures.
4. Use [scripts/list_training_demo.py](scripts/list_training_demo.py) for a tiny list-training smoke test.
5. Use [scripts/file_training_demo.py](scripts/file_training_demo.py) to generate and train tiny CSV or JSON fixtures.
6. Use [scripts/export_training_data.py](scripts/export_training_data.py) to train a tiny bot and write export JSON.

## Trainer selection

| Task | Trainer |
| --- | --- |
| A single ordered conversation in Python | `ListTrainer` |
| Installed `chatterbot-corpus` data by dotted path | `ChatterBotCorpusTrainer` |
| CSV or TSV rows | `CsvFileTrainer` |
| JSON files with a root `conversation` array | `JsonFileTrainer` |
| Legacy Ubuntu dialog corpus tar/TSV layout | `UbuntuCorpusTrainer` |
| Custom source/format | subclass `Trainer` and implement `train()` |

## Required setup

Most trainer paths instantiate a normal `ChatBot`, so the default SQL + `PosLemmaTagger` path needs a spaCy model such as `en_core_web_sm`.

Corpus training needs `pyyaml` and usually the separate `chatterbot-corpus` package. Unit conversion is not a training feature; route that to [logic-adapters](../logic-adapters/SKILL.md).

## Data model

Training creates `Statement` rows. Each response statement normally stores:

- its own `text`;
- `in_response_to` pointing at the previous utterance or explicit response field;
- `search_text` and `search_in_response_to` computed by the bot's tagger;
- optional `conversation`, `persona`, `tags`, and `created_at` metadata.

Configure preprocessors and tagger before training because trainers apply the bot's preprocessors and tagger while building statements.

## Boundaries

- For core `ChatBot` lifecycle and read-only inference after training, use [core-chatbot](../core-chatbot/SKILL.md).
- For response selection after trained data exists, use [logic-adapters](../logic-adapters/SKILL.md).
- For storage backend persistence and query filters, use [storage-adapters](../storage-adapters/SKILL.md).
- For Django database migrations and web app training integration, use [django-integration](../django-integration/SKILL.md).
