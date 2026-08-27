# Structured-generation API reference

This reference summarizes the Outlines API surface used when a task is about the **shape** of model output. Model construction is covered by sibling local/provider skills.

## Imports

```python
import outlines
from outlines import Generator
from outlines.types import Regex, CFG, Choice, JsonSchema
from typing import Literal
from enum import Enum
from pydantic import BaseModel
```

`outlines.regex(...)`, `outlines.cfg(...)`, and `outlines.json_schema(...)` are top-level helper aliases for the structured output wrappers.

## Model call and generator contract

Verified signature:

```text
Generator(model, output_type=None, backend=None, *, processor=None)
```

Use either a direct model call:

```python
response = model("Classify: great product", Literal["positive", "negative"])
```

or a reusable generator:

```python
sentiment = Generator(model, Literal["positive", "negative"])
response = sentiment("Classify: great product")
```

Rules:

- `output_type` and `processor` are mutually exclusive.
- `processor` works only with steerable/local models; black-box/server providers reject it.
- `backend` is used only when a steerable model compiles an output type into a logits processor.
- Generator methods mirror model methods: `__call__(prompt, **inference_kwargs)`, `batch(prompts, **inference_kwargs)`, and `stream(prompt, **inference_kwargs)` when the wrapped model implements them.
- Generation returns raw text. Outlines does not automatically return a parsed Pydantic object in v1.

## Output type categories

### Basic Python and typing types

Use plain types and typing containers when the target language matches the type hint shape:

```python
model(prompt, int)
model(prompt, list[str])
model(prompt, dict[str, int | str])
```

For JSON-like nested objects, prefer Pydantic/dataclass/TypedDict schemas because they are easier to validate after generation.

### Finite choices

```python
from typing import Literal
from enum import Enum
from outlines.types import Choice

model(prompt, Literal["yes", "no"])
model(prompt, Choice(["low", "medium", "high"]))

class Priority(str, Enum):
    low = "low"
    high = "high"
model(prompt, Priority)
```

Use `Choice` when the list is computed at runtime. Use `Literal`/`Enum` when the choices are static and should be visible in the type.

### JSON schemas

`JsonSchema` accepts JSON-schema dictionaries/strings and common Python schema carriers:

```python
from pydantic import BaseModel

class Ticket(BaseModel):
    priority: Literal["low", "medium", "high"]
    summary: str

text = model(prompt, Ticket, max_new_tokens=200)
ticket = Ticket.model_validate_json(text)
```

Wrapper options:

```python
schema = JsonSchema(
    {"type": "object", "properties": {"answer": {"type": "integer"}}},
    whitespace_pattern=None,
    ensure_ascii=True,
)
```

`whitespace_pattern` is supported by the `outlines_core` backend. `llguidance` and `xgrammar` raise a backend error if it is set.

### Regex

```python
from outlines.types import Regex
phone = Regex(r"\([0-9]{3}\) [0-9]{3}-[0-9]{4}")
assert phone.matches("(206) 386-4636")
text = model(prompt, phone)
```

Outlines also exposes reusable regex terms such as `email`, `uuid4`, `date`, `time`, `semver`, `latitude`, and `longitude` from `outlines.types`.

### Regex DSL

The DSL combines terms with operators and helpers:

```python
from outlines.types import Regex, either, exactly, one_or_more

hex_digit = Regex(r"[0-9A-Fa-f]")
hex_byte = exactly(2, hex_digit)
choice = either("red", "green", "blue")
```

A `Term` can be combined with `+` for sequence, `|` for alternatives, `.optional()`, `.exactly(n)`, `.between(min, max)`, `.one_or_more()`, and `.zero_or_more()`.

### Context-free grammars

Use `CFG` for Lark-style grammar definitions:

```python
from outlines.types import CFG

grammar = CFG('''
?start: answer
answer: "yes" | "no"
''')
response = model(prompt, grammar, backend="llguidance")
```

`outlines_core` does not support CFG. Use `llguidance` or `xgrammar` with a compatible steerable model.

## Batch and stream

Use `batch` only when the model wrapper supports it:

```python
results = model.batch(["first", "second"], Ticket, max_new_tokens=200)
```

Multiple samples may return a list from a single prompt when the underlying model accepts parameters such as `num_return_sequences` or provider-specific `n`.

Streaming depends on the wrapper. Server providers often stream; Transformers currently raises `NotImplementedError` for streaming in this source revision. See sibling provider/local-model references before relying on a streaming path.

## Custom logits processors

For steerable/local models only:

```python
from outlines.processors.base_logits_processor import OutlinesLogitsProcessor
from outlines import Generator

class MyProcessor(OutlinesLogitsProcessor):
    def process_logits(self, input_ids, logits):
        # modify logits and return the same tensor-library type
        return logits

processor = MyProcessor(model.tensor_library_name)
generator = Generator(model, processor=processor)
```

Do not pass both `output_type` and `processor`:

```python
Generator(model, Ticket, processor=processor)  # ValueError
```

Processor details belong in [`backends.md`](backends.md) and local runtime prerequisites in `../../local-models/SKILL.md`.
