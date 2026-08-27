# SAM workflow schema and authoring patterns

This reference is a self-contained operating guide for authoring SAM workflow app configs. It describes the installed `solace-agent-mesh` workflow model rather than requiring original repo docs or examples.

## Where workflow config lives

A workflow is a SAM app whose `app_module` is `solace_agent_mesh.workflow.app`. The workflow model validates the nested `app_config` object.

```yaml
apps:
  - name: support_router_workflow_app
    app_module: solace_agent_mesh.workflow.app
    app_config:
      namespace: ${NAMESPACE}
      name: SupportRouterWorkflow
      agent_discovery: {enabled: false}
      agent_card_publishing: {interval_seconds: 10}
      max_workflow_execution_time_seconds: 1800
      default_node_timeout_seconds: 300
      node_cancellation_timeout_seconds: 30
      default_max_map_items: 100
      workflow:
        description: Route and process support requests
        version: "1.0.0"
        input_schema:
          type: object
          properties:
            request: {type: string}
          required: [request]
        nodes:
          - id: classify
            type: agent
            agent_name: RequestClassifier
            input:
              request: "{{workflow.input.request}}"
          - id: handle
            type: agent
            agent_name: GeneralHandler
            depends_on: [classify]
            input:
              request: "{{workflow.input.request}}"
              classification: "{{classify.output}}"
        output_mapping:
          response: "{{handle.output.response}}"
```

Only the workflow app config is dry-validated here. Project files, broker settings, model providers, service definitions, and live execution belong to other sub-skills.

## App-level workflow fields

These fields sit directly under `app_config`.

| Field | Required | Default | Notes |
| --- | --- | --- | --- |
| `namespace` | Yes | none | Topic prefix used by SAM A2A messages. The dry validator only checks presence/type. |
| `name` | Yes | none | Workflow identity. The model also populates inherited `agent_name` from this value. |
| `workflow` | Yes | none | Workflow DAG definition. |
| `max_workflow_execution_time_seconds` | No | `1800` | Total workflow timeout. Numeric seconds. |
| `default_node_timeout_seconds` | No | `300` | Default per-node call timeout when a node has no `timeout`. Numeric seconds. |
| `node_cancellation_timeout_seconds` | No | `30` | Wait for cancellation acknowledgement before force-failing. |
| `default_max_map_items` | No | `100` | Safety cap used when a map node omits `max_items`/`maxItems`. |
| `agent_card` | No | generated/default | Static discovery card settings; workflow schemas are also exposed in the workflow card. |
| `agent_card_publishing` | No | interval `10` | Periodic discovery-card publishing settings. |
| inherited agent fields | No | model defaults | Workflow config inherits many agent config fields such as services and discovery. They are not a reason to start live services during validation. |

## Workflow definition fields

These fields sit under `app_config.workflow`.

| Field | Required | Default | Notes |
| --- | --- | --- | --- |
| `description` | Yes | none | Human-readable workflow purpose. |
| `version` | No | `1.0.0` | User-facing workflow version. |
| `input_schema` / `inputSchema` | No | none | JSON Schema for workflow input. |
| `output_schema` / `outputSchema` | No | none | JSON Schema for final workflow output. |
| `nodes` | Yes | none | Ordered list of DAG/control nodes. Node order is not execution order; dependencies control scheduling. |
| `output_mapping` / `outputMapping` | Yes | none | Mapping from workflow/node data to final output. |
| `skills` | No | none | Skills advertised in the workflow agent card. |
| `on_exit` / `onExit` | No | none | String node id, or object with `always`, `on_success`/`onSuccess`, `on_failure`/`onFailure`, `on_cancel`/`onCancel`. |
| `fail_fast` / `failFast` | No | `true` | Stop scheduling new nodes after a failure while already-running nodes finish. |
| `max_call_depth` / `maxCallDepth` | No | `10` | Recursion safety for workflow/agent call depth; must be at least `1`. |
| `retry_strategy` / `retryStrategy` | No | none | Default retry strategy for nodes, overridable per agent/workflow node. |

## Common node fields

All nodes share these fields.

| Field | Required | Notes |
| --- | --- | --- |
| `id` | Yes | Unique node identifier. Use simple stable ids (`classify`, `process_items`) because template paths depend on them. |
| `type` | Yes | One of `agent`, `workflow`, `switch`, `map`, `loop`. |
| `depends_on` / `dependencies` | No | List of node ids that must complete before this node can be scheduled. |

Rules:

- Node ids must be unique.
- Dependency references must name existing nodes.
- Dependency cycles are invalid.
- Nodes with no dependencies run as initial nodes, except map/loop target nodes, which are executed by their control node.
- When multiple nodes are ready at the same time, SAM treats them as implicit parallel branches.
- A node that depends on multiple previous nodes should usually provide explicit `input`; otherwise the runtime may not know how to merge dependency outputs.

