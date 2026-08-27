# Workflow authoring troubleshooting

Use this guide after a dry validation error, confusing branch behavior, or template failure. The remedies are safe configuration edits; they do not require starting a broker, gateway, agent, or LLM.

## First response checklist

1. Run the dry validator:

   ```bash
   python sub-skills/workflow-authoring/scripts/validate_workflow_config.py path/to/workflow.yaml
   ```

2. If the file contains multiple workflow apps, select one:

   ```bash
   python sub-skills/workflow-authoring/scripts/validate_workflow_config.py path/to/workflow.yaml --app WorkflowName
   ```

3. Fix structural errors before reasoning about live runtime behavior. Missing ids, invalid node types, branch dependency mistakes, and template typos are cheaper to catch statically.
4. If package-backed validation is unavailable, use the static errors and warnings, then validate again in an environment where `solace-agent-mesh` is installed.

## YAML parse and include errors

### Symptom

- `YAML parse failed`
- `undefined alias`
- `could not determine a constructor for tag !include`
- A full SAM app file uses shared anchors or include directives.

### Cause

SAM configuration files may use an include/anchor preprocessor before runtime. A plain YAML parser may not know those project-local include semantics. The validator tries a safe direct load and then a heuristic extraction of workflow `app_config` blocks, but it does not execute includes.

### Fix

- Prefer validating a self-contained workflow `app_config` snippet while authoring.
- If validating a full app file, ensure the workflow app block itself is parseable without relying on included anchors for the `workflow` section.
- Service/broker anchors are not necessary for workflow schema validation; keep them out of the workflow-only snippet.
- Do not start `sam run` just to discover a schema error.

## Missing `name` or `namespace`

### Symptom

- Package validation reports missing `app_config.name`.
- Static validation reports missing `namespace`.

### Cause

Workflow app config uses `name` as the workflow agent identity. `namespace` is inherited from SAM agent config and is used for topics.

### Fix

```yaml
app_config:
  namespace: ${NAMESPACE}
  name: MyWorkflow
  workflow:
    description: ...
    nodes: [...]
    output_mapping: {...}
```

Do not replace `name` with `agent_name`; the workflow model derives inherited `agent_name` from `name`.

## Missing required workflow fields

### Symptom

- Missing `workflow.description`, `workflow.nodes`, or `workflow.output_mapping`.

### Fix

Add the minimal required workflow object:

```yaml
workflow:
  description: Explain what this workflow does
  nodes:
    - id: first_step
      type: agent
      agent_name: FirstAgent
  output_mapping:
    result: "{{first_step.output}}"
```

`output_mapping` can be simple during early authoring, but it must exist.

## Invalid or misspelled node type

### Symptom

- `Unsupported node type`
- Package validation emits many union/model errors for one node.

### Cause

The installed workflow model supports `agent`, `workflow`, `switch`, `map`, and `loop`.

### Fix

Correct `type` and required fields:

- `type: agent` requires `agent_name`.
- `type: workflow` requires `workflow_name`.
- `type: switch` requires `cases`.
- `type: map` requires `node` plus exactly one item source.
- `type: loop` requires `node` and `condition`.

## Duplicate or missing node ids

### Symptom

- Duplicate id validation error.
- Dependency, branch, map, loop, or exit handler references a non-existent node.

### Fix

- Give every node a stable unique `id`.
- Use exact id spelling in all `depends_on`, `dependencies`, switch targets, map targets, loop targets, exit handlers, and templates.
- Prefer ids that are valid path-like labels: lowercase words separated by underscores.

Example fix:

```yaml
nodes:
  - id: classify
    type: agent
    agent_name: Classifier
  - id: route
    type: switch
    depends_on: [classify]
    cases:
      - condition: "'{{classify.output.kind}}' == 'billing'"
        node: billing_handler
  - id: billing_handler
    type: agent
    agent_name: BillingAgent
    depends_on: [route]
```

## Dependency cycles

### Symptom

- Static validator reports `Dependency cycle detected`.
- No initial node exists.

### Cause

`depends_on` forms a directed graph. A node cannot depend, directly or indirectly, on itself.

### Fix

- Remove the backward dependency.
- For loops, do not make the target node depend on the loop node unless the model explicitly requires it; the loop control node invokes the target.
- For maps, the target node is an inner node invoked by the map control node.
- For switch branches, branch handlers should depend on the switch node, but the switch node should not depend on branch handlers.

## Switch branch runs too early

### Symptom

- A branch handler executes even when its case is not selected.
- Validation reports a logic error that a switch routes to a target that does not list the switch in `depends_on`.

### Cause

Switch branch target nodes are normal nodes unless gated by dependency on the switch node. The model requires branch targets to depend on the switch.

### Fix

```yaml
- id: route
  type: switch
  depends_on: [classify]
  cases:
    - condition: "'{{classify.output.kind}}' == 'billing'"
      node: billing
  default: general

- id: billing
  type: agent
  agent_name: BillingAgent
  depends_on: [route]

- id: general
  type: agent
  agent_name: GeneralAgent
  depends_on: [route]
```

