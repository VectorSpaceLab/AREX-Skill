# Structured-generation workflows

## Schema-first JSON workflow

Use this for extraction, classification with rich fields, function-call-like arguments, and typed records.

1. Define a Pydantic model, dataclass, TypedDict, callable signature, GenSON schema, or JSON Schema.
2. Validate the schema independently when possible.
3. Generate with a compatible model and enough output tokens.
4. Parse the raw result explicitly.

```python
from typing import Literal
from pydantic import BaseModel

class Ticket(BaseModel):
    priority: Literal["low", "medium", "high"]
    summary: str
    needs_followup: bool

raw = model(
    "Summarize: customer cannot access paid account and needs help today.",
    Ticket,
    max_new_tokens=200,
)
ticket = Ticket.model_validate_json(raw)
```

If parsing fails, do not silently trust the string. Check token limits, required fields, overly narrow enums, unsupported provider schema keywords, and provider refusal/content-filter behavior.

## Finite-choice classification

For a finite set of labels:

```python
from typing import Literal
sentiment = model("This is excellent", Literal["positive", "neutral", "negative"])
```

Use an `Enum` when the labels are part of reusable application code. Use `Choice([...])` when the choices are computed at runtime.

## Regex iteration workflow

Use this when the structure is naturally a regular language, such as a code, ID, phone number, slug, or constrained text fragment.

1. Start with a real positive example and at least one negative edge case.
2. Write the simplest regex that should match the positive example.
3. Validate locally with `scripts/validate_structure.py regex` or Python `re.fullmatch`.
4. Generate through a compatible model.
5. Inspect repeated or low-quality outputs and refine the regex only after revalidating examples.

```bash
python scripts/validate_structure.py regex --pattern '\([0-9]{3}\) [0-9]{3}-[0-9]{4}' --text '(206) 386-4636'
```

```python
from outlines.types import Regex
phone = Regex(r"\([0-9]{3}\) [0-9]{3}-[0-9]{4}")
raw = model("Generate one Washington State phone number", phone)
```

## CFG workflow

Use CFGs when regex is not expressive enough: nested delimiters, recursive syntax, or a grammar with named nonterminals.

```python
from outlines.types import CFG

grammar = CFG('''
?start: answer
answer: "yes" | "no"
''')
raw = model("Answer yes or no", grammar, backend="llguidance")
```

Checks:

- Use `llguidance` or `xgrammar`, not `outlines_core`.
- Keep grammars small and test positive/negative strings independently before generation.
- For provider/server models, check whether the provider exposes CFG support; most do not.

## Reusable generator workflow

Use a generator when the same output type is reused many times:

```python
from outlines import Generator

generate_ticket = Generator(model, Ticket)
for prompt in prompts:
    raw = generate_ticket(prompt, max_new_tokens=200)
    yield Ticket.model_validate_json(raw)
```

The generator caches the compiled output constraint where the model backend supports that, reducing repeated setup work.

## Batch and multiple samples

Batch only when the selected model route implements `batch`:

```python
raw_items = model.batch(["Create Alice", "Create Bob"], Ticket, max_new_tokens=200)
items = [Ticket.model_validate_json(item) for item in raw_items]
```

If a model supports multiple return sequences for one prompt, expect a list and validate each item independently. Do not assume all wrappers support the same parameter names.

## Custom processor workflow

Use this for advanced local-model control when an output type is not enough:

1. Confirm the model is a steerable local model.
2. Subclass `OutlinesLogitsProcessor` and implement `process_logits(input_ids, logits)`.
3. Instantiate with `model.tensor_library_name`.
4. Use `Generator(model, processor=processor)`.

Never mix `output_type` and `processor`. Never use a custom processor with server/black-box provider wrappers.

## Integrated prompt + structure workflow

For prompt-heavy tasks, use `../../prompt-workflows/SKILL.md` first to render a template and produce a clean prompt, then return here for the output type:

```python
prompt = template(topic="release notes", fields=["title", "impact"])
raw = model(prompt, ReleaseNote, max_new_tokens=300)
note = ReleaseNote.model_validate_json(raw)
```

For provider execution, check `../../remote-providers/SKILL.md`; for local model execution, check `../../local-models/SKILL.md`.
