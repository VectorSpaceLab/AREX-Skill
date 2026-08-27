# Chat and Agent Troubleshooting

Use this guide to diagnose chat, agent, command, provider, and conversation problems without starting the server or depending on source-checkout docs at runtime.

## Schema or Option Uncertainty

Symptoms:

- Unsure which fields belong in `ChatRequestBody`, `ModifyAgentBody`, or `ModifyHiddenAgentBody`.
- Confusion between slash commands and agent `input_tools`.
- A payload uses `research` or `operator` as an agent tool and fails validation or behaves unexpectedly.

Safe response:

```bash
python skills/khoj/sub-skills/chat-agents/scripts/inspect_chat_schema.py
```

Check the printed Pydantic schemas, `ConversationCommand` values, agent input-tool choices, output-mode choices, and event names. The helper sets `DJANGO_SETTINGS_MODULE` and runs `django.setup()`, but it does not import `khoj.main`, start FastAPI, run migrations, or make network/model calls.

## Missing Chat Model or API Key

Symptoms:

- `POST /api/chat` returns or streams a 500-style message asking to add a chat model.
- Error detail says `Set your OpenAI API key or enable Local LLM via Khoj settings.`
- Agents list but chat cannot answer.

Likely causes:

- No default chat model exists.
- Default/user chat model has no usable provider/API configuration.
- OpenAI/Anthropic/Google model type is selected but the associated AI Model API key is missing.
- A local model path/proxy was configured during first run but the provider is no longer reachable.

Fix path:

1. Confirm server/admin chat model exists and is selected as default or user setting.
2. Confirm `ChatModel.model_type` matches the provider: OpenAI-compatible proxies still use model type `Openai`, Anthropic uses `Anthropic`, Gemini/Google uses `Google`.
3. Confirm the associated AI Model API has the API key and, if needed, base URL.
4. For the default agent, remember it dynamically uses the user's/default chat model; changing the default/user model can change default-agent behavior without editing the agent.
5. Route broad provider/admin setup and server settings to `deployment-api`.

## Local Provider Base URL or Model Mismatch

Symptoms:

- Ollama, LiteLLM, LM Studio, vLLM, Groq, Cerebras, or another OpenAI-compatible provider returns unknown model, connection refused, invalid JSON/structured output, or timeout errors.
- Docker Khoj cannot reach a provider that works from the host shell.
- Streaming works for one provider but fails for a local proxy.

Checks:

- The `Chat Model.name` must be the exact provider model id.
- OpenAI-compatible providers should use model type `Openai` and an AI Model API with the proxy base URL.
- Host-native Ollama commonly uses `http://localhost:11434/v1/`; Docker often needs `http://host.docker.internal:11434/v1/` or a compose service hostname.
- LiteLLM may need proxy flags that drop unsupported provider parameters.
- LM Studio is documented as unsupported because Khoj relies heavily on JSON/structured outputs and LM Studio's JSON mode support has been unreliable.
- Local APIs get a longer read timeout, but still must support the response format and tool/schema behavior Khoj asks for.

Fix path:

1. Verify the model id directly against the provider API.
2. Verify the base URL is reachable from the Khoj process, not just from your shell/browser.
3. Avoid setting tokenizers for OpenAI, Mistral, or Llama3-style OpenAI-compatible setups unless needed.
4. If structured-output/tool-calling behavior is the issue, prefer a provider/model known to support JSON mode or route through LiteLLM/OpenAI-compatible infrastructure that preserves it.

## Unsafe Agent Prompt Rejected

Symptoms:

- `POST /api/agents` or `PATCH /api/agents` returns 400 with a safety reason.
- Public agent creation fails but a private test prompt seems acceptable.

Root cause:

- Normal agent create/update runs a model-backed prompt safety check.
- Private agents use lax safety mode; public/protected-style agents use stricter safety mode.
- If only the persona changed during update, the new persona is checked before saving.

Fix path:

1. Remove instructions that ask the agent to bypass safety, exfiltrate secrets, impersonate users, perform harmful actions, or reveal private data.
2. For private personal agents, keep the prompt user-scoped and avoid public/administrative claims.
3. For public/protected agents, make the persona narrow, helpful, and non-deceptive.
4. Do not skip the safety check in route logic unless a maintainer explicitly asks for a policy change.

