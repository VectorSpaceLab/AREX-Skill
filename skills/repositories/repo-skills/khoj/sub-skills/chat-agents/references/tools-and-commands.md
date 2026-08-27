# Tools, Commands, and Output Modes

Khoj chat can use explicit slash commands or infer tools automatically from a default query. Commands are represented by `ConversationCommand` values and are not identical to agent option enums.

## Slash Commands

| User prefix | Command value | Behavior |
| --- | --- | --- |
| `/notes` | `notes` | Search the user's or selected agent's knowledge base and answer from notes. |
| `/general` | `general` | Answer from model/general knowledge without note retrieval. |
| `/default` or no command | `default` | Ask a fast model to choose sources and output mode from available options. `/default` itself is not matched explicitly; unmatched prefixes fall back to default. |
| `/online` | `online` | Search the web, read top webpages, and include online references. |
| `/webpage` | `webpage` | Infer and read specific webpage URLs relevant to the query. |
| `/image` | `image` | Generate a creative image and then produce a text response around it. |
| `/diagram` | `diagram` | Generate a Mermaid.js diagram and then produce a text response around it. |
| `/code` | `code` | Generate and run simple Python in a sandbox, then answer from results. |
| `/research` | `research` | Run the multi-step research loop; when selected, it suppresses other chat commands. |
| `/operator` | `operator` | Operate a browser/computer environment when the operator feature is enabled. |
| `/help` | none in route parser | Described in prompts/docs for users; route parser does not return a dedicated `help` command. |
| `/automated_task` | `automated_task` | Preprocessed before normal chat command detection so it can combine with another command. Route automation ownership elsewhere. |

Only the first recognized leading command is returned by the route parser. The automatic `default` path can still select multiple sources plus one output mode, such as `online` plus `code` with `text`, or `notes` plus `image`.

## Automatic Tool Selection

When command resolution yields `default`, Khoj asks a fast chat model to choose:

- input sources from currently enabled tools, filtered by the selected agent's `input_tools` when non-empty;
- one output mode from valid modes, filtered by the selected agent's `output_modes` when non-empty.

The chooser removes unavailable options before prompting:

- `notes` is hidden if the user has no entries.
- `operator` is hidden unless `KHOJ_OPERATOR_ENABLED=true`.
- `online` and `webpage` are hidden unless web search is enabled.
- `code` is hidden unless a code sandbox is enabled.

If the chooser returns invalid sources, chat falls back to `[default]` for unrestricted agents or `[general]` for agents with restricted sources. If it returns an invalid output mode, chat falls back to `text`.

## Agent Tools vs Chat Commands

Agent `input_tools` currently allow only `general`, `online`, `notes`, `webpage`, and `code`. Agent `output_modes` currently allow `image` and `diagram`.

Do not assume every `ConversationCommand` can be stored on an agent:

- `research` and `operator` are chat/research command values but not current agent input-tool choices.
- `image` and `diagram` are output modes, not input tools.
- Internal research tool values such as `search_web`, `read_webpage`, `semantic_search_files`, `regex_search_files`, `view_file`, `list_files`, `run_code`, and `operate_computer` are for the research loop/tool-calling layer, not user-facing agent payloads.

## `/notes`

What it does:

- Calls chat-side document search with the query, `n`, optional distance `d`, current conversation history, location, attached files/images, relevant memories, and selected agent.
- Emits `status` events about found notes and sends note references in the `references.context` event.
- Uses file/query filters via the search layer; route detailed filter syntax and embedding/ranking issues to `search-retrieval`.

Failure behavior:

- If note search raises, Khoj emits a status saying document search failed and tries to respond without document references.
- If `/notes` is the only command and the user has no entries, Khoj returns the no-entries response.
- If notes were selected among multiple tools but no references are found, Khoj removes `notes` from the command set and continues with other tools.

## `/general`

What it does:

- Skips note/online/code/operator retrieval and proceeds to model response generation with conversation history, memories, location, attached files/images, and agent persona.
- Useful for debugging whether failures come from retrieval/tools or from the base chat model/provider.

Failure behavior:

- Still requires a valid chat model and provider/API setup.
- Still may fail for provider rate limits, invalid model names, prompt-size issues, or missing API keys.

## `/online`

What it does:

- Generates up to three online search subqueries.
- Uses configured web search providers and reads selected webpage content.
- Emits status updates such as browsing links and returns deduplicated online references in `references.onlineContext`.

Prerequisites:

- Web search is enabled when at least one of `GOOGLE_SEARCH_API_KEY`, `SERPER_DEV_API_KEY`, `EXA_API_KEY`, `FIRECRAWL_API_KEY`, or `KHOJ_SEARXNG_URL` is set.
- Docker-based deployments commonly use SearXNG through `KHOJ_SEARXNG_URL`; production-grade hosted search often uses `SERPER_DEV_API_KEY`.
- Internet access is still needed unless the provider is a local reachable service with cached/private data.

Failure behavior:

- Search errors are logged and Khoj emits a status saying online search failed, then tries to answer without online references.
- Poor results can come from disabled provider config, provider quota/rate limits, blocked network, missing location hints, or too-long provider queries.

## `/webpage`

What it does:

- Infers specific webpage URLs to read, or uses URLs obvious from the query.
- Reads up to one webpage in the direct chat path and adds extracted content under `onlineContext[query].webpages`.
- Emits a `Read web pages` status with the chosen links.

Prerequisites:

