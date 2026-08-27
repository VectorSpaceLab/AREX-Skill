# Prompt Workflow Recipes

These recipes distill reusable ideas from Outlines examples into prompt-composition patterns that do not depend on the source checkout.

## 1) Structured event extraction

Use a template to present the message and context, then pair it with a schema-backed output type in the sibling structured-generation route.

```python
from datetime import datetime
from pydantic import BaseModel, Field
from outlines import Application, Template

class Event(BaseModel):
    title: str = Field(description="event title")
    location: str = Field(description="event location")
    start: str = Field(description="ISO timestamp if recoverable")

prompt = Template.from_string(
    """
    Current time: {{ now }}
    Message: {{ message }}
    Extract the event fields.
    """
)

app = Application(prompt, Event)
# event = app(model, {"now": now, "message": message}, max_new_tokens=128)
```

Workflow notes:

- Keep the template short and role-driven.
- Put schema details in the output type, not the prompt.
- If the event text is relative in time, add a bounded instruction to normalize against `now`.
- Validate the template independently before wiring the model.

## 2) Safe self-consistency

Self-consistency works best when the prompt asks for multiple independent attempts and a downstream reducer selects a majority or best-supported answer.

```python
from collections import Counter

prompt = Template.from_string(
    """
    Solve the problem carefully.
    Return only the final answer.

    Problem:
    {{ question }}
    """
)

# candidates = [generator(prompt(question=question)) for _ in range(k)]
# cleaned = [normalize(text) for text in candidates]
# answer = Counter(cleaned).most_common(1)[0][0]
```

Workflow notes:

- Use a fixed `k` and a deterministic reducer.
- Keep the reducer outside the model prompt.
- Do not ask the model to execute its own consensus algorithm.
- Avoid `eval`/`exec` on explanations or pseudo-code.
- If outputs are structured, parse them with a schema-aware validator before voting.

## 3) BabyAGI-style bounded task loops

Use templates for task execution, task creation, and task prioritization, but keep the loop bounded and the parsing strict.

```python
from collections import deque
from outlines import Template

perform = Template.from_string("Objective: {{ objective }}\nTask: {{ task }}\nReturn a concise result.")
create = Template.from_string(
    "Objective: {{ objective }}\nResult: {{ result }}\nCreate a short numbered list of new tasks."
)
prioritize = Template.from_string(
    "Objective: {{ objective }}\nTasks: {{ tasks }}\nReturn the reordered numbered list."
)

queue = deque([{"task_id": 1, "task_name": "Start"}])
max_cycles = 5
for _ in range(max_cycles):
    current = queue.popleft()
    # result = generator(perform(objective=objective, task=current["task_name"]))
    # new_tasks = parse_numbered_list(generator(create(...)))
    # queue.extend(new_tasks)
```

Workflow notes:

- Cap cycles, task count, and per-cycle token budget.
- Parse only the specific list format you asked for.
- Keep a human-readable audit trail of task IDs and sources.
- Do not let the loop mutate into an open-ended agent.
- Route model selection and provider capability to the sibling provider/local-model route.

## 4) Regex iteration for structured outputs

This pattern is useful when a natural-language prompt is not enough and the next step is to tighten a structure such as a phone number, code, date string, or identifier.

```python
import re
from outlines import Template
from outlines.types import Regex

phone_example = "(206) 386-4636"
pattern = Regex(r"\([0-9]{3}\) [0-9]{3}-[0-9]{4}")
assert re.fullmatch(pattern.pattern, phone_example)

prompt = Template.from_string(
    "Generate a Washington-style phone number that matches the required format."
)

# generator(model, pattern)(prompt())
```

Workflow notes:

- Validate the real example before generation.
- Tighten the regex only after checking it still matches the example set.
- When generation becomes repetitive, iterate on the structure instead of padding the prompt.
- If the task is truly structured, route to the sibling structured-generation skill.

## 5) Chat-first multimodal prompting

Use `Chat` when message history matters or when the model expects chat-shaped inputs.

```python
from outlines.inputs import Chat, Image

chat = Chat()
chat.add_system_message("You are concise and only answer with the requested fields.")
chat.add_user_message(["Describe this image in one sentence.", Image(pil_image)])
```

Workflow notes:

- Keep role ordering deliberate.
- Validate that each message content shape matches the chosen model's adapter.
- Use `Image` only with a real PIL image format; if needed, save and reload from a file or buffer to ensure `format` is set.
- Treat `Audio` and `Video` as capability-gated assets.

## 6) Prompt assembly + cache

Cache deterministic prompt assembly or parsing helpers, not random sampling.

```python
from outlines.caching import cache, cache_disabled

@cache(expire=600)
def format_examples(items):
    return "\n".join(f"- {item}" for item in items)

with cache_disabled():
    # useful for debugging stale prompt assembly or intentionally stochastic paths
    pass
```

Workflow notes:

- Use `OUTLINES_CACHE_DIR` for repeatable runs.
- Clear the cache when function signatures or output shapes change.
- Do not use the cache as a substitute for validation.

## 7) Composition checklist

Before a workflow is considered ready for a model run:

- Template renders with all variables supplied.
- Any includes or extends are inside the permitted template boundary.
- Chat messages have valid roles and content shapes.
- Image assets have a real PIL format.
- Output parsing is safe, bounded, and deterministic.
- No generated code will be executed directly.
