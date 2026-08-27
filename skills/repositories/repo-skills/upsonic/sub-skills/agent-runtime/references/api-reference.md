# Agent Runtime API Reference

## Verified signatures

| Surface | Verified shape | What to remember |
| --- | --- | --- |
| `Task` | `Task(description, attachments=None, tools=None, skills=None, response_format=str, context=None, ...)` | The task is where the user asks, input context, tool list, cache flags, response format, and policy-scoping flags live. |
| `Agent` | `Agent(model='openai/gpt-4o', *, name=None, memory=None, db=None, session_id=None, ..., tools=None, skills=None, ...)` | This is the full runtime: model selection, memory, tools, policies, profiles, reflection, context management, and output control. |
| `Agent.do` | `Agent.do(task, model=None, debug=False, retry=1, return_output=False, timeout=None, partial_on_timeout=False)` | Use for synchronous runs. Accepts a string, a `Task`, or a list of tasks. |
| `Agent.do_async` | `Agent.do_async(task, model=None, debug=False, retry=1, return_output=False, state=None, timeout=None, partial_on_timeout=False, graph_execution_id=None, ...)` | Use when the caller already manages an event loop or wants a resumable async run. |
| `Agent.print_do` | `Agent.print_do(task, model=None, debug=False, retry=1, return_output=False)` | Use when you want the rich/console presentation. |
| `Direct` | `Direct(model=None, *, settings=None, profile=None, provider=None, print=None)` | Use for the lightest direct model-call path. |
| `Direct.do` | `Direct.do(task, show_output=None)` | Takes a `Task` or a plain string and executes without the full agent stack. |
| `Chat` | `Chat(session_id, user_id, agent, *, storage=None, full_session_memory=True, summary_memory=False, user_analysis_memory=False, ...)` | Chat binds an Agent to Memory + Storage and keeps session state. |

## Runtime examples

```python
from upsonic import Agent, Task

agent = Agent(model="anthropic/claude-sonnet-4-6", name="Analyst")
result = agent.do(Task("Summarize the report in 3 bullets"))
```

```python
from upsonic import Direct, Task

response = Direct(model="openai/gpt-4o").do(Task("Write a concise answer"))
```

```python
from upsonic import Agent, Task

agent = Agent(model="openai/gpt-4o")
result = agent.do(Task("Return JSON", response_format=dict), return_output=True)
```

## Workflow notes

- Use `Agent` when the run needs tools, skills, memory, or policy layers.
- Use `Direct` when the user only wants a model call and does not need the rest of the stack.
- Prefer `Task` objects for anything with attachments, structured output, or cache controls.
- Use `partial_on_timeout=True` when a partial answer is better than a hard failure.
- Route provider selection and credentials questions to the models-and-providers sub-skill.
