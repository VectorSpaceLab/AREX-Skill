---
name: core-chatbot
description: "Use ChatterBot core ChatBot, Statement, preprocessing, tagging,
  search, comparison, response selection, and CLI/version workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Core ChatBot

Use this sub-skill when a task asks how to instantiate a ChatterBot bot, call `get_response`, control conversation IDs, understand `Statement` fields, debug default response behavior, use preprocessors/taggers/search, or run the small `python -m chatterbot` CLI.

## Quick route

1. For installation or spaCy model errors, read the root [installation notes](../../references/installation-and-extras.md) and [cross-cutting troubleshooting](../../references/troubleshooting.md).
2. For constructor and method signatures, read [references/api-reference.md](references/api-reference.md).
3. For basic response lifecycle examples, conversation IDs, `read_only`, preprocessors, and taggers, read [references/workflows.md](references/workflows.md).
4. For missing input, missing language models, repeated responses, bad adapter configs, and confidence surprises, read [references/troubleshooting.md](references/troubleshooting.md).
5. Run or adapt [scripts/core_chat_smoke.py](scripts/core_chat_smoke.py) for a deterministic in-memory ChatBot smoke test.

## Core objects

The central object is:

```python
from chatterbot import ChatBot
bot = ChatBot("Example Bot", database_uri=None)
response = bot.get_response("Hello")
```

`get_response` accepts a string, a `Statement`, a dict containing `text`, or `text=` as a keyword. It returns a `Statement` with a `text` value and a `confidence` assigned by the selected logic adapter.

Use `database_uri=None` for in-memory SQL smoke tests and `read_only=True` when a bot should not learn from user input during inference.

## Important behavior

- A `ChatBot` has one storage adapter and a list of logic adapters.
- The default storage adapter is `chatterbot.storage.SQLStorageAdapter`.
- The default logic adapter list is `['chatterbot.logic.BestMatch']`.
- `ChatBot` creates a default conversation ID so repeated calls can track prior responses unless a caller passes `conversation=`.
- If `read_only` is false, `get_response` saves both the input statement and learned response relationship.
- `Statement` carries text, search fields, conversation label, persona, tags, `in_response_to`, timestamps, and confidence.
- Default SQL matching uses `PosLemmaTagger`, which normally needs a spaCy model such as `en_core_web_sm`.

## CLI

ChatterBot exposes only simple module CLI checks:

```bash
python -m chatterbot --version
python -m chatterbot --help
```

Use these for package identity, not for training or serving.

## Boundaries

- For trainers and data formats, route to [training](../training/SKILL.md).
- For built-in/custom logic adapter configuration, route to [logic-adapters](../logic-adapters/SKILL.md).
- For SQL/Mongo/Redis storage details, route to [storage-adapters](../storage-adapters/SKILL.md).
- For Django projects, route to [django-integration](../django-integration/SKILL.md).