- Same web-search enablement gate as `/online` for automatic/default tool exposure.
- Webpage scraping can fall back to plain HTTP requests; configured web scrapers such as Firecrawl, Olostep, or Exa can improve extraction.

Failure behavior:

- Read errors are logged and Khoj emits a status saying webpage read failed, then tries to answer without webpage references.
- Validate URLs, scraper credentials, reachable network, and blocked/private webpage access before changing chat logic.

## `/code`

What it does:

- Builds context from note references and online results.
- Asks the model to generate a simple Python snippet.
- Executes the code in an ephemeral sandbox.
- Returns `codeContext` in references and uses it in the final answer.

Prerequisites:

- Code sandbox is enabled when `KHOJ_TERRARIUM_URL` is set or `E2B_API_KEY` is set.
- Terrarium/Pyodide has no network access and a smaller package set.
- E2B has network access and a broader package set; optional `E2B_TEMPLATE` can select a sandbox template.
- The chat model must be able to produce fenced Python code; generated code is cleaned before execution.

Failure behavior:

- If code generation or execution raises `ValueError`, Khoj adds `Failed to run code` to program context and continues to answer without code results.
- For sandbox failures, check sandbox URL/API key, service reachability, timeout, generated code shape, unavailable packages, and whether the task asks for unsafe code.

## `/image`

What it does:

- Uses the user's text-to-image model config to generate a creative image.
- For non-multimodal image models, first improves the image prompt using chat history, note references, online results, attached images/files, memories, and agent persona.
- Emits `generated_assets` with `images` on success, and stores generated images in conversation metadata.

Prerequisites:

- A user/server text-to-image model must be configured.
- Supported provider paths include OpenAI, Google, and Replicate text-to-image configs.
- For OpenAI image generation, the configured model/API must support image generation.
- For Replicate, the model name/API key must match the Replicate model being called.

Failure behavior:

- Missing text-to-image config yields a 501-style failure message: setup image generation on the server.
- OpenAI policy violations are surfaced as image generation blocked by policy.
- Network/provider failures are converted to failed-generation context and Khoj continues with a text response.

## `/diagram`

What it does:

- Generates a better diagram description and Mermaid.js diagram syntax.
- Emits `generated_assets` with `mermaidjsDiagram` on success.
- Stores the Mermaid.js diagram in conversation metadata.

Prerequisites:

- A functioning chat model/provider capable of the diagram prompt and structured-ish output.
- The request should be a visual relationship, flowchart, architecture, or similar diagram task; charts/quantitative plots belong to `/code`, not Mermaid diagram generation.

Failure behavior:

- If diagram generation cannot produce both improved description and Mermaid.js, Khoj emits `Failed to generate diagram. Please try again later.` and continues with a fallback text response context.

## `/research`

What it does:

- Runs a multi-iteration research loop that can use internal tools for document search, regex/list/view file, online search, webpage reading, Python coding, and operator steps.
- Streams status updates as it plans, executes, and summarizes research iterations.
- If selected in the automatic/default path, it becomes the only command for that turn.

Prerequisites:

- All normal chat model/provider prerequisites.
- Research command usage is rate-limited under billing-enabled mode: 20 daily command uses for trial users and 75 for subscribed users.
- The specific tools used inside research have their own prerequisites: web search, code sandbox, operator, and indexed notes.

Failure behavior:

- The research loop records partial iterations. Interrupted WebSocket turns can persist partial `researchContext` and resume/continue with an interrupt query.
- If a requested internal tool is unavailable, research should skip or adapt, and the troubleshooting target is usually the tool prerequisite rather than `/api/chat` transport.

## `/operator`

What it does:

- Runs a browser/computer operator environment and appends visited webpage references into `onlineContext` when available.
- Can be invoked directly with `/operator` when enabled, or internally through research.

Prerequisites:

- `KHOJ_OPERATOR_ENABLED=true`.
- Operator runtime dependencies such as container/browser environment and Playwright support.
- Current operator notes indicate Anthropic Claude 3.7+/Sonnet/Opus-class models are the supported operator models during the experimental phase.
- Docker socket/container access may be needed for the computer environment depending on deployment.

Failure behavior:

- If operator is disabled, `/operator` is not recognized by `get_conversation_command` and falls back to `default` rather than returning an operator command.
- Operator execution `ValueError` adds `Browser operation error: ...` to program context and emits a status saying browser operation failed.

## Voice and Speech

Voice input is usually client-side speech-to-text feeding normal chat text. The chat-side speech endpoint is text-to-speech:

- `POST /api/chat/speech?text=<text>` streams `audio/mpeg`.
- It uses the user's configured voice model when present, otherwise a default voice id.
- Text-to-speech requires `ELEVEN_LABS_API_KEY`; missing key raises a 503 response with the underlying error message.

Speech-to-text model setup and voice model options are admin/deployment configuration, not chat route logic.

## Mixed Command Case

For a query like `Build a small report from current web data and plot it`, the default path may select `online`, `code`, and `text`:

1. Online search gathers fresh facts and webpage snippets.
2. Code execution receives the note/online context and generates/runs Python for calculations or chart/document output.
3. References include both `onlineContext` and `codeContext`.
4. Final answer generation receives both contexts and any generated files/assets.

For a query like `/online /code compare current exchange rates`, only the first recognized leading command matters. Because the parser sees `/online`, `/code` is not separately parsed as a command. If both tools are required deterministically, prefer default inference with clear wording or modify the route logic deliberately.
