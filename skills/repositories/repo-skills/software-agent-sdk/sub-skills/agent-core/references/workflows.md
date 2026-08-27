# Agent Core Workflows

## Local agent with custom tools

1. Create `LLM` with a model and credential.
2. Create `Agent` with explicit `Tool(name=...)` entries.
3. Create `Conversation(agent=..., workspace=...)`.
4. Send the first prompt and run the conversation.
5. Inspect callbacks, tags, or persisted state if needed.

## Local conversation with custom callbacks

Use callbacks for event capture, metrics, or external logging.
Do not assume `Conversation.send_message()` runs the model immediately; collect state after `run()` completes.

## Remote conversation workflow

1. Create `Workspace(host=..., working_dir=...)` or a remote workspace object.
2. Build `Conversation(agent=..., workspace=workspace)`.
3. Use the remote server's HTTP/WebSocket APIs for remote state updates.
4. Generate titles or inspect status from the live conversation state.

## Persistence and resume

- Set `persistence_dir` for local runs that must be reopened later.
- Use `conversation.close()` when you want to release resources cleanly.
- Use `conversation.interrupt()` for cooperative cancellation rather than killing the Python process.

## What to read elsewhere

- For skill loading or prompt suffixes, use `../extensions/SKILL.md`.
- For tool choices, use `../built-in-tools/SKILL.md`.
- For remote transport, use `../remote-runtime/SKILL.md`.