## Agent Cannot See Selected Files

Symptoms:

- Agent payload includes `files`, but search/chat returns no references.
- `GET /api/agents/{slug}` shows files, but answers do not use expected knowledge.
- Updating many files produces missing or partial knowledge.

Likely causes:

- The file was never indexed into the creator's base knowledge store.
- The filename/path in `files` does not exactly match existing `FileObject.file_name` and `Entry.file_path` values.
- The agent is private and the requester is not the creator.
- The chat query used `/general` or an agent without `notes` enabled.
- Ranking/filter behavior eliminated the expected entries.

Fix path:

1. Use `content-indexing` to verify upload/indexing first.
2. Confirm agent update copied both file objects and entries for the chosen files.
3. Confirm the chat path uses `/notes` or default inference can select `notes`.
4. Use `search-retrieval` for semantic ranking, filters, and score/distance issues.
5. Treat partial large/concurrent updates as bugs: agent file replacement is intended to be atomic.

## Command Not Triggering Expected Tool

Symptoms:

- `/operator ...` behaves like a normal/default query.
- `/help` does not route to a help endpoint.
- `/online /code ...` runs only online search.
- Default query chooses general knowledge instead of notes/online/code.

Root causes:

- The route parser only returns one leading recognized command.
- `/operator` is recognized only when the operator feature is enabled.
- `/help` is described in prompts/docs but has no dedicated command branch in the route parser.
- Agent `input_tools` restrict automatic/default source selection.
- Unavailable services are removed from automatic tool options.

Fix path:

1. Use a single explicit command when deterministic behavior is needed.
2. For multi-tool behavior, use a default query with clear wording and make sure services/agent tools allow the desired tools.
3. Do not store chat-only commands such as `research` or `operator` in `input_tools` unless the enum has changed.
4. If changing parser behavior, update `get_conversation_command`, `/api/chat/options`, references, and tests together.

## Online or Webpage Tool Unavailable

Symptoms:

- Default inference never selects online/webpage.
- `/online` or `/webpage` emits a status saying search/read failed and answers without online references.
- Online results are empty, stale, or provider-specific errors appear.

Checks:

- Web search option exposure requires at least one of `GOOGLE_SEARCH_API_KEY`, `SERPER_DEV_API_KEY`, `EXA_API_KEY`, `FIRECRAWL_API_KEY`, or `KHOJ_SEARXNG_URL`.
- Plain webpage reading can work with HTTP requests, but configured scrapers improve extraction and may need their own credentials.
- Provider quotas, blocked egress, DNS, country/location settings, and webpage bot protection can all affect output.

Fix path:

1. Confirm the desired provider environment variable or webscraper admin config is present to the running Khoj process.
2. For Docker, verify the search/scraper service is reachable by service name or configured URL from inside the container.
3. For Serper/Exa/Firecrawl/Google, verify API key validity and quota.
4. If only ranking/filtering of note references is wrong, route to `search-retrieval`; if only web extraction is wrong, inspect online-search processor behavior.

## Code Tool Unavailable or Failing

Symptoms:

- Default inference never selects `code`.
- `/code` answers without `codeContext`.
- Status says code failed, or logs show sandbox timeout/connection errors.

Checks:

- Code option exposure requires `KHOJ_TERRARIUM_URL` or `E2B_API_KEY`.
- Terrarium/Pyodide has no network access and limited packages.
- E2B has network access and more packages but requires a valid API key and optional template.
- Generated code must appear in Python code fences and must avoid unsafe behavior.

Fix path:

1. Confirm sandbox service/API key is configured in the Khoj runtime environment.
2. Test the sandbox service separately with a tiny arithmetic expression if operational validation is allowed.
3. Inspect generated code for missing fences, unavailable packages, file path assumptions, or unsafe instructions.
4. Keep chat-attached files distinct from indexed content; code receives selected context/input files, not arbitrary local source paths.

## Image or Diagram Output Failing

Symptoms:

- `/image` returns setup or policy-failure text.
- No `images` appear in non-streaming response.
- `/diagram` emits failure status or no `mermaidjsDiagram`.

Image checks:

- A text-to-image model config must exist for the user/server.
- OpenAI, Google, and Replicate paths require provider-specific API keys/model names.
- OpenAI may reject prompts for content policy violations.
- Generated image upload can fall back to inline WebP data if storage upload fails.

