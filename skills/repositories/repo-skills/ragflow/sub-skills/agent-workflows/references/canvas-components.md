# Canvas DSL and Components

## DSL Envelope

RAGFlow agent workflows are stored as a JSON DSL. The backend accepts legacy DSLs through a normalizer, but runtime execution centers on these keys:

- `components`: map of component ID to `{obj, upstream, downstream}`. `obj.component_name` selects the Python component/tool class and `obj.params` feeds the matching parameter object.
- `path`: runtime execution path. Fresh agent workflows normally start with `begin`; ingestion/dataflow canvases can start from file-oriented nodes.
- `globals`: system and environment variables. Common system keys include `sys.query`, `sys.user_id`, `sys.conversation_turns`, `sys.files`, `sys.history`, and `sys.date`.
- `history`: assistant/user history carried by the canvas runtime.
- `retrieval`: accumulated chunk/reference data used for citations and final responses.
- `memory`: memory state associated with the canvas.
- `variables`: optional environment-variable definitions whose values reset into `env.*` globals.
- `graph`: optional visual nodes/edges used by import/export and layout tooling; do not treat visual layout as execution semantics.

Component IDs are not guaranteed to be human-friendly. Templates often use IDs like `Agent:StalePandasDream` or `Message:BrownPugsStick`; use the exact ID in references and downstream lists.

## Execution Model

`Canvas.run(...)` is asynchronous and yields event dictionaries. Important event names include:

- `workflow_started`: emitted before component execution with request inputs.
- `node_started`: emitted before a component in the current path slice runs.
- `message`: streamed content from a `Message` component or streamed upstream content.
- `message_end`: final message metadata after a message component completes.
- `node_finished`: component inputs, outputs, error, elapsed time, component ID/name/type, and thoughts.
- `user_inputs`: emitted when a `UserFillUp` component asks for more input and the run pauses.
- `workflow_finished`: final workflow output and elapsed time.

Execution expands `path` dynamically:

- Normal components append their `downstream` IDs.
- `Switch` and `Categorize` append the component output `_next`.
- `Iteration` and `Loop` append their internal start component (`IterationItem` or `LoopItem`).
- `IterationItem`/`LoopItem` can return control to the parent or parent downstream when their loop ends.
- `ExitLoop` exits a `Loop` and appends the parent downstream.
- Components with `exception_goto` can reroute execution on error instead of using normal downstream edges.

The runtime batches the current path slice and invokes components concurrently up to the internal thread pool limit. A component is skipped/removed from the immediate slice when it references an upstream component that has not yet run. This makes reference correctness and path ordering critical.

## Variables and References

RAGFlow resolves variables in component inputs and message/template text with these forms:

- `{component_id@output}` or `{{component_id@output}}`: reads a component output key.
- `{component_id@output.sub.path}`: reads nested dict/list/object fields with dot notation; list indexes are allowed.
- `{sys.query}`, `{sys.user_id}`, `{sys.files}`, `{sys.history}`, `{sys.date}`: reads runtime globals.
- `{env.name}`: reads environment variables defined in the canvas `variables` map.
- `{item}`, `{index}`, `{result}`: aliases inside an `Iteration` child workflow; they resolve to the current `IterationItem` output when used by internal components.

If a referenced component ID is missing, runtime raises a variable lookup error. If a nested field cannot be decoded or found, nested lookup returns `None`, which often renders as an empty string in text contexts. For this reason, debug broken prompts by checking both the component ID and the exact output key.

## Core Components

- `Begin`: initializes workflow inputs. Webhook mode can map `webhook_payload.input` to the Begin `request` input and exposes other payload keys as Begin outputs.
- `UserFillUp`: requests missing user-provided fields and can pause the run with `user_inputs`.
- `LLM`: plain LLM generation component with prompt variables, optional citation support, model settings, and streaming behavior.
- `Agent`: LLM planner/worker component that can call in-canvas tools, sub-agents, plugin-style tools, and MCP tools. It supports max rounds, retries, framework prompt overrides, structured output, and citations.
- `Message`: formats final or intermediate response content. It consumes variable references, streams partials, can expose downloads, can auto-play TTS, and can save selected content to memory.
- `Retrieval`: tool component for datasets and/or memories. It outputs `formalized_content`, may output JSON chunk data, and adds references for citation-aware downstream nodes.
- `Switch`: rule-based branching. Cases support operators such as equals, not equals, comparisons, contains, starts/ends with, empty/not empty. Empty condition component IDs fall through to else.
- `Categorize`: LLM-driven branching for classification-like routing.
- `Iteration`: splits/iterates over an array referenced by `items_ref`; children use `IterationItem` and aliases such as `{item}`.
- `Loop`: initializes loop variables and repeats its internal `LoopItem` workflow until termination conditions or maximum count stop the loop.
- `ExitLoop`: exits a loop and continues at the parent downstream component.
- `Invoke`: calls another configured component/canvas path as part of a workflow.
- `VariableAssigner`, `VariableAggregator`, `DataOperations`, `ListOperations`, `StringTransform`: transform, assign, aggregate, or reshape data for downstream references.
- `Browser`, `DocGenerator`, `ExcelProcessor`: specialized components with optional dependencies and environment requirements.

## Agent Component Details

An `Agent` component has two modes:

- Standalone: without tools, it behaves like an LLM component and emits `content` or structured output.
- Planner/tool user: with tools, sub-agents, or MCP bindings, it binds tool metadata to the chat model and records tool traces through the canvas callback.

Tool names are indexed internally to avoid collisions, for example a tool function may become `search_my_dataset_0`. Keep tool descriptions specific because the model sees the tool schema. For sub-agents, the `Agent` component exposes a callable schema with `user_prompt`, `reasoning`, and `context`, so supervisor prompts should explain when to delegate and what state to pass.

Structured output is supported by defining an output schema under the Agent outputs. If parsing fails, the component can retry formatting to JSON up to the configured retry count before setting `_ERROR`.

## Sessions, Completion, Debug, and Logs

Behavior-level API surfaces include:

- Agent sessions: create/list/get/delete sessions under an agent, with normalized messages and per-message references.
- Agent completion: chat completion routes can run with or without existing session state, can stream, can return traces, and can execute against the runtime canvas replica.
- Component input form: returns a component's expected runtime inputs.
- Component debug: resets a canvas, injects `params` as debug inputs for a component, and runs that component in isolation where possible.
- Agent logs: retrieves trace records for a message/task when available.
- Reset and rerun: reset canvas runtime state or rerun parts of an existing DSL for debugging.

For exact REST paths and SDK method names, use the `sdk-http-integration` sub-skill. For backend route implementation details, use `backend-api-services`.

## Template Import and Export Checks

Before importing or editing a template, check:

- JSON parses and either the root or `dsl` contains `components`.
- Every component has `obj.component_name` and a params object, even if empty.
- Every `upstream`, `downstream`, `exception_goto`, Switch/Categorize target, Loop/Iteration child parent, and graph edge target points to an existing component ID.
- `path` starts from an existing component and does not contain obsolete IDs.
- `globals` includes expected `sys.*` keys for the intended entrypoint.
- Variable references match real component IDs and plausible output keys.
- Visual `graph.nodes[].data.form` and `components[*].obj.params` are not unintentionally divergent after round-trip conversion.
