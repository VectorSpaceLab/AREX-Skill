---
name: workflow-authoring
description: "Author, inspect, validate, and troubleshoot Solace Agent Mesh
  workflow YAML/configs without starting live services."
disable-model-invocation: true
metadata:
  disco-role: operating
  repo: solace-agent-mesh
  package: solace-agent-mesh
license: Apache 2.0
---

# Workflow authoring

Use this sub-skill when the task is to author, inspect, dry-validate, or troubleshoot a Solace Agent Mesh (SAM) workflow configuration that uses `app_module: solace_agent_mesh.workflow.app` and an `app_config.workflow` DAG.

Do **not** use this sub-skill for:

- Creating a SAM project scaffold or generated app layout; route to `project-bootstrap`.
- Starting brokers, gateways, agents, or workflow executions; route to `runtime-operations`.
- Authoring or running `sam eval` suites; route to `evaluation`.

## Fast path

1. Locate the workflow app config:
   - Full SAM app files normally place workflows under `apps[]` with `app_module: solace_agent_mesh.workflow.app`.
   - The model-validated payload is the nested `app_config` object.
2. Check fields and examples in [references/workflow-schema.md](references/workflow-schema.md).
3. Check data/template behavior in [references/template-resolution.md](references/template-resolution.md).
4. Run the bundled dry validator before any live run:

   ```bash
   python sub-skills/workflow-authoring/scripts/validate_workflow_config.py path/to/workflow.yaml
   ```

   Add `--json` for machine-readable output, `--app WorkflowName` to select one workflow app in a multi-app file, or `--self-test` to exercise the validator on an embedded tiny fixture.
5. If validation fails or behavior is confusing, use [references/troubleshooting.md](references/troubleshooting.md) to map the symptom to a concrete config fix.

## Safety boundaries

- The validator and guidance here only parse YAML and validate package/static schema. They must not start brokers, LLM providers, gateways, tasks, or workflow execution.
- Keep actual runtime service checks, `sam run`, task submission, REST gateway checks, and UI verification outside this sub-skill.
- SAM workflows are experimental; when source examples and installed package validation disagree, prefer the installed package schema and document the mismatch.

## Minimal authoring checklist

- `app_config.name` is present; it becomes the workflow agent identity.
- `app_config.namespace` is present for A2A topics.
- `workflow.description`, `workflow.nodes`, and `workflow.output_mapping` are present.
- Every node has a unique `id` and one of the supported `type` values: `agent`, `workflow`, `switch`, `map`, or `loop`.
- Every `depends_on`/`dependencies`, switch branch, map target, loop target, and exit handler points to an existing node.
- Switch branch target nodes list the switch node in `depends_on`; otherwise branch handlers can run too early.
- Map nodes set exactly one item source: `items`, `withParam`, or `withItems`.
- Agent/workflow node timeouts use duration strings like `30s`, `5m`, `1h`, `1d`, or numeric seconds.
- Template paths used in `input`, `instruction`, conditions, and `output_mapping` match the producing node outputs.

## Provenance distilled

This sub-skill was distilled from SAM workflow documentation, example workflow YAML files, workflow implementation modules, workflow unit tests for Pydantic models, DAG logic, template resolution, safe conditional evaluation, and map/loop workflow target behavior. The runtime files are self-contained and do not require opening those source files.