Diagram checks:

- Diagram output depends on a capable chat model and valid Mermaid.js generation.
- Diagrams are for visual relationships and flowcharts; charts/quantitative plots belong to `/code`.

Fix path:

1. Verify model provider/API config and selected model capability.
2. Check whether prompt enhancement failed before generation or the generation provider failed afterward.
3. For policy blocks, rewrite the prompt rather than retrying unchanged.
4. For Mermaid failures, simplify the requested diagram and ensure the model response is clean Mermaid syntax.

## Voice or Speech Failing

Symptoms:

- `POST /api/chat/speech` returns 503.
- Web UI voice response does not play.
- Voice input transcription works but spoken response fails.

Checks:

- Text-to-speech requires `ELEVEN_LABS_API_KEY`.
- A user voice model can override the default voice id; an invalid voice id can fail provider-side.
- Speech-to-text setup for voice input is separate from `/api/chat/speech`.

Fix path:

1. Confirm `ELEVEN_LABS_API_KEY` is present in the running server environment.
2. Verify any configured voice id exists in the provider account.
3. If the issue is speech-to-text or admin voice model setup, route broader configuration to `deployment-api`.

## Operator Unavailable or Unsafe to Run

Symptoms:

- `/operator` falls back to default chat behavior.
- Operator status appears but browser/computer actions fail.
- Research operator step errors or stalls.

Checks:

- `KHOJ_OPERATOR_ENABLED=true` is required for parser recognition and automatic tool exposure.
- Operator is experimental and current notes limit supported models to Anthropic Claude 3.7+/Sonnet/Opus-class models.
- Runtime may require Docker, browser/container support, Playwright, and Docker socket access depending on deployment.
- Operator can perform external actions; do not run it during verification unless the user explicitly approves an operational test.

Fix path:

1. Confirm the feature flag and model/provider are correct.
2. Validate the operator environment separately only when safe.
3. For implementation changes, preserve cancellation/interrupt behavior and partial operator context persistence.

## Research Rate Limited or Interrupted

Symptoms:

- `/research` returns a daily command limit message.
- WebSocket interrupt stops or modifies an in-flight research turn.
- History includes partial `researchContext` or `operatorContext` without a final answer.

Root causes:

- Research is command-rate-limited when billing is enabled: 20 daily uses for trial users and 75 for subscribed users.
- WebSocket interrupts persist partial context so a turn can stop or continue with a new instruction.
- Research may use multiple child tools, so a single missing web/code/operator prerequisite can degrade the result.

Fix path:

1. Check subscription/billing state before changing rate-limit code.
2. Inspect persisted train-of-thought/status and partial contexts in conversation history.
3. Verify child tool prerequisites one by one.
4. Keep `research` as a single-command path when selected; mixed research plus other commands is intentionally suppressed.

## Share Domain Errors

Symptoms:

- `POST /api/chat/share` returns `401 Unauthorized domain`.
- Share URLs use `http` unexpectedly or fail behind a reverse proxy.
- Shared conversation history hides or replaces agent metadata.

Root causes:

- The request `Host` domain must be in `ALLOWED_HOSTS`.
- If request scheme is `http`, Khoj upgrades generated share URLs to `https` unless `KHOJ_NO_HTTPS=true` or the base URL is local.
- Private hidden agents are not exposed to viewers who cannot access them.

Fix path:

1. Check `KHOJ_DOMAIN`, `KHOJ_ALLOWED_DOMAIN`, proxy host headers, and `KHOJ_NO_HTTPS` with `deployment-api`.
2. Use the externally visible host when creating share links.
3. Expect public share history to scrub inaccessible private agent metadata.

## Image Upload Limits

Symptoms:

- Chat with images returns a 429-like message about too many or too-large images.
- WebSocket sends an error before starting chat processing.

Limits:

- Max images per chat message: 10.
- Max combined image payload size: 20 MB for the chat route/WebSocket configuration.
- Limits are enforced only when billing is enabled and the user is authenticated.

Fix path:

1. Reduce image count or compress images before sending.
2. Ensure images are valid base64/data URI strings.
3. Do not bypass limiter logic except for deliberate billing/deployment policy changes.
