# Troubleshooting

## Common symptoms and likely causes

### DAG does not render or run

- malformed DAG JSON
- missing upstream task names
- task names that do not match a registered `Task`
- Jinja variables that fail to render at pipeline build time
- skipped nodes that never receive the intended `when` condition

### Template registration fails

- args JSON does not match the documented group/field shape
- a field uses an unsupported `type`
- required `choice`, `label`, or `require` data is missing
- `resource_cpu`, `resource_memory`, or `resource_gpu` values fail the form validators
- the template image or repository entry is missing

### Argo submission fails

- CRDs are not installed yet
- image pull secrets or hubsecret configuration is wrong
- service account or namespace settings do not match the cluster setup
- `parallelism` or task-level resource settings conflict with the desired schedule

### Runtime task fails

- launcher expects files that were not mounted
- the task writes metrics/output to a path that the UI cannot read back
- `working_dir` or `volume_mount` is wrong
- command-line flags were not rendered from the args JSON as expected

### Run history or monitoring looks wrong

- workflow exists but the corresponding run history row was not updated
- the task completed but no metrics payload was written
- the pipeline is submitting with an unexpected image or environment

## Concrete recovery checks

1. Validate the args payload with the bundled helper before registering a new template.
2. Confirm the template family README and launcher agree on the same field names.
3. Check that the job image and repository entry exist before blaming the pipeline DAG.
4. Inspect the pipeline/task resources and node selector before assuming a cluster issue.
5. If the workflow fails after scheduling, compare the task's expected output path with the artifact mount used by the template.

## What not to do

- Do not use a template launcher or build script as a generic validation helper.
- Do not treat a passing CLI help check as proof that the Argo or cluster submission path is healthy.
- Do not run live image builds or pipeline submissions during skill drafting.

## Helpful cross-links

- `job-template-catalog.md` for the field schema and built-in template families
- `argo-and-resource-contract.md` for environment variables and runtime resource semantics
- `pipeline-workflows.md` for the task → pipeline → workflow flow
