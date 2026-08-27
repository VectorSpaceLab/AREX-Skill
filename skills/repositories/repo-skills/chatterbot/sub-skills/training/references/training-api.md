# Training API Reference

## When to read

Read this before choosing a trainer, constructing a field map, or deciding how training statements become searchable responses.

## Verified trainer signatures

Installed-package inspection for ChatterBot 1.2.14 confirmed:

```python
ListTrainer.train(self, conversation: list[str])
ChatterBotCorpusTrainer.train(self, *corpus_paths)
CsvFileTrainer.train(self, data_path: str, limit=None)
JsonFileTrainer.train(self, data_path: str, limit=None)
UbuntuCorpusTrainer.train(self, data_download_url: str, limit=None)
```

All trainers are initialized with a `ChatBot` instance:

```python
trainer = ListTrainer(chatbot, show_training_progress=False)
```

The base `Trainer` reads `CHATTERBOT_SHOW_TRAINING_PROGRESS` when `show_training_progress` is not passed. Pass `show_training_progress=False` in tests and automated scripts.

## `ListTrainer`

`ListTrainer.train(conversation)` accepts an ordered list of strings. Each item after the first is stored as a possible response to the previous item.

```python
trainer.train([
    "Hello",
    "Hi there!",
    "How are you?",
    "I'm doing well.",
])
```

Before storing statements, the trainer applies the chatbot's preprocessors and uses the chatbot's tagger to populate `search_text` and `search_in_response_to`.

## `ChatterBotCorpusTrainer`

`ChatterBotCorpusTrainer.train(*corpus_paths)` accepts one or more dotted corpus paths or filesystem paths. Common dotted paths include:

```python
trainer.train("chatterbot.corpus.english")
trainer.train("chatterbot.corpus.english.greetings")
trainer.train("chatterbot.corpus.english.conversations")
```

This requires `pyyaml`; the public corpus data normally comes from the separate `chatterbot-corpus` package. Categories in corpus files become statement tags.

## `CsvFileTrainer`

`CsvFileTrainer` reads CSV by default and TSV when initialized with `file_extension="tsv"`. It accepts a file or a directory and recursively consumes files with the configured extension.

The default generic field map uses column/header names:

```python
{
    "text": "text",
    "conversation": "conversation",
    "created_at": "created_at",
    "persona": "persona",
    "tags": "tags",
}
```

Field map values can be header names or integer column indexes:

```python
CsvFileTrainer(
    chatbot,
    show_training_progress=False,
    field_map={"created_at": 0, "persona": 1, "text": 2, "conversation": 3},
)
```

If no explicit `in_response_to` field is supplied, rows are treated as ordered conversation turns and each row responds to the previous row.

## `JsonFileTrainer`

`JsonFileTrainer` expects a root `conversation` array. Its default mapping is:

```python
{
    "text": "text",
    "conversation": "conversation",
    "created_at": "created_at",
    "in_response_to": "in_response_to",
    "persona": "persona",
    "tags": "tags",
}
```

Each item in `conversation` should contain the keys used by the field map.

## `UbuntuCorpusTrainer`

`UbuntuCorpusTrainer` is marked pending deprecation in favor of `CsvFileTrainer` for similar formats. It downloads a tar archive if absent, extracts it safely, and treats extracted TSV rows with this field map:

```python
{"text": 3, "created_at": 0, "persona": 1}
```

Use it only when the task specifically needs the Ubuntu dialog corpus. Use a small `limit` or tiny fixture for tests because full corpus training is large and slow.

## Exporting learned data

Every trainer inherits `export_for_training(file_path="./export.json")`. It writes JSON shaped like:

```json
{"conversations": [["previous text", "response text"]]}
```

Use this to move learned response pairs into another training corpus.
