# API Workflow Automation

Use this reference when an agent must import, invoke, poll, or troubleshoot Galaxy workflows through the HTTP API. For authoring Galaxy workflow YAML or tool XML, route to `../workflows-and-tools/SKILL.md`; this page focuses on API automation around already-defined artifacts.

## Workflow Import Options

Galaxy workflow creation/import routes accept several mutually exclusive creation modes. The source route validates that exactly one creation source is present.

Common modes:

- `workflow`: inline workflow object, often for serialized workflow definitions.
- `from_path`: server-side path import; this is usually admin-only or deployment-sensitive and should not be used for ordinary external automation.
- `archive_file` or `archive_source`: import from a workflow archive file or allowed URI.
- `from_history_id`: extract a workflow from an existing history and selected jobs/datasets.
- `shared_workflow_id`: import from an existing shared workflow.

Legacy example scripts used `POST /api/workflows` with payloads such as:

```json
{
  "installed_repository_file": "workflow.ga",
  "add_to_menu": true
}
```

Modern route schemas are stricter and may require a different field set. Confirm with OpenAPI or API tests for the target Galaxy version before executing writes.

## Workflow Invocation Shape

Current Galaxy route code schedules a stored workflow with `POST /api/workflows/{workflow_id}/invocations`. The workflow ID is part of the URL, while the JSON body describes the target history and inputs:

```json
{
  "history": "hist_id=encoded-history-id",
  "inputs": {
    "input1": {"src": "hda", "id": "encoded-dataset-id"}
  },
  "inputs_by": "name"
}
```

The schema also accepts legacy fields used by older scripts and tests:

```json
{
  "history": "History name or hist_id=encoded-history-id",
  "ds_map": {
    "0": {"src": "hda", "id": "encoded-dataset-id"},
    "1": {"src": "ldda", "id": "encoded-library-dataset-id"}
  }
}
```

Stable invocation concepts:

- The workflow ID identifies the stored workflow in the route path.
- The invocation needs an output history target, either by ID, an existing name, or a request to create/use a named history.
- Prefer `inputs` with `inputs_by` set to `name`, `step_id`, `step_index`, or `step_uuid` when the workflow exposes formal inputs.
- Use legacy `ds_map` only when matching older helper/script behavior or tests that intentionally cover legacy input mapping.
- Dataset-like values include a source discriminator such as `hda`, `hdca`, or `ldda` plus an encoded ID.
- Submit responses describe the invocation and/or jobs; they do not guarantee outputs are complete.

## Dry-Run Plan for Import and Invoke

When asked to automate a workflow safely, produce a dry-run plan before executing:

1. Confirm target Galaxy base URL and whether it is local, staging, or production.
2. Confirm the API key user with `GET /api/whoami` if execution is authorized.
3. Validate the workflow artifact format with the workflow/tool sub-skill before using the API.
4. Create or select a disposable output history.
5. Import the workflow using the allowed source mode for that deployment.
6. Resolve workflow input labels or step IDs from the stored workflow detail endpoint.
7. Resolve dataset/collection IDs in the target history.
8. Build an invocation payload with explicit input mappings.
9. Submit the invocation only after user-confirmed execution.
10. Poll invocation, jobs, and output datasets until terminal state.
11. Summarize created IDs with keys redacted.

The bundled `scripts/galaxy_api_smoke.py` can generate this dry-run plan without contacting a server.

## Polling and Async States

Workflow execution is asynchronous. A reliable automation loop should:

- Store the invocation ID returned by submission.
- Poll the invocation endpoint for state and step details when available.
- Poll jobs for terminal `ok`, `error`, `deleted`, or cancellation-like states.
- Poll output datasets or collections until all expected outputs are terminal.
- Use a bounded timeout and sleep interval.
- Report partial progress without printing secrets.

Pseudo-flow:

```text
submit invocation
while timeout not exceeded:
  read invocation summary
  if invocation failed/cancelled: stop with diagnostic
  read jobs and outputs
  if all expected outputs ok: success
  if any required output error: stop with failing job/output IDs
  sleep
```

## API Test Helpers for Workflows

For repository changes, prefer Galaxy's API test helpers over standalone scripts:

- `WorkflowPopulator.upload_yaml_workflow(...)` creates workflows from Galaxy Format2 YAML fixtures.
- `WorkflowPopulator.simple_workflow(...)` is useful for minimal workflow fixtures.
- `WorkflowPopulator.import_workflow_from_path_raw(...)` returns a raw response for status/error assertions.
- `WorkflowPopulator.run_workflow(...)` and related helpers invoke workflows with test datasets.
- `WorkflowPopulator.wait_for_invocation(...)`, `wait_for_invocation_and_jobs(...)`, and `wait_for_invocation_and_completion(...)` encode Galaxy's async polling expectations.
- Pair workflows with `DatasetPopulator` to create histories and test datasets.

Use raw responses for negative tests, for example checking `403` plus `ADMIN_REQUIRED` on an import path that needs admin privileges.

## Admin and Run-As Caveats

- Server-side path imports and administrative routes may require an admin key.
- `run-as` is an admin-authenticated request header used in tests/admin contexts to act as another user.
- A non-admin user should use user-owned workflow imports, published/shared workflow access, or workflow uploads allowed by the deployment instead of trying to decode IDs or access server paths.
- If a workflow needs private tools, libraries, or histories, check sharing and role permissions before blaming the invocation payload.

## Troubleshooting Workflow API Failures

- `400` on import: usually missing exactly-one source field, invalid archive, unsupported workflow schema, missing tools, or a request body that does not match the current API schema.
- `400` on invocation: often wrong input step keys, missing runtime inputs, invalid dataset source discriminator, or dataset IDs not visible in the chosen history.
- `403 ADMIN_REQUIRED`: route needs admin privileges; switch key/endpoint/source mode.
- `404`: stored workflow, history, or dataset is not visible to the current user, or the base URL/route is wrong.
- Stuck invocation: inspect jobs and outputs; a workflow invocation can wait on queued jobs, paused steps, failed jobs, or dataset collection mapping.
- Missing outputs: verify the workflow's output declarations and step IDs, not just the submit response.
