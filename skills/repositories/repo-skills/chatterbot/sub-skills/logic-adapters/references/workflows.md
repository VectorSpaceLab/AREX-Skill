# Logic Adapter Workflows

## BestMatch with a default response

Use `BestMatch` when the bot should answer from learned statement/response pairs.

```python
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer

bot = ChatBot(
    "Default Bot",
    database_uri=None,
    logic_adapters=[
        {
            "import_path": "chatterbot.logic.BestMatch",
            "default_response": "I am sorry, but I do not understand.",
            "maximum_similarity_threshold": 0.90,
        }
    ],
)
ListTrainer(bot, show_training_progress=False).train([
    "How can I help you?",
    "Read the documentation.",
])
print(bot.get_response("Unrelated question").text)
```

`maximum_similarity_threshold` is the score at which search stops because a close enough match was found. It is not a minimum confidence filter by itself; default behavior depends on whether a response list is found.

## Specific response adapter

Use `SpecificResponseAdapter` for deterministic canned responses:

```python
bot = ChatBot(
    "Exact Bot",
    logic_adapters=[
        {"import_path": "chatterbot.logic.BestMatch"},
        {
            "import_path": "chatterbot.logic.SpecificResponseAdapter",
            "input_text": "Help me!",
            "output_text": "Open the support guide.",
        },
    ],
)
```

The adapter requires both `input_text` and `output_text`. `output_text` may be a callable that returns a string.

## Math and time adapters

Use these when the bot should answer deterministic questions without relying on trained data:

```python
bot = ChatBot(
    "Math Time Bot",
    database_uri=None,
    logic_adapters=[
        "chatterbot.logic.MathematicalEvaluation",
        "chatterbot.logic.TimeLogicAdapter",
    ],
)
print(bot.get_response("What is 4 + 9?"))
print(bot.get_response("What time is it?"))
```

`TimeLogicAdapter` uses phrase matching over a configured list of positive time-question phrases. It can return a time string even with confidence `0`; the confidence tells ChatterBot whether the response should win.

## Unit conversion

Install `pint` before using `UnitConversion`:

```bash
python -m pip install pint
```

Then configure:

```python
bot = ChatBot(
    "Unit Bot",
    database_uri=None,
    logic_adapters=["chatterbot.logic.UnitConversion"],
)
print(bot.get_response("How many meters are in one kilometer?"))
```

Supported query patterns include:

- `How many meters are in one kilometer?`
- `0 Celsius to fahrenheit`
- `2 TB is how many GB?`

## Response selection customization

Use custom response selection or comparison methods through `BestMatch` kwargs:

```python
from chatterbot import comparisons, response_selection

bot = ChatBot(
    "Selection Bot",
    logic_adapters=[
        {
            "import_path": "chatterbot.logic.BestMatch",
            "statement_comparison_function": comparisons.LevenshteinDistance,
            "response_selection_method": response_selection.get_most_frequent_response,
        }
    ],
)
```

`response_selection_method` can also be a dotted import path string.

## Custom logic adapter

A custom adapter subclasses `LogicAdapter`, overrides `can_process` when needed, and returns a `Statement` from `process`:

```python
from chatterbot.logic import LogicAdapter
from chatterbot.conversation import Statement

class EchoQuestionAdapter(LogicAdapter):
    def can_process(self, statement):
        return statement.text.endswith("?")

    def process(self, input_statement, additional_response_selection_parameters=None):
        response = Statement(text=f"You asked: {input_statement.text}")
        response.confidence = 0.7
        return response
```

Use its import path in `logic_adapters` after placing it in an importable module.

## LLM adapter with deterministic tools

The LLM adapters are experimental. Use them only when a model service and credentials are available.

Ollama example:

```python
bot = ChatBot(
    "Ollama Tool Bot",
    logic_adapters=[
        {
            "import_path": "chatterbot.logic.OllamaLogicAdapter",
            "model": "llama3.1",
            "host": "http://localhost:11434",
            "logic_adapters_as_tools": [
                "chatterbot.logic.MathematicalEvaluation",
                "chatterbot.logic.TimeLogicAdapter",
                "chatterbot.logic.UnitConversion",
            ],
        }
    ],
)
```

OpenAI-compatible example:

```python
bot = ChatBot(
    "OpenAI Tool Bot",
    logic_adapters=[
        {
            "import_path": "chatterbot.logic.OpenAILogicAdapter",
            "model": "gpt-4o-mini",
            "logic_adapters_as_tools": ["chatterbot.logic.MathematicalEvaluation"],
        }
    ],
)
```

The deterministic adapters exposed as tools must have their own optional dependencies installed (`pint` for `UnitConversion`). Pass `conversation=` to `get_response` when LLM context should persist across turns.

## Run the bundled demo

```bash
python sub-skills/logic-adapters/scripts/logic_adapter_demo.py --mode all
```

This demo avoids provider calls and uses in-memory SQL storage.