Then use `coalesce` in `output_mapping` for mutually exclusive branch outputs.

## Map item source errors

### Symptoms

- `MapNode requires one of: items, withParam, or withItems`.
- `MapNode accepts only one of: items, withParam, or withItems`.
- Map target node does not exist.

### Fix

Use exactly one item source:

```yaml
- id: process_items
  type: map
  items: "{{load_items.output.items}}"
  node: process_one
```

or a static list:

```yaml
- id: process_items
  type: map
  withItems:
    - alpha
    - beta
  node: process_one
```

Ensure `process_one` exists and is authored as the inner target. The target may be an `agent` or `workflow` node.

## Loop does not stop or stops immediately

### Symptoms

- Loop reaches `max_iterations` unexpectedly.
- Loop stops after one iteration.
- Loop condition evaluation fails.

### Cause

The first loop iteration always runs. Later iterations continue only while `condition` evaluates true. Template path, quoting, or output shape errors can make the condition false or invalid.

### Fix

- Keep `max_iterations` low while developing.
- Use a simple boolean condition first:

  ```yaml
  condition: "{{check_status.output.ready}} == false"
  ```

- Confirm the target node actually outputs the referenced field.
- Add a safe `delay` for polling (`2s`, `30s`, `1m`) instead of tight loops.

## Template path errors

### Symptoms

- `Output field ... not found`.
- Condition evaluator says a referenced node has not completed.
- Final output is `null` because a branch was skipped.

### Fix

- Check producer node ids and output field names.
- Add the producer to `depends_on` for any node that reads its output.
- Use `coalesce` for optional/skipped branch outputs.
- Quote string-valued templates in conditions:

  ```yaml
  condition: "'{{classify.output.kind}}' == 'billing'"
  ```

- Leave numeric and boolean templates unquoted:

  ```yaml
  when: "{{score.output.value}} > 10 and {{score.output.ready}} == true"
  ```

See [template-resolution.md](template-resolution.md) for exact template and condition behavior.

## Node schema override silently ignored

### Symptom

A node-level `input_schema` or `output_schema` appears to have no effect.

### Cause

The installed node model uses `input_schema_override` and `output_schema_override` for agent/workflow nodes. Plain `input_schema` and `output_schema` are workflow-level fields or agent app fields, not installed node override fields.

### Fix

```yaml
- id: summarize
  type: agent
  agent_name: Summarizer
  input_schema_override:
    type: object
    properties:
      analysis: {type: object}
  output_schema_override:
    type: object
    properties:
      summary: {type: string}
```

## Timeout format problems

### Symptoms

- Invalid duration warning.
- Node timeout falls back to `default_node_timeout_seconds`.

### Cause

Per-node `timeout` and loop `delay` parse duration strings. Supported units are seconds, minutes, hours, and days.

### Fix

Use one of:

- `30s`
- `5m`
- `1h`
- `1d`
- `300` or `"300"` for seconds

App-level timeouts (`max_workflow_execution_time_seconds`, `default_node_timeout_seconds`, `node_cancellation_timeout_seconds`) are numeric seconds.

## Workflow nesting errors

### Symptoms

- Direct recursion detected.
- Nested workflow call cannot resolve target at live runtime.

### Cause

A workflow node cannot directly invoke the same workflow name. Dry validation can catch direct self-recursion but cannot prove live registry availability for another workflow.

### Fix

- Ensure `workflow_name` differs from current `app_config.name`.
- Add `max_call_depth`/`maxCallDepth` to bound nested chains.
- Route live discovery/runtime checks to `runtime-operations`; do not start services from this sub-skill.

## Multiple dependencies but no explicit input

### Symptom

Runtime complains that a node has multiple dependencies but no explicit `input` mapping.

### Cause

The runtime can infer simple dependency input in limited cases, but multiple dependencies are ambiguous.

### Fix

Always author explicit input for join nodes:

```yaml
- id: combine
  type: agent
  agent_name: Combiner
  depends_on: [left_branch, right_branch]
  input:
    left: "{{left_branch.output}}"
    right: "{{right_branch.output}}"
```

## Unknown live agent or workflow target

### Symptom

Dry validation passes, but live execution cannot find `agent_name` or `workflow_name`.

### Cause

Schema validation does not query the live agent registry.

### Fix

- Keep names exact and case-sensitive.
- In a project, make sure the target agent/workflow apps are included in the app file or running/discoverable.
- Route live registry/gateway/broker diagnosis to `runtime-operations`.

## Safe hard cases to test during review

These are useful synthetic usability cases for this sub-skill:

1. A switch/map workflow where one switch branch target lacks `depends_on: [route]`, a map references a missing target, and final `output_mapping` must use `coalesce` for skipped branches.
2. A nested workflow config where a workflow node calls the parent workflow name, one node has `input_schema` instead of `input_schema_override`, and a string condition lacks quotes around a template.
