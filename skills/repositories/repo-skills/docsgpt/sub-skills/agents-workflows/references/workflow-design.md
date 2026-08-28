# Workflow Design

## Graph contract

Node types: `start`, `end`, `agent`, `note`, `state`, `condition`, `code`.

A run starts with shared state including `query` and `chat_history`. Node output defaults to `node_<node_id>_output`; an agent/code node can write a named output variable. Persisted execution logs hold state deltas, not full snapshots.

## Syntax boundary

| Field | Syntax | Example |
|---|---|---|
| Agent prompt template | `{{name}}` substitution | `Summarize {{document_text}}` |
| End output template | `{{name}}` substitution | `Result: {{summary}}` |
| Set State expression | CEL | `retry_count + 1` |
| Condition case expression | CEL | `needs_review && retry_count < 3` |

Do not use braces in CEL. Do not use bare CEL identifiers where a template expects braces.

## Nodes

### Start and End

Use exactly one reachable start. Every branch should eventually reach an end. End renders the user-visible output from state.

### Agent

Important config: `agent_type`, `system_prompt`, `prompt_template`, `output_variable`, `stream_to_user`, `tools`, `sources`, `chunks`, `retriever`, `model_id`, `json_schema`, `input_documents`, and `file_passing` (`auto`, `native`, `extract`).

### State

Each operation needs `target_variable` and a CEL `expression`. Use stable semantic names between branches instead of wiring every later node to generated output names.

### Condition

First true case wins; every condition needs an else branch. Every case source handle needs an outgoing edge. A runtime expression error skips that case, often causing unexpected else routing.

### Code

Runs in a sandboxed run-scoped session. Keep code bounded, pass explicit files/artifact refs, emit small JSON/state results, and treat generated files as artifacts. Configure the sandbox before using code nodes.

## Document passing

Agent nodes can select attached/run documents. `auto` passes natively when the model accepts the MIME type and otherwise extracts text; `native` fails on unsupported MIME; `extract` always parses to text. File counts and parsing calls are bounded by deployment settings.

## Graph checklist

- unique node/edge ids;
- one start and at least one end;
- no edge references missing nodes;
- no unreachable operational nodes;
- every reachable branch reaches an end;
- condition cases and else have outgoing edges;
- state read only after a predecessor writes it;
- loops have counters/termination and global run limits;
- only intended nodes stream to the user;
- code/tool side effects have approvals/idempotency;
- outputs remain JSON-serializable where state persistence requires it.

Use the bundled offline validator first, then run a tiny workflow with mocks/test services before production inputs.
