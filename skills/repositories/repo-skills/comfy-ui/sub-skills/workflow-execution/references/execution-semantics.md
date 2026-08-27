# Execution Semantics

## Validation Order

ComfyUI execution starts with a prompt graph and validates progressively:

1. JSON/request shape is parsed by the API client/server.
2. Each node id resolves to a node object with `class_type` and `inputs`.
3. `class_type` resolves through the active node registry.
4. Input names and constant values are checked against the node's `INPUT_TYPES` or public API schema.
5. Links are resolved as dependencies and output indexes are read from upstream cached/executed results.
6. Node-level `VALIDATE_INPUTS`, including async validation, may reject values before execution.
7. Runtime execution can still fail because of model files, backend availability, tensor/image shapes, timeout, or node code exceptions.

Keep structural prompt validation separate from node-schema and runtime validation. A prompt can be valid JSON and still fail because a node is missing, a model name is unavailable, or a custom node rejects an input.

## Dependency Graph

Execution uses a dynamic prompt and a topological execution list:

- Strong links are non-lazy linked inputs that must be ready before a node runs.
- A node becomes ready when all blocking upstream dependencies are executed or cached.
- Dependency cycles are reported as graph errors.
- Dynamic or ephemeral nodes can be added by graph-building behavior during execution, while display/parent ids keep errors attributable to user-visible nodes.

A linked input is only available after the upstream node has produced outputs. If the upstream node is missing or the output index is out of range, the downstream input is marked missing and execution/validation will fail.

## Lazy Inputs

Some node inputs are lazy. Lazy dependencies are not scheduled until the node decides they are needed. This enables patterns such as a mask/mix node that only evaluates one branch. When diagnosing “why did this upstream node not run?”, check whether the input is lazy and whether the runtime condition selected that branch.

Async lazy checks can also decide which inputs are required. A skipped lazy branch is not an execution failure if the node's lazy logic intentionally did not request it.

## Async Nodes

ComfyUI supports async execution and async validation paths. Execution tests cover:

- async nodes running successfully,
- independent async nodes progressing in parallel,
- async nodes waiting on dependencies,
- async `VALIDATE_INPUTS` failures returning validation errors,
- async lazy checks,
- async runtime exceptions carrying prompt/node context,
- timeout handling and recovery for later runs.

When debugging async failures, capture the node id, prompt id, error type/message, and whether the failure came from validation before scheduling or from runtime execution after the node started.

## Progress and Output Metadata

Websocket progress/executing messages include prompt ids and node ids. Clients should filter messages by the submitted `prompt_id`, especially when multiple prompts or clients are active. Output history stores node output metadata such as image filenames, subfolders, types, and other node-specific `ui`/output fields. Binary previews may arrive over websocket but final outputs are usually recovered from history/view endpoints.

Output nodes such as `SaveImage` and `PreviewImage` are important because they make results visible in history/UI. If a prompt has no reachable output node and no partial execution target, it may execute nothing useful from a user's perspective.

## Cache Modes

ComfyUI supports multiple cache behaviors:

- Classic cache keeps hierarchical output/object caches keyed by input signatures.
- LRU cache limits output cache size while preserving object cache behavior.
- RAM pressure cache evicts based on available memory headroom.
- No cache disables intermediate reuse.

Output cache keys are based on input signatures: node `class_type`, `IS_CHANGED`/fingerprint results, linked ancestry, constant input values, and sometimes node id. Node id becomes part of the signature for non-idempotent nodes or nodes that receive hidden `UNIQUE_ID`.

## Why a Node Re-executes

A node can re-run when:

- a constant input changes,
- an upstream node input/signature changes,
- `IS_CHANGED` or `fingerprint_inputs` reports a new value,
- a node is non-idempotent,
- a hidden unique id is part of its signature,
- cache mode is `none`, cache size evicted it, or RAM pressure dropped it,
- a custom/external cache provider declines or cannot reuse the value.

A downstream node may still be cached if its effective input signature is unchanged. Conversely, changing a seemingly unrelated UI field can invalidate cache if that field is included in node inputs or fingerprints.
