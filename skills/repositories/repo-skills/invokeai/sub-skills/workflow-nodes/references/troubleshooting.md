# Troubleshooting Workflow Nodes

Use this page to map node/graph symptoms to likely causes and focused fixes.

## Node Import and Registration

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Custom node type is unknown in workflow JSON | Node pack did not import, lacks `__init__.py`, is hidden/underscored, or the class is not imported by the pack `__init__.py` | Ensure the pack directory has `__init__.py`, import every node class there, then restart InvokeAI. |
| Startup logs say a pack failed to load | Import-time exception in the node pack | Fix imports and top-level side effects. A failed pack may partially register classes; restart after fixing. |
| Warning about overriding a core/custom node | Duplicate `@invocation("type")` or duplicate `@invocation_output("type")` | Rename the node/output type to a globally unique value. Treat core-node clobbering as unsafe. |
| Node changes do not appear in the UI | Node packs load at app startup | Restart InvokeAI after adding/changing nodes. Route custom node directory/config questions to `../operations-config/`. |
| A built-in node disappears from validation | `allow_nodes`/`deny_nodes` config excludes it | Route allow/deny config work to `../operations-config/`. |

## Decorator and Field Errors

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `Invalid version string for node` | `@invocation(..., version=...)` is not semver | Use a semver string such as `1.0.0`; do not use `v1`, `1`, dates, or free text. |
| `must implement the invoke method` | Invocation subclass does not override `invoke()` | Add `def invoke(self, context: InvocationContext) -> ConcreteOutput:`. |
| `must have a return annotation of a subclass of BaseInvocationOutput` | Missing, string-unresolvable, base-class, or wrong return annotation | Define/decorate a concrete output class first and annotate `invoke()` with it. |
| `Invalid field definition` | A class field is not `InputField(...)` or `OutputField(...)`, or lacks type annotation | Annotate every node input and output model field and use the field helpers. |
| `Invalid field name` | Field uses reserved names such as `id`, `type`, `metadata`, `board`, `output_meta` | Rename the field or use `WithMetadata`/`WithBoard` for internal metadata/board inputs. |
| Deprecated `UIType` warnings | Old model/primitive UI hints are used | Prefer inferred primitive UI; for models use `ui_model_base`, `ui_model_type`, `ui_model_variant`, `ui_model_format`, `ui_model_provider_id`. |
| `ui_type` ignored | `ui_type` was combined with new `ui_model_*` filters | Remove `ui_type` from model fields when using `ui_model_*`. |

## Missing Inputs and Required Connections

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Required connection error before `invoke()` | Required `Input.Connection` field has no incoming edge/value | Add an edge to the field or give it a safe default if it is truly optional. |
| Missing input error before `invoke()` | Required `Input.Any` field has neither a direct value nor a connection | Provide a direct value, connect an upstream output, or set a default. |
| Node parses but fails when executing | `InputField` made the field optional for serialization, then `invoke_internal()` enforced the original requirement | Debug the original field default and `input=` metadata, not only Pydantic construction. |
| Optional field unexpectedly absent | Field is `Input.Any` or `Input.Connection` with no value and no default | Use optional typing and handle `None`, or provide an explicit default in `InputField`. |

## Graph JSON and Edge Validation

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| JSON cannot be read | File is not valid JSON | Run `python scripts/validate_workflow_json.py <file>` and fix the syntax first. |
| Missing `nodes` or `edges` | File is not a graph object or graph is nested in a workflow record | Use `--graph-key graph` when the graph is under a key, or extract the graph/session object. Route workflow records to `../workflows-queues/`. |
| Duplicate node ID | Same node ID appears more than once, or node key differs from object `id` | Make every node ID unique and keep the mapping key equal to the object's `id`. |
| Edge source/destination node missing | Edge references a node ID not present in `nodes` | Fix node IDs or remove stale edges. |
| Edge field missing | Edge references an output/input field that does not exist | Check source output model fields and destination invocation fields. The bundled script can only infer fields present in JSON; full validation needs InvokeAI imports. |
| Cycle error | Edge introduces a directed cycle | Break feedback loops; InvokeAI source graphs must be DAGs. |
| Edge already exists | Destination field already has an incoming edge | Remove the old edge or use `collect.item` for many-to-one item aggregation. |
| Field types are incompatible | Source output annotation cannot feed destination input annotation | Connect matching types, use a converter node, or make the destination type explicitly accept `Any`/union. |
| Unknown node type in full validation | Registry cannot parse the node's `type` discriminator | Ensure core/custom invocation modules are imported before validating. |

