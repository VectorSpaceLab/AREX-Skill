# Structured Task Workflows

## Purpose

Read this when you want to build or debug Promptify tasks using the current public API instead of the archived notebook examples.

## 1. Build a domain-specific NER task

```python
from promptify import NER

ner = NER(
    model="gpt-4o-mini",
    domain="medical",
    labels=["CONDITION", "SYMPTOM", "AGE"],
)
result = ner("The patient has chronic hip pain and osteoporosis.")
```

Use `domain` for a domain-prefixed prompt, `labels` to constrain the entity set, and `examples` when the model needs a few-shot pattern.

## 2. Run a custom Pydantic schema task

```python
from pydantic import BaseModel
from promptify import Task

class MovieReview(BaseModel):
    sentiment: str
    rating: float
    key_themes: list[str]

review_task = Task(
    model="gpt-4o-mini",
    output_schema=MovieReview,
    instruction="Analyze this movie review.",
)
result = review_task("Nolan's best work, but the pacing drags.")
```

Use `Task` when none of the built-in task families fit the requested output shape.

## 3. Use async or batch execution

```python
result = await ner.acall("Patient has diabetes")
results = ner.batch(["text1", "text2", "text3"], max_concurrent=2)
```

Notes:
- `acall()` mirrors the sync call.
- `batch()` uses async concurrency under the hood.
- If you already have an event loop running, Promptify handles that by dispatching batch work through a short-lived thread.

## 4. Work offline with a mock engine

For documentation, tests, and local smoke checks, replace the engine with a mock that returns deterministic JSON.

```python
from promptify.engine.llm import LLMResponse

class MockEngine:
    def __init__(self, payload):
        self.payload = payload

    def complete(self, messages, output_schema=None, **kwargs):
        return LLMResponse(text=self.payload, parsed=None, usage={}, model="mock", cost=0.0)

    async def acomplete(self, messages, output_schema=None, **kwargs):
        return self.complete(messages, output_schema=output_schema, **kwargs)
```

This pattern is useful when you want to verify prompt construction and parsing without contacting a provider.

## 5. Use built-in templates deliberately

Built-in template names:

- ner
- classify_binary
- classify_multiclass
- classify_multilabel
- qa
- relation_extraction
- tabular_extraction
- question_generation
- sql_writer
- summarize
- text_normalization
- topic_modelling

Template selection happens inside the task constructor. You normally choose the task class, not the template name, unless you are building a custom PromptBuilder workflow.

## 6. Understand task kwargs

Promptify splits kwargs into two groups:

- Model kwargs: temperature, top_p, max_tokens, stop, presence_penalty, frequency_penalty, timeout, max_retries.
- Template kwargs: domain, labels, examples, question, schema, rules, num_questions, num_topics, max_length, key_points, description, and any task-specific extras.

This means the same call can tune the provider and the prompt separately.

## 7. Suggested smoke path

Run the bundled helper when you need a quick sanity check:

```bash
python scripts/check_promptify.py --mode tasks
```

That script uses mocked engines, so it never needs provider credentials.

## 8. Legacy example translation

If you encounter an old example that uses Prompter, OpenAI, or Pipeline, translate it into the current API instead of copying it verbatim.

- Old NER example -> NER(model=..., domain=..., labels=...)
- Old prompt builder example -> PromptBuilder(template=...)
- Old pipeline example -> task object plus an optional mock or live LLM engine

## 9. When to switch to evaluation

If the workflow changes from building a task to scoring the task outputs, switch to the evaluation sub-skill. The current route stops at task execution and prompt parsing.
