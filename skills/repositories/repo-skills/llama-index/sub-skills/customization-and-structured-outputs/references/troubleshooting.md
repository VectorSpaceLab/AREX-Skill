# Troubleshooting

## `ServiceContext` Is Missing or Deprecated

Symptoms:

- Old examples instantiate `ServiceContext` or pass `service_context=...`.
- New code ignores settings from an older context object.

Fix:

- Replace global service context setup with `Settings.llm`, `Settings.embed_model`, `Settings.node_parser`, `Settings.transformations`, and `Settings.callback_manager`.
- Prefer explicit constructor arguments for local overrides.
- If porting old snippets, map chunk settings to `SentenceSplitter` or `Settings.chunk_size` / `Settings.chunk_overlap` only when the active parser supports them.

## Global Settings Leak Across Tests

Symptoms:

- Tests pass alone but fail in a suite.
- A test unexpectedly uses another test's mock LLM, embedding dimension, callback handlers, parser, or chunk size.

Fix:

- Snapshot and restore hidden `Settings` fields around tests: `_llm`, `_embed_model`, `_callback_manager`, `_node_parser`, `_transformations`, `_prompt_helper`, and `_chat_prompt_helper`.
- Use `MockLLM` and `MockEmbedding` for no-provider tests.
- Avoid setting `Settings` at module import time in tests; set inside fixtures/context managers.
- Prefer local constructor overrides (`llm=...`, `embed_model=...`, `callback_manager=...`) when only one object needs customization.

## Missing API Keys or Provider Dependencies

Symptoms:

- Accessing `Settings.llm` or `Settings.embed_model` tries to resolve a default provider and fails.
- Structured-output or evaluator examples fail before parser logic runs.

Fix:

- For unit tests, set `Settings.llm = MockLLM(...)` and `Settings.embed_model = MockEmbedding(...)` before building components.
- For real providers, install the provider integration package and configure credentials through the integration workflow, not in this sub-skill's examples.
- If the failure appears while constructing an index, route index/provider setup to the indexing and integrations sub-skills.

## Structured Output Validation Errors

Symptoms:

- `PydanticOutputParser.parse(...)` raises JSON extraction or Pydantic validation errors.
- A structured LLM wrapper raises because the returned object is not the expected output class.
- `LLMTextCompletionProgram` raises `Output parser returned ... but expected ...`.

Fix:

1. Print `parser.get_format_string(escape_json=False)` and confirm the schema matches the desired output.
2. Make the prompt explicitly require JSON only, with no Markdown fences unless the parser can extract from them.
3. Start with a simple Pydantic model, then add field constraints after the model follows the schema.
4. Ensure `output_cls` and the parser's `output_cls` are the same model class.
5. If using a provider with weak schema following, retry with a stricter model, a provider-native structured-output integration, or a repair step that re-prompts on validation errors.
6. For tests, use a fake LLM that returns valid JSON for the exact schema rather than `MockLLM` if exact structured content matters.

## Parser and Model Mismatch

Symptoms:

- The prompt includes one schema but the program expects another output class.
- Field names in output differ from the Pydantic model.
- `excluded_schema_keys_from_format` hides schema information the LLM needed.

Fix:

- Create one `PydanticOutputParser(output_cls=YourModel)` and reuse it with the prompt/program.
- Avoid excluding schema keys until the basic structured flow works.
- Validate a hand-written JSON string with `parser.parse(...)` before adding the LLM call.
- Keep Pydantic aliases and field validators simple until the LLM reliably returns the base schema.

## Prompt Key Not Found

Symptoms:

- `update_prompts(...)` does nothing or raises for an unknown key.
- A custom prompt appears unused.

Fix:

- Call `component.get_prompts()` on the exact component instance after construction.
- Use one of the returned keys exactly, such as a nested key for the response synthesizer.
- Confirm the query path uses that component; router, agent, and workflow paths may call a different engine/tool.
- For one-off behavior, pass prompt templates directly during construction when supported.

## Callback Handler Not Firing

Symptoms:

- Token counts remain zero.
- Debug handler has no trace events.
- Custom handler methods are not called.

Fix:

- Set `Settings.callback_manager` before constructing the index/query engine/LLM/embed model, or pass `callback_manager=` directly.
- Verify the component actually emits the event type your handler listens for.
- Check the handler's ignore lists (`event_starts_to_ignore`, `event_ends_to_ignore`).
- For direct checks, wrap code in `with callback_manager.as_trace("name"):` or `with callback_manager.event(CBEventType.QUERY):`.
- Do not register two global handlers of the same type; the callback manager rejects duplicate global handler classes.

## Instrumentation Handler Not Observing Events

Symptoms:

- Callback handlers fire but instrumentation handlers do not.
- Observability integration receives no spans.

Fix:

- Confirm the integration uses the instrumentation dispatcher, not callback manager APIs.
- Register event/span handlers before executing the operation.
- Trigger a minimal query or LLM call known to emit the relevant event type.
- If only local debugging is needed, use `CallbackManager`, `TokenCountingHandler`, or `LlamaDebugHandler` first.

## Evaluation Data Shape Issues

Symptoms:

- Evaluator returns `invalid_result=True`.
- Scores or passing fields are `None` unexpectedly.
- `evaluate_response(...)` produces missing contexts.

Fix:

- Pass `query`, `response`, and `contexts` explicitly when testing evaluator logic.
- For `evaluate_response(...)`, ensure the `Response` has `source_nodes` with readable node content.
- Distinguish retrieval metrics, response evaluators, and pairwise evaluators; each expects different inputs.
- LLM-backed evaluators require a configured LLM and may return invalid results when the grading prompt response is unparsable.

## Structured Outputs in Agent Paths

Symptoms:

- An agent returns natural language when a downstream step expects a Pydantic model.
- Tool outputs validate but final agent response does not.

Fix:

- Route orchestration and agent-specific setup to the agents/workflows sub-skill.
- Define the Pydantic schema and parser/structured LLM contract here.
- Decide whether the structured contract applies to a tool result, an intermediate program, or the final agent response.
- Add validation and retry at the boundary where unstructured text enters the structured path.
