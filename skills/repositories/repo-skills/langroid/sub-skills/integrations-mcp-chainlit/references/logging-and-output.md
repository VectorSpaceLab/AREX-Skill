# Logging and output controls

This reference covers Langroid integration behavior around HTML task logging, regular task logs, quiet mode, streaming output, and status spinners.

## Task logging files

Langroid task logging is controlled through `TaskConfig`:

```python
import langroid as lr

task = lr.Task(
    agent,
    config=lr.TaskConfig(
        enable_html_logging=True,
        logs_dir="logs",
    ),
)
```

By default, HTML logging is enabled. For each task name, Langroid may create:

- `<task-name>.html` for interactive collapsible viewing.
- `<task-name>.log` for text logs.
- `<task-name>.tsv` for tab-separated analysis.

The filename is derived from the task name, then the agent name, with a fallback root name. Set `logs_dir` to a writable relative path for the app or test run. Disable HTML output when it is not needed:

```python
task = lr.Task(agent, config=lr.TaskConfig(enable_html_logging=False))
```

If all task loggers should be disabled, use the task logger controls in `TaskConfig` rather than only disabling HTML.

## HTML log behavior

The HTML logger writes a self-contained dark-themed page with:

- Collapsible entries for user, LLM, agent, and system messages.
- Tool call visibility with parameters and results.
- Faded intermediate steps and full-opacity important responses.
- Expand/collapse controls.
- Auto-refresh while the task is running.
- Browser-local persistence for expanded/collapsed state and important-only filtering.

Avoid placing secrets or provider keys into prompts or tool outputs, because logs can preserve them.

## Quiet mode

Use `quiet_mode()` to suppress terminal LLM streaming and noisy output during workflows:

```python
from langroid.utils.configuration import quiet_mode, settings

with quiet_mode(True):
    result = task.run("Do the work")

settings.quiet = True  # global switch, use sparingly
```

Quiet mode is nested safely: an inner `quiet_mode(False)` does not override an outer quiet context. The previous quiet setting is restored even if an exception occurs.

## Async streaming output

LLM configs include `async_stream_quiet`:

```python
import langroid.language_models as lm

llm = lm.OpenAIGPTConfig(async_stream_quiet=True)
```

- Set `async_stream_quiet=True` to suppress async streaming in terminal workflows.
- Set it to `False` when you want streamed tokens visible, especially in Chainlit UI flows.
- `settings.quiet` also suppresses streaming output globally.
- Chainlit callback injection sets `agent.llm.config.async_stream_quiet = False` so the UI can receive streamed output.

## Status spinners

Langroid's status helper uses a Rich spinner when not already quiet and temporarily enters quiet mode while the spinner is active:

```python
from langroid.utils.output import status

with status("Indexing inputs"):
    do_work()
```

If quiet mode is already active, status messages are logged instead of shown as a spinner when logging is enabled. If Rich cannot create a live spinner because another live display is active, Langroid falls back to logging the message.

## Output design for integrations

- Use quiet mode for batch or scripted runs where only final results matter.
- Leave streaming visible for interactive terminal demos and Chainlit apps.
- Keep HTML logging enabled for debugging multi-turn tool behavior, then disable it for minimal smoke tests.
- Set `logs_dir` explicitly in apps that need predictable relative log placement.
- Do not parse HTML logs as a programmatic API; use task/agent return objects for assertions.

## Troubleshooting pointers

- If no HTML file appears, confirm `enable_html_logging=True`, loggers are enabled, and `logs_dir` is writable.
- If terminal output disappears, inspect `settings.quiet`, active `quiet_mode()` contexts, and `async_stream_quiet`.
- If Chainlit does not stream, ensure callbacks were injected and that the app is using async task/agent methods.
- If output becomes interleaved with spinners, wrap the long operation in `status()` or run in quiet mode.
