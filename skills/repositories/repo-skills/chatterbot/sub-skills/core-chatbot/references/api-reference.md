# Core API Reference

## When to read

Read this for verified ChatterBot core signatures and object relationships before writing code that instantiates a bot, passes statements, or changes search/tagger behavior.

## Verified signatures

Installed-package inspection confirmed these signatures for ChatterBot 1.2.14:

```python
ChatBot(name, stream=False, **kwargs)
ChatBot.get_response(self, statement=None, **kwargs) -> Statement
Statement(text: str, in_response_to=None, **kwargs)
```

Important supporting classes/functions:

```python
StorageAdapter.filter(self, **kwargs)
StorageAdapter.create(self, **kwargs)
list_corpus_files(dotted_path) -> list[str]
load_corpus(*data_file_paths)
```

## `ChatBot` constructor essentials

Common keyword arguments:

| Keyword | Meaning |
| --- | --- |
| `storage_adapter` | import path or config dict for the storage adapter. Defaults to `chatterbot.storage.SQLStorageAdapter`. |
| `logic_adapters` | list of import paths or dict configs. Defaults to `['chatterbot.logic.BestMatch']`. |
| `tagger` | tagger class or pre-instantiated tagger. Storage adapters can override the preferred tagger. |
| `tagger_language` | language class such as `chatterbot.languages.ENG`. |
| `preprocessors` | list of preprocessor import paths. Defaults to `clean_whitespace`. |
| `database_uri` | storage-specific URI. For SQL, `None` means in-memory SQLite and omitted/false creates `sqlite:///db.sqlite3`. |
| `read_only` | when true, `get_response` does not save new input/response statements. |
| `stream` | returns LLM streaming output when an LLM model is configured; experimental. |
| `model` | LLM model definition for experimental LLM adapter paths. |

Adapter configs can be strings or dictionaries:

```python
ChatBot(
    "Bot",
    storage_adapter={"import_path": "chatterbot.storage.SQLStorageAdapter", "database_uri": None},
    logic_adapters=[{"import_path": "chatterbot.logic.BestMatch"}],
)
```

## `get_response` input shapes

`get_response` accepts:

```python
bot.get_response("Hello")
bot.get_response(text="Hello", conversation="abc123")
bot.get_response({"text": "Hello", "tags": ["greeting"]})
bot.get_response(Statement(text="Hello", conversation="abc123"))
```

If no statement object, string, dict with `text`, or `text=` keyword is supplied, ChatterBot raises its `ChatBotException`.

The return value is a `Statement`. Use `str(response)` or `response.text` for the text and `response.confidence` for the adapter confidence.

## `Statement` fields

`Statement` stores:

- `text`
- `search_text`
- `conversation`
- `persona`
- `tags`
- `in_response_to`
- `search_in_response_to`
- `created_at`
- `confidence`

`Statement.add_tags(*tags)` appends tags, and `Statement.serialize()` returns a dict of statement fields. Storage adapters may map this object to SQLAlchemy, Django, MongoDB, or Redis records.

## Preprocessors

Built-ins:

- `chatterbot.preprocessors.clean_whitespace`: strips leading/trailing whitespace, removes line breaks/tabs, and compresses repeated spaces.
- `chatterbot.preprocessors.unescape_html`: converts escaped HTML such as `&lt;b&gt;`.
- `chatterbot.preprocessors.convert_to_ascii`: normalizes Unicode to ASCII equivalents when possible.

A custom preprocessor must accept and return a `Statement`.

## Taggers and languages

Built-ins:

- `PosLemmaTagger`: default for SQL-style indexed text search; loads a spaCy model and creates POS/lemma bigram strings.
- `LowercaseTagger`: lowercases text for a simpler search index.
- `NoOpTagger`: leaves text unchanged and is preferred by Redis vector storage.

`chatterbot.languages` contains many language classes, each with `ISO_639`, `ISO_639_1`, and `ENGLISH_NAME`. `get_model_for_language(language)` maps selected language classes to spaCy model package names.

## Search and response selection

Search classes:

- `IndexedTextSearch`: default. Uses `search_in_response_to_contains` and a comparison class to find close matches.
- `TextSearch`: compares raw text over broader storage filters.
- `SemanticVectorSearch`: used by Redis vector storage and expects confidence from vector similarity.

Comparison classes include `LevenshteinDistance`, `SpacySimilarity`, and `JaccardSimilarity`.

Response selection functions include:

- `get_first_response`
- `get_most_frequent_response`
- `get_random_response`

Use these through logic adapter kwargs such as `response_selection_method` rather than calling storage internals directly in normal chatbot code.