## `agent` node

Invokes another SAM agent by name.

```yaml
- id: summarize
  type: agent
  agent_name: Summarizer
  depends_on: [analyze]
  input:
    analysis: "{{analyze.output}}"
    audience: "{{workflow.input.audience}}"
  instruction: "Keep the summary suitable for {{workflow.input.audience}}."
  timeout: 10m
  retryStrategy:
    limit: 2
    retryPolicy: OnFailure
    backoff:
      duration: 2s
      factor: 2.0
      maxDuration: 30s
```

| Field | Required | Notes |
| --- | --- | --- |
| `agent_name` | Yes | Target agent card name. Discovery/live availability is not checked by dry validation. |
| `input` | No | Mapping sent to the agent. Supports templates and operators from [template-resolution.md](template-resolution.md). |
| `instruction` | No | Extra instruction string; templates are allowed. |
| `when` | No | Conditional execution expression. False means the node is marked skipped. |
| `input_schema_override` | No | JSON Schema override for this workflow call. Prefer this exact field name. |
| `output_schema_override` | No | JSON Schema override for validating/handling the agent result. Prefer this exact field name. |
| `timeout` | No | Per-node override such as `30s`, `5m`, `1h`, or numeric seconds. |
| `retry_strategy` / `retryStrategy` | No | Per-node retry policy. |

Pitfall: workflow-level `input_schema`/`output_schema` are valid under `workflow`. For node-level overrides, use `input_schema_override` and `output_schema_override`; a plain `input_schema` field on an agent node may be ignored by the installed model.

## `workflow` node

Invokes another workflow. Workflows register as agents, but the node schema uses `workflow_name` instead of `agent_name`.

```yaml
- id: run_validation
  type: workflow
  workflow_name: ValidationWorkflow
  depends_on: [prepare]
  input:
    payload: "{{prepare.output.cleaned_payload}}"
  timeout: 15m
```

| Field | Required | Notes |
| --- | --- | --- |
| `workflow_name` | Yes | Target workflow identity. |
| `input`, `instruction`, `when`, `timeout`, `retryStrategy` | No | Same semantics as `agent` node. |
| `input_schema_override`, `output_schema_override` | No | Same override fields as agent nodes. |

Rules:

- Direct self-recursion is invalid at runtime: a workflow node must not call the same `app_config.name`.
- `max_call_depth` limits deeper nesting.
- Map and loop target nodes can be either `agent` or `workflow` nodes.

## `switch` node

Routes to one selected branch. Cases are evaluated in order; the first true case wins. If no case matches, `default` is used when present.

```yaml
- id: route_priority
  type: switch
  depends_on: [classify]
  cases:
    - condition: "'{{classify.output.priority}}' == 'critical'"
      node: escalate
    - when: "'{{classify.output.priority}}' == 'normal'"
      then: handle_normal
  default: handle_other

- id: escalate
  type: agent
  agent_name: EscalationAgent
  depends_on: [route_priority]
  input:
    request: "{{workflow.input.request}}"

- id: handle_normal
  type: agent
  agent_name: NormalHandler
  depends_on: [route_priority]
  input:
    request: "{{workflow.input.request}}"

- id: handle_other
  type: agent
  agent_name: GeneralHandler
  depends_on: [route_priority]
  input:
    request: "{{workflow.input.request}}"
```

| Field | Required | Notes |
| --- | --- | --- |
| `cases` | Yes | List of case objects. |
| `cases[].condition` / `cases[].when` | Yes | Safe condition expression. |
| `cases[].node` / `cases[].then` | Yes | Branch target node id. |
| `default` | No | Branch target when no case matches. |

Critical branch rule: every switch target (`cases[].node` and `default`) must exist and must list the switch id in `depends_on`. Without that dependency, the target can be scheduled before the switch chooses it.

Switch node output contains the selected branch metadata, typically as `{{route_priority.output.selected_branch}}` and `{{route_priority.output.selected_case_index}}`.

## `map` node

Runs a target node once for each item and aggregates ordered results.

```yaml
- id: process_all_items
  type: map
  depends_on: [load_items]
  items: "{{load_items.output.items}}"
  node: process_one_item
  concurrency_limit: 4
  max_items: 50

- id: process_one_item
  type: agent
  agent_name: ItemProcessor
  input:
    item_id: "{{_map_item.id}}"
    value: "{{_map_item.value}}"
    index: "{{_map_index}}"
```

