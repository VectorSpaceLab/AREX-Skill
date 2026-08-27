# Agent Core API Reference

## Public constructors and signatures

```python
LLM(*, model='gpt-5.5', api_key=None, auth_type='api_key', base_url=None, ...)
Agent(*, llm, tools=[], mcp_config={}, filter_tools_regex=None, include_default_tools=[], agent_context=None, system_prompt=None, condenser=None, critic=None, tool_concurrency_limit=1)
Conversation(agent, *, workspace='workspace/project', plugins=None, persistence_dir=None, callbacks=None, token_callbacks=None, hook_config=None, max_iteration_per_run=500, stuck_detection=True, tags=None, client_tools=None, observability_metadata=None, observability_tags=None)
AgentContext(*, skills=[], system_message_suffix=None, user_message_suffix=None, load_user_skills=False, load_public_skills=False, marketplace_path='marketplaces/default.json', registered_marketplaces=[], load_project_skills=False, load_memory=False, memory_context=None, disabled_skills=[], secrets=None, current_datetime=None)
```

## Important behavior

- `Conversation(...)` returns a concrete local or remote implementation based on the `workspace` object.
- `AgentContext.skills` may contain explicit `Skill` objects; project, public, and user skills are loaded only when the corresponding flags are enabled.
- `Conversation.send_message()` queues work; `Conversation.run()` drives the agent until the current turn finishes or pauses.
- `Conversation.interrupt()` cancels the active run and pauses the conversation.
- `Conversation.generate_title()` uses the shared title helper path; it should not depend on a deprecated remote title endpoint.

## Lifecycle notes

- Local conversations persist events and state to the selected persistence directory when provided.
- `callbacks` receive emitted events, and `token_callbacks` receive model streaming chunks.
- `tags` and observability metadata are safe places to record task metadata and trace attributes.
- `stuck_detection` and `max_iteration_per_run` control how long a single run may continue.

## Model/provider guidance

- The SDK accepts the full model string at the boundary.
- Provider-specific behavior should be handled by the SDK's provider utilities and model-feature helpers rather than ad hoc string parsing.
- For Bedrock IAM/SigV4 auth, do not forward `LLM.api_key` as a bearer token.
