# Core ChatBot Workflows

## Minimal in-memory bot

Use this for smoke tests and examples that should not create a file database:

```python
from chatterbot import ChatBot

bot = ChatBot("Smoke Bot", database_uri=None, read_only=True)
response = bot.get_response("Hello")
print(response.text, response.confidence)
```

`database_uri=None` makes `SQLStorageAdapter` use in-memory SQLite. `read_only=True` prevents `get_response` from saving the user input and generated response.

## Persistent SQLite bot

Use a SQLite file when responses should persist across processes:

```python
bot = ChatBot(
    "Persistent Bot",
    storage_adapter="chatterbot.storage.SQLStorageAdapter",
    database_uri="sqlite:///db.sqlite3",
)
```

If `database_uri` is omitted or false for SQL storage, ChatterBot defaults to `sqlite:///db.sqlite3`. Be explicit in examples so the database location is intentional.

## Conversation IDs

`ChatBot` creates a default conversation ID per instance. Pass `conversation=` when your application has sessions:

```python
session_id = "customer-support-1"
first = bot.get_response("Hi", conversation=session_id)
second = bot.get_response("Can you help me?", conversation=session_id)
```

If a statement has no `in_response_to`, `get_response` looks up the latest response in that conversation and records the new input as a response to it.

## Read-only inference after training

Train or seed storage first, then disable learning:

```python
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer

bot = ChatBot("Read Only Bot", database_uri=None)
ListTrainer(bot, show_training_progress=False).train(["Hello", "Hi there!"])
bot.read_only = True
print(bot.get_response("Hello"))
```

In `read_only=True`, `get_response` does not save new user input or generated responses.

## Preprocessors

Set preprocessors as import paths:

```python
bot = ChatBot(
    "Clean Bot",
    database_uri=None,
    preprocessors=[
        "chatterbot.preprocessors.clean_whitespace",
        "chatterbot.preprocessors.unescape_html",
    ],
)
```

Training also applies the bot's preprocessors, so data cleaning should be configured before calling trainer methods.

## Tagger choices

Default SQL/BestMatch behavior uses POS/lemma indexing:

```python
from chatterbot import languages
from chatterbot.tagging import PosLemmaTagger

bot = ChatBot("English Bot", tagger=PosLemmaTagger, tagger_language=languages.ENG)
```

Use `NoOpTagger` only when a storage adapter or custom workflow does not need indexed search fields:

```python
from chatterbot.tagging import NoOpTagger
bot = ChatBot("NoOp", tagger=NoOpTagger, database_uri=None)
```

Do not use `NoOpTagger` as proof that default SQL search quality has been verified.

## Search and response selection

Override search/comparison/selection through logic adapter kwargs:

```python
from chatterbot import comparisons, response_selection

bot = ChatBot(
    "Search Bot",
    logic_adapters=[
        {
            "import_path": "chatterbot.logic.BestMatch",
            "search_algorithm_name": "text_search",
            "statement_comparison_function": comparisons.LevenshteinDistance,
            "response_selection_method": response_selection.get_first_response,
        }
    ],
)
```

Use `additional_response_selection_parameters` to narrow response choices at call time:

```python
response = bot.get_response(
    "How are you?",
    additional_response_selection_parameters={"tags": ["support"]},
)
```

## CLI identity checks

The module CLI is intentionally small:

```bash
python -m chatterbot --version
python -m chatterbot --help
```

Do not look for training or server subcommands in this CLI; ChatterBot training and app integration happen through Python APIs.
