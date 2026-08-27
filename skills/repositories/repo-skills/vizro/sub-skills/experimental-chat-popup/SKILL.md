---
name: experimental-chat-popup
description: "Use and maintain vizro-experimental chat model and floating popup,
  preserving optional LLM dependencies and security boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Experimental Chat Popup

Use this sub-skill when the task involves `vizro-experimental`, the `Chat` model, floating chat popup, dashboard-agent helper, chat security, or experimental chat examples/docs.

Route elsewhere when the task is mainly about:
- Stable Vizro core dashboard layout/components: `../core-dashboard-build/SKILL.md` and `../core-components-data-actions/SKILL.md`.
- Vizro-MCP agent workflows: `../mcp-agent-workflows/SKILL.md`.

## Experimental caveat

`vizro-experimental` is an incubation package. APIs may change, be removed, or graduate into `vizro-core`. Say this when giving user-facing guidance.

## Chat model

```python
from vizro_experimental.chat.models.chat import Chat

chat = Chat(
    id="assistant",
    placeholder="Ask a question about this dashboard",
    file_upload=False,
    example_questions=["What changed this month?"],
)
```

Live signature in the verified snapshot:

```text
Chat(*, id=<factory>, type='chat', actions=[], placeholder='How can I help you?', file_upload=False, example_questions=[])
```

## Floating popup

The popup package uses lazy exports:

```python
from vizro_experimental.chat.popup import add_chat_popup

add_chat_popup(
    generate_response=lambda messages, **kwargs: "Local deterministic response",
    title="Analytics Assistant",
    streaming=False,
)
```

Available lazy exports:

- `add_chat_popup`
- `create_dashboard_agent`
- `make_generate_response`

There is no `Popup` class exported from `vizro_experimental.chat.popup` in this snapshot.

## Optional dependency boundary

Preserve the BYO callback boundary:

- Users who pass `generate_response` should not need dashboard-agent provider dependencies.
- Do not promote dashboard-agent/pydantic-ai imports to module scope if that would break BYO mode.
- Only load `create_dashboard_agent`/`make_generate_response` when the user explicitly requests agent-backed behavior.

## Security defaults

- Treat chat input and uploaded file content as untrusted.
- Do not leak API keys or environment variables into chat responses or logs.
- Avoid executing user-provided code from chat messages.
- Prefer deterministic/mocked `generate_response` in tests.
- Require explicit provider credentials and network/cost authorization before live LLM calls.

## Repository tests

From `vizro-experimental/`:

```bash
hatch run test-unit tests/unit/test_component.py tests/unit/test_security.py tests/unit/popup/test_popup.py
```

Browser integration tests under `tests/integration/browser/` require a browser backend; do not make them required on a host without Chrome/Chromium.

## Debug checklist

- Is the task using stable core features or truly experimental chat APIs?
- Is the user using `Chat` as a model component or adding the floating popup to an already built Vizro app?
- Is `generate_response` provided? If yes, keep provider dependencies out of the path.
- If using dashboard-agent helpers, are credentials/model/provider settings available and authorized?
- Are tests using mocked local responses rather than live LLM calls?

## Evidence anchors

- `vizro-experimental/src/vizro_experimental/chat/models/chat.py`
- `vizro-experimental/src/vizro_experimental/chat/popup/__init__.py`
- `vizro-experimental/src/vizro_experimental/chat/popup/popup.py`
- `vizro-experimental/src/vizro_experimental/chat/popup/dashboard_agent.py`
- `vizro-experimental/docs/pages/chat/{chat-component,api-reference}.md`
- `vizro-experimental/examples/chat_component/app.py`
- `vizro-experimental/tests/unit/{test_component,test_security}.py`
- `vizro-experimental/tests/unit/popup/test_popup.py`
