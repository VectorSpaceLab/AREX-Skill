# Troubleshooting Workflow Execution

## “This workflow JSON fails when POSTed”

Likely cause: the file is a UI workflow export, not API prompt JSON. UI exports usually have top-level `nodes` and `links`; API prompts are objects keyed by node id with `class_type` and `inputs`. Convert/export to API format, then wrap it as `{ "prompt": ... }` for the server request.

## “Node has no class_type”

Every API prompt node needs `class_type`. If the source is a UI workflow, find the node's type/name in the UI metadata and map it to the runtime class mapping. If it is a custom node, confirm the custom node package is installed and registers that mapping.

## “Node not found” or unresolved reference

A linked input such as `["12", 0]` references upstream node `12`. Fix the link if node `12` was renamed, omitted during conversion, or stored as a numeric id while the prompt uses string keys. Also check nested/template substitutions that accidentally remove nodes.

## “Output index out of range”

The upstream node exists, but the requested output socket does not. Output indexes are zero-based. Inspect the node's `RETURN_TYPES` or public API output schema and update the second element of the link.

## “Wrong widget/input type”

Static graph validation cannot know all node-specific types. Check the node's `INPUT_TYPES`, combo options, min/max constraints, and custom validation method. Common mistakes include numeric strings where numbers are expected, model filenames that are not in a combo list, image links passed to latent/model inputs, or stale custom-node input names.

## “Nothing ran” or “No output”

Check that intended output nodes are present and reachable. `SaveImage`/`PreviewImage`-style nodes make results visible in history/UI. Also verify partial execution targets, lazy branches, and whether the node was cached rather than executed.

## “A branch was skipped”

Lazy inputs are only evaluated when requested by the consuming node. If a mask, condition, switch, or lazy-check node does not require one branch, upstream nodes on that branch may not run. This is expected unless the node's lazy status logic is wrong.

## “Async validation failed”

Async validation failures happen before the node runs and usually return a request validation error. Capture the failing node id and validation message, then inspect threshold/range/combo/file/model inputs. Do not debug it as a websocket transport problem unless the server accepted the prompt and later emitted an execution error.

## “Async node timed out or errored”

Runtime async failures should include prompt and node context. Check timeout parameters, external API latency, model/backend initialization, and whether concurrent async branches share resources. After a failure, a later independent prompt should still be able to run; if not, inspect server logs and custom node cleanup behavior.

## “Cache behavior is surprising”

Cache reuse depends on input signatures, linked ancestry, `IS_CHANGED`/fingerprint outputs, hidden unique ids, non-idempotent flags, selected cache mode, and eviction. If a node re-runs, compare constants and upstream signatures. If a node stays cached unexpectedly, confirm its `IS_CHANGED` or fingerprint logic accounts for the external state that changed.

## “Inference test is too expensive”

Full inference workflows can require model files, memory, and backend support. First validate prompt shape and links. Then check model paths and backend flags. Treat full image/video/audio generation as an expensive integration test, not as the first debugging step.
