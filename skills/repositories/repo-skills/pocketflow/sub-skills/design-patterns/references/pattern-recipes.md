# PocketFlow pattern recipes

Use these recipes when you need to decide which PocketFlow shape fits a task.

## 1. Workflow

Choose workflow when the task has a clear sequence of stages.

### Common shape
- `outline -> draft -> review -> finalize`
- `extract -> normalize -> validate -> publish`
- `plan -> execute -> reflect`

### Shared-store keys
- `input`, `topic`, `query`, `source_text`
- `outline`, `draft`, `results`, `final`

### Validation step
- Validate the stage output in `post()` or a dedicated review node.
- If the LLM output has a structured form, assert required keys before continuing.

## 2. Agent

Choose agent when the next step depends on runtime context.

### Common shape
- `decide -> tool -> decide`
- The decision node inspects the current context and returns an action.
- The tool node updates the shared store and sends control back to the decision node.

### Useful action space design
- Keep action names mutually exclusive.
- Separate retrieve/search actions from answer/finalize actions.
- Avoid duplicating similar actions that differ only in phrasing.

### Shared-store keys
- `context`, `history`, `tool_results`, `decision`, `answer`

### Validation step
- Assert the decision output has a recognized action.
- If using YAML or JSON, parse and validate before returning the action string.

## 3. RAG

Choose RAG when answer quality depends on retrieving relevant context from a document set.

### Offline stage
- chunk documents
- embed chunks
- store vectors/index entries

### Online stage
- embed the query
- retrieve top matches
- generate the answer with retrieved context

### Shared-store keys
- `files`, `chunks`, `embeddings`, `index`, `question`, `retrieved_chunk`, `answer`

### Validation step
- Verify chunk counts and embedding dimensions.
- Confirm the retrieved context is non-empty and aligned with the question.
- If the answer depends on a vector backend, document that backend as optional unless the task requires it.

## 4. Map-reduce

Choose map-reduce when many independent items can be processed and aggregated.

### Common shape
- `chunk -> map each item -> aggregate`
- `file -> summarize each file -> combine summaries`

### Shared-store keys
- `items`, `chunks`, `partials`, `aggregate`, `final`

### Validation step
- Confirm each map result has the expected type.
- Make the reduce step robust to empty inputs.

## 5. Structured output

Choose structured output when an LLM must produce a dictionary, list, YAML block, or schema-like result.

### Common shape
- Prompt the model with a concrete schema.
- Parse the output.
- Assert required keys and types.
- Retry on malformed output.

### Validation step
- Check the parsed object before storing it in `shared`.
- Keep schema validation close to the producing node.

## 6. Multi-agent

Choose multi-agent when two or more role-specific nodes coordinate through messages.

### Common shape
- `hinter -> guesser -> hinter`
- `planner -> worker -> reviewer`
- Use queues or a message list in shared state.

### Shared-store keys
- `messages`, `queues`, `past_guesses`, `turn`, `status`

### Validation step
- Ensure each role has a clear contract.
- Make the stop condition explicit so the loop can terminate.

## 7. Service/background pattern

Choose this when PocketFlow is embedded in a web app or background job system.

### Common shape
- `request -> enqueue job -> progress updates -> result`
- `submit -> background worker -> status stream -> final artifact`

### Shared-store keys
- `job_id`, `queue`, `progress`, `result`, `errors`

### Validation step
- Keep the flow itself independent from the web framework.
- Treat web handlers as thin orchestration around the graph.

## 8. Structured agentic-coding project layout

A simple PocketFlow app often fits this layout:

- `main.py` entry point
- `flow.py` graph wiring
- `nodes.py` node definitions
- `utils/` utility functions
- `requirements.txt`
- optional `docs/design.md`

Use this layout when a user asks for a repo-style PocketFlow app that is easy to inspect and test.

## 9. Pattern selection cheat sheet

- Use **workflow** for fixed stages.
- Use **agent** for dynamic decisions.
- Use **RAG** when context retrieval matters.
- Use **map-reduce** for many independent items.
- Use **structured output** for schema-like LLM replies.
- Use **multi-agent** for coordinated roles.
- Use **service/background** when a web app or queue sits around the graph.

## 10. What not to do

- Do not force one generic graph shape onto every problem.
- Do not mix provider calls, retrieval, and UI code into one node if separate utilities are clearer.
- Do not make action names ambiguous.
- Do not skip validation just because the model usually behaves well.
