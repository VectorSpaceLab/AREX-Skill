# Training Workflows

## List training

Use list training for short, ordered conversations embedded in Python code:

```python
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer

bot = ChatBot("List Bot", database_uri=None)
trainer = ListTrainer(bot, show_training_progress=False)
trainer.train(["Hello", "Hi there!", "How are you?", "I'm doing well."])
print(bot.get_response("Hello"))
```

Each list item after the first is stored as a response to the previous item. Repeated training calls can add multiple valid responses for the same input.

Run the bundled tiny demo:

```bash
python sub-skills/training/scripts/list_training_demo.py --prompt "Hello"
```

## Corpus training

Use `ChatterBotCorpusTrainer` for the separate `chatterbot-corpus` package:

```python
from chatterbot.trainers import ChatterBotCorpusTrainer

trainer = ChatterBotCorpusTrainer(bot, show_training_progress=False)
trainer.train("chatterbot.corpus.english.greetings")
```

Install prerequisites if needed:

```bash
python -m pip install pyyaml chatterbot-corpus
```

Dotted paths can target the whole language or a subset. Examples:

- `chatterbot.corpus.english`
- `chatterbot.corpus.english.greetings`
- `chatterbot.corpus.english.conversations`

## CSV and TSV training

Use `CsvFileTrainer` for row-based data. Field maps can reference header names or integer columns.

Header-based CSV:

```python
from chatterbot.trainers import CsvFileTrainer

trainer = CsvFileTrainer(
    bot,
    show_training_progress=False,
    field_map={"text": "text", "conversation": "conversation", "persona": "persona"},
)
trainer.train("./data")
```

Index-based CSV:

```python
trainer = CsvFileTrainer(
    bot,
    show_training_progress=False,
    field_map={"created_at": 0, "persona": 1, "text": 2, "conversation": 3},
)
```

TSV uses the same class:

```python
trainer = CsvFileTrainer(bot, file_extension="tsv", field_map={"text": 3, "created_at": 0, "persona": 1})
```

Run a bundled fixture demo:

```bash
python sub-skills/training/scripts/file_training_demo.py --format csv --prompt "Is anyone there?"
python sub-skills/training/scripts/file_training_demo.py --format json --prompt "Is anyone there?"
```

## JSON training

`JsonFileTrainer` expects JSON files with a root `conversation` array. A minimal file can look like:

```json
{
  "conversation": [
    {"text": "Is anyone there?", "conversation": "demo", "persona": "user"},
    {"text": "Yes", "conversation": "demo", "persona": "bot", "in_response_to": "Is anyone there?"}
  ]
}
```

Set `field_map` if your keys differ.

## Ubuntu corpus training

Use `UbuntuCorpusTrainer` only when the task explicitly needs the Ubuntu Dialog Corpus. It may download and extract a large archive. Always use a small `limit` for trials:

```python
from chatterbot.trainers import UbuntuCorpusTrainer
trainer = UbuntuCorpusTrainer(bot, show_training_progress=False)
trainer.train("https://example.invalid/ubuntu_dialogs.tgz", limit=50)
```

This trainer is pending deprecation in favor of `CsvFileTrainer` for similar TSV layouts.

## Export training data

Export learned response pairs after training:

```python
trainer.export_for_training("./export.json")
```

Run the bundled export helper:

```bash
python sub-skills/training/scripts/export_training_data.py --output ./export.json
```

The output is JSON with a `conversations` list of `[input, response]` pairs.

## Progress control

Use `show_training_progress=False` in scripts and tests. The base trainer also reads `CHATTERBOT_SHOW_TRAINING_PROGRESS`; set it to `0` to disable progress by default:

```bash
CHATTERBOT_SHOW_TRAINING_PROGRESS=0 python your_training_script.py
```
