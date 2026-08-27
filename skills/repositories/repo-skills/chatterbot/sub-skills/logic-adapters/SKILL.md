---
name: logic-adapters
description: "Configure ChatterBot logic adapters, response selection,
  comparison methods, custom adapters, MCP tool adapters, and experimental
  Ollama/OpenAI LLM adapters."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Logic Adapters

Use this sub-skill when a task asks how ChatterBot chooses a response, how to configure built-in logic adapters, how to add a custom adapter, why confidence values behave a certain way, or how experimental Ollama/OpenAI adapters expose deterministic adapters as tools.

## Quick route

1. Read [references/logic-api.md](references/logic-api.md) for verified adapter signatures, parameters, and response-selection surfaces.
2. Read [references/workflows.md](references/workflows.md) for concrete BestMatch, default response, math/time/unit conversion, specific response, custom adapter, and LLM-tool recipes.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for optional dependencies, missing `model`, provider/service failures, invalid adapter dicts, and confidence surprises.
4. Run [scripts/logic_adapter_demo.py](scripts/logic_adapter_demo.py) for deterministic math/time/specific/default/unit adapter smoke checks.

## Built-in adapters

| Adapter | Use for | Notes |
| --- | --- | --- |
| `BestMatch` | find learned responses from storage | default adapter; uses search + response selection |
| `SpecificResponseAdapter` | exact or matcher-triggered canned response | requires `input_text` and `output_text` |
| `MathematicalEvaluation` | natural-language or symbolic math | uses `mathparse`; also exposes `calculate` as a tool |
| `TimeLogicAdapter` | current time questions | uses spaCy phrase matching; also exposes current time as a tool |
| `UnitConversion` | natural-language unit conversion | requires `pint`; exposes `convert_units` as a tool |
| `OllamaLogicAdapter` | experimental local/remote Ollama responses | requires `model`, client package, and an Ollama service |
| `OpenAILogicAdapter` | experimental OpenAI-compatible responses | requires `model`, client package, and credentials/base URL |

## Adapter configuration pattern

Use import paths or config dictionaries:

```python
from chatterbot import ChatBot

bot = ChatBot(
    "Logic Bot",
    logic_adapters=[
        {
            "import_path": "chatterbot.logic.BestMatch",
            "default_response": "I am sorry, but I do not understand.",
            "maximum_similarity_threshold": 0.90,
        },
        {
            "import_path": "chatterbot.logic.SpecificResponseAdapter",
            "input_text": "Help me!",
            "output_text": "Read the support guide.",
        },
    ],
)
```

If multiple adapters can process a statement, ChatterBot returns the response with the highest confidence, with special handling when multiple adapters agree on the same statement.

## Boundaries

- For `ChatBot` lifecycle, `Statement`, taggers, and search classes, use [core-chatbot](../core-chatbot/SKILL.md).
- For training data that powers `BestMatch`, use [training](../training/SKILL.md).
- For SQL/Mongo/Redis storage behavior used by search, use [storage-adapters](../storage-adapters/SKILL.md).
- For Django-specific adapter usage, use [django-integration](../django-integration/SKILL.md).