| Field | Required | Notes |
| --- | --- | --- |
| exactly one of `items`, `withParam`, `withItems` | Yes | Dynamic template, Argo-style JSON array expression, or static list. |
| `node` | Yes | Target node id to execute for each item. |
| `concurrency_limit` / `concurrencyLimit` | No | Maximum concurrent iterations; omitted means unlimited. |
| `max_items` / `maxItems` | No | Per-map cap; default comes from `default_max_map_items`. |

Rules:

- The target node must exist.
- The target node is treated as an inner node and is not scheduled as a normal initial node.
- The target may be an `agent` or `workflow` node.
- Use `{{_map_item}}`, `{{_map_item.field}}`, `{{_map_index}}`, or Argo aliases `{{item}}`/`{{item.field}}` in target input mappings.
- Map output is available as `{{process_all_items.output.results}}`.

## `loop` node

Runs a target node repeatedly. The first iteration always runs; after that, `condition` is evaluated before each next iteration. The loop stops when the condition becomes false or `max_iterations` is reached.

```yaml
- id: poll_until_ready
  type: loop
  node: check_status
  condition: "{{check_status.output.ready}} == false"
  max_iterations: 10
  delay: 5s

- id: check_status
  type: agent
  agent_name: StatusChecker
  input:
    task_id: "{{workflow.input.task_id}}"
    iteration: "{{_loop_iteration}}"
```

| Field | Required | Notes |
| --- | --- | --- |
| `node` | Yes | Target node id. The target may be an `agent` or `workflow` node. |
| `condition` | Yes | Continue while this expression is true. |
| `max_iterations` / `maxIterations` | No | Safety cap, default `100`. |
| `delay` | No | Duration between iterations after the first iteration. |

Loop output includes `iterations_completed` and `stopped_reason` (`condition_false` or `max_iterations`).

## Exit handlers and failure behavior

Exit handlers are ordinary nodes referenced from `on_exit`/`onExit`.

```yaml
workflow:
  description: Example with cleanup
  failFast: true
  onExit:
    always: log_completion
    onFailure: send_alert
  nodes:
    - id: work
      type: agent
      agent_name: Worker
    - id: log_completion
      type: agent
      agent_name: AuditLogger
      input:
        status: "{{workflow.status}}"
    - id: send_alert
      type: agent
      agent_name: AlertAgent
      input:
        error: "{{workflow.error}}"
  outputMapping:
    result: "{{work.output}}"
```

Validation rules:

- Referenced exit handler ids must exist.
- `fail_fast: true` stops scheduling new nodes after failure; it does not cancel already-running nodes by itself.
- Exit-handler templates may reference workflow-level status/error/output context at runtime.

## Retry strategy fields

Retry strategy can be set at workflow level or per agent/workflow node.

```yaml
retryStrategy:
  limit: 3
  retryPolicy: OnFailure
  backoff:
    duration: 1s
    factor: 2.0
    maxDuration: 30s
```

Allowed `retryPolicy` values: `Always`, `OnFailure`, `OnError`.

## Representative complete patterns

### Sequential pipeline

```yaml
app_config:
  namespace: ${NAMESPACE}
  name: SequentialWorkflow
  workflow:
    description: Analyze text then summarize it
    nodes:
      - id: analyze
        type: agent
        agent_name: TextAnalyzer
        input:
          content: "{{workflow.input.text}}"
      - id: summarize
        type: agent
        agent_name: Summarizer
        depends_on: [analyze]
        input:
          analysis: "{{analyze.output}}"
    output_mapping:
      summary: "{{summarize.output.summary}}"
```

### Parallel fork and join

```yaml
app_config:
  namespace: ${NAMESPACE}
  name: ParallelWorkflow
  workflow:
    description: Run independent enrichers, then combine
    nodes:
      - id: enrich_customer
        type: agent
        agent_name: CustomerEnricher
        input: {order: "{{workflow.input.order}}"}
      - id: check_inventory
        type: agent
        agent_name: InventoryChecker
        input: {order: "{{workflow.input.order}}"}
      - id: combine
        type: agent
        agent_name: Combiner
        depends_on: [enrich_customer, check_inventory]
        input:
          customer: "{{enrich_customer.output}}"
          inventory: "{{check_inventory.output}}"
    output_mapping:
      combined: "{{combine.output}}"
```

### Branch output coalescing

```yaml
app_config:
  namespace: ${NAMESPACE}
  name: BranchWorkflow
  workflow:
    description: Route by classification and return selected branch output
    nodes:
      - id: classify
        type: agent
        agent_name: Classifier
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
    output_mapping:
      answer:
        coalesce:
          - "{{billing.output.answer}}"
          - "{{general.output.answer}}"
```

## Dry validation

Use [../scripts/validate_workflow_config.py](../scripts/validate_workflow_config.py) for package-backed and static validation. It is intentionally safe: it imports schema models when available and checks YAML/DAG/template structure; it does not start broker, agent, gateway, or LLM services.