## Iterator and Collector Failures

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `Iterator must have a collection input edge` | `iterate.collection` is unconnected | Connect exactly one collection output to `iterate.collection`. |
| `Iterator may only have one input edge` | Multiple edges feed `iterate.collection` | Collect/merge upstream collections first, then feed one edge to the iterator. |
| `Iterator input must be a collection` | Source output is not `list[...]` or compatible collection | Connect a collection output or insert a collection-producing node. |
| `Iterator outputs must connect to an input with a matching type` | `iterate.item` consumers do not accept the collection item type | Adjust consumer input type or convert item values before consuming. |
| `Iterator collection type must match all iterator output types` | Iterator is fed by a collector whose resolved item type conflicts with item consumers | Make collector inputs homogeneous and match downstream consumer types. |
| `Collector must have at least one item or collection input edge` | `collect` is present with no inputs | Add `item` or `collection` input, or remove the collector. |
| `Collector collection input must be a collection` | A scalar output is connected to `collect.collection` | Connect scalar values to `collect.item`; reserve `collect.collection` for list outputs. |
| `Collector input collection items must be of a single type` | Mixed item roots feed one collector | Split into separate collectors or convert values to a shared type. |
| Collector output type mismatch | Collector output feeds a destination collection with incompatible item type | Change destination input type or normalize collector inputs. |
| Empty iterator graph seems to skip downstream collectors | Empty collection produces no iterator execution nodes | This is expected; handle empty collections before iteration if a downstream output is required. |

## Lazy If Branch Surprises

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| False branch did not execute | `If` condition resolved true and branch-exclusive false nodes were skipped | This is expected lazy behavior. Inspect selected branch and skipped prepared nodes. |
| Branch node executes before condition | Node is shared, or its outputs leave the branch, so it is not branch-exclusive | Keep expensive branch-only work feeding only that branch input, or restructure graph. |
| Nested/iterated `If` behaves differently per item | Branch resolution is per prepared execution node and iteration path | Debug `prepared_source_mapping`, iteration paths, and selected branch for each prepared `if`. |
| Collector receives only selected values | Skipped branch execution nodes are ignored by collector preparation | Expected for `If` outputs. If both values are needed, do not gate them through `If`. |
| Resume after JSON round trip changes readiness | Runtime queues must be rehydrated from serialized execution graph/results | Validate the serialized `GraphExecutionState` and check `indegree`, `executed`, and branch condition outputs. |

## Context and Service Misuse

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Image mutation leaks to other nodes | Node modifies a shared object instead of a copy | Use `context.images.get_pil()`, which returns a copy, and save a new image. |
| Saved image lacks metadata or board assignment | Node did not inherit `WithMetadata`/`WithBoard`, or override args were passed incorrectly | Add mixins to image-producing nodes, or pass explicit `metadata`/`board_id` intentionally. |
| Long node ignores cancellation | Node never calls `context.util.is_canceled()` | Check cancellation inside loops and return/raise consistently with node behavior. |
| Model load fails for external API model | External API models cannot be loaded from disk | Use model-management guidance and external-provider APIs instead of `context.models.load()`. |
| Unit test is hard to set up | Node uses full services instead of context facade or has import-time side effects | Mock `InvocationContext` methods with `MagicMock`; keep imports side-effect-light. |

## Fast Debug Checklist

1. Confirm the node pack imports and registered node/output types are unique.
2. Confirm every invocation/output field has a type annotation and uses `InputField`/`OutputField`.
3. Confirm `invoke()` return annotation names a decorated output class.
4. Run `scripts/validate_workflow_json.py` to catch structural graph issues before full InvokeAI validation.
5. For full validation, import the same custom node packs before parsing graph JSON.
6. For execution failures, separate graph validation errors from `invoke_internal()` required-input checks and context-service failures.
7. For iterator/collector/if bugs, inspect prepared execution IDs, source mapping, iteration paths, skipped branches, and collector input edge ordering.
