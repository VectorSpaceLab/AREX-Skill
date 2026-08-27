# Core ChatBot Troubleshooting

## `ChatBot("name")` fails with a spaCy model error

**Symptom:** initialization raises an error about a missing spaCy model such as `en_core_web_sm`.

**Cause:** the default `PosLemmaTagger` loads a model for the selected language.

**Fix:** install the model and rerun a small smoke check:

```bash
python -m spacy download en_core_web_sm
python sub-skills/core-chatbot/scripts/core_chat_smoke.py --check-model en_core_web_sm
```

If the task uses Redis vector storage, route to the storage sub-skill because Redis prefers `NoOpTagger` and semantic search.

## `get_response()` says text is required

Call one of the accepted forms:

```python
bot.get_response("Hello")
bot.get_response(text="Hello", conversation="session")
bot.get_response({"text": "Hello", "tags": ["tag"]})
bot.get_response(Statement(text="Hello"))
```

A bare `bot.get_response(conversation="session")` is invalid because no input text was supplied.

## The bot keeps learning unexpected statements

By default `read_only` is false, so `get_response` saves new input and response statements.

Use either:

```python
bot = ChatBot("Bot", read_only=True)
# or after training
bot.read_only = True
```

## Low-confidence or repeated responses

- `BestMatch` returns confidence `0` when it uses a default/random response.
- If no database statement exists, the input statement may be echoed.
- Repeated recent responses can be filtered by `filters.get_recent_repeated_responses` through BestMatch internals.
- Use tags or `additional_response_selection_parameters` to constrain response selection.

## Language lookup failures

`KeyError: A corresponding spacy model for "..." could not be found` means ChatterBot does not have a mapping for that language class. Choose a mapped `chatterbot.languages.*` class or provide a custom tagger that does not require the default mapping.

## Adapter class validation failures

If initialization says a class must be a subclass of `StorageAdapter` or `LogicAdapter`, check that each import path is in the correct slot and every dict has an `import_path` key.
