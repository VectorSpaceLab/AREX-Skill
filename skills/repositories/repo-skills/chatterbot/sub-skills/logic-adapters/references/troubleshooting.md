# Logic Adapter Troubleshooting

## Invalid adapter dictionaries

**Symptoms**

- `The dictionary ... must contain a value for "import_path"`.
- A storage adapter is accepted where a logic adapter was intended, or the reverse.

**Fix**

Use dictionaries with `import_path` and place them in the correct constructor field:

```python
ChatBot(
    "Bot",
    logic_adapters=[{"import_path": "chatterbot.logic.BestMatch"}],
)
```

## `SpecificResponseAdapter` missing arguments

**Symptoms**

- `The SpecificResponseAdapter requires an input_text parameter.`
- `The SpecificResponseAdapter requires an output_text parameter.`

**Fix**

Provide both:

```python
{
    "import_path": "chatterbot.logic.SpecificResponseAdapter",
    "input_text": "Help me!",
    "output_text": "Open the guide.",
}
```

## Unit conversion cannot import `pint`

**Symptom**

- `Unable to import "pint". Please install "pint" before using the UnitConversion logic adapter.`

**Fix**

```bash
python -m pip install pint
```

Then verify:

```bash
python sub-skills/logic-adapters/scripts/logic_adapter_demo.py --mode unit
```

## LLM adapter missing `model`

**Symptom**

- `ValueError: LLM logic adapters require a 'model' parameter`.

**Fix**

Set `model` in the adapter config. For Ollama, also set or accept `host`. For OpenAI-compatible use, ensure credentials and optional base URL are configured outside source code.

## Ollama adapter failures

**Symptoms**

- `Ollama library not installed`.
- Connection refused or model not found.
- Tool calling falls back to prompt-based mode.

**Fix**

1. Install the client package, often via `pip install chatterbot[dev]` or `pip install ollama`.
2. Start the Ollama service and pull the selected model.
3. Use `host` if the service is not at `http://localhost:11434`.
4. If native tool support is uncertain, let ChatterBot fall back automatically or set `force_native_tools` only after testing the model.

## OpenAI adapter failures

**Symptoms**

- OpenAI client import error.
- Authentication/base URL errors.
- Tool call JSON errors from a provider-compatible endpoint.

**Fix**

1. Install the client, often via `pip install chatterbot[dev] openai`.
2. Set `OPENAI_API_KEY` or use the provider's required credential setup.
3. For compatible endpoints, pass `host` as the base URL.
4. Start with one simple deterministic tool such as `MathematicalEvaluation` before combining several tools.

## Confidence surprises

- `TimeLogicAdapter` can create a time response even when confidence is `0`; confidence decides whether ChatterBot should choose it.
- `BestMatch` returns confidence `0` when it selects a random/default response.
- Semantic Redis search returns vector confidence differently from SQL indexed text search.
- Multiple adapters returning the same statement can cause ChatterBot to prefer that agreed response over a different single high-confidence result.

## `BestMatch` does not return the expected trained response

Check these in order:

1. Was the bot trained before `read_only=True` was set?
2. Do stored statements have `search_text` and `search_in_response_to` populated by the same tagger?
3. Are `additional_response_selection_parameters` filtering out the target response?
4. Did `excluded_words` remove the response?
5. Is the storage adapter using Redis semantic search instead of SQL indexed search?

Use the core and storage sub-skills for tagger/search/storage checks.
