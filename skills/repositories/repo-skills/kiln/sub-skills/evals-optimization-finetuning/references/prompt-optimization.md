# Prompt Optimization Jobs

Use this reference when starting, checking, listing, or materializing Kiln prompt optimization jobs. Prompt optimization is a Kiln Copilot/cloud workflow: it packages project evidence, sends it to a remote Kiln server, tracks the job locally, and creates a new prompt plus run config when the job succeeds.

For provider/model/run-config primitives, route to task-execution-providers-tools. For base task/project persistence and package-project details, route to project-datamodel.

## Datamodel: `PromptOptimizationJob`

Fields:

- `name`: local display name.
- `description`: optional human description.
- `job_id`: remote Kiln server job ID.
- `target_run_config_id`: run config that the optimizer is improving.
- `latest_status`: cached status; defaults to `pending` and is not live-updated automatically.
- `optimized_prompt`: optimized prompt text after success.
- `created_prompt_id`: local prompt ID created from the result, stored with an `id::` prefix.
- `created_run_config_id`: local task run config ID created from the optimized prompt.
- `eval_ids`: evals used for the optimization job.

A job is a child of `Task`. Use the parent task to resolve the parent project and target run config.

## Readiness checks

### Check target run config

`GET /api/projects/{project_id}/tasks/{task_id}/prompt_optimization_jobs/check_run_config?run_config_id={id}`

Returns:

```json
{ "is_supported": true }
```

A run config is unsupported when:

- it is not a `KilnAgentRunConfigProperties` config,
- it uses tools,
- model name/provider are missing,
- the remote prompt optimization service reports the model unsupported,
- Copilot authentication cannot be established.

Prompt optimization intentionally excludes tool-enabled run configs.

### Check eval

`GET /api/projects/{project_id}/tasks/{task_id}/prompt_optimization_jobs/check_eval?eval_id={id}`

Returns:

```json
{
  "has_default_config": true,
  "has_train_set": true,
  "model_is_supported": true
}
```

A usable eval needs:

- `current_config_id` set to a loadable eval config,
- `train_set_filter_id` present,
- default judge config model supported by the remote optimization service.

If `current_config_id` is missing or stale, `has_default_config` is false. If the default config has missing model/provider values or an unsupported model, `model_is_supported` is false.

## Starting a job

Endpoint:

`POST /api/projects/{project_id}/tasks/{task_id}/prompt_optimization_jobs/start`

Request:

```json
{
  "target_run_config_id": "run_config_id",
  "eval_ids": ["eval_id_1", "eval_id_2"]
}
```

The endpoint requires approval because it can use many credits.

Start behavior:

1. Resolve task and parent project.
2. Resolve the target run config.
3. Reject non-Kiln-agent run configs.
4. Reject run configs with tools.
5. Authenticate to the Kiln Copilot server.
6. Package the project for training with:
   - one task ID,
   - the target run config ID,
   - selected eval IDs,
   - documents excluded,
   - task runs included,
   - eval config runs excluded.
7. Upload the package to the remote prompt optimization endpoint.
8. Save a local `PromptOptimizationJob` with generated local name, remote job ID, target run config ID, pending status, eval IDs, and task parent.

Upload/read errors are surfaced as connection/project-size/server-unreachable messages when possible.

## Listing and status updates

### List local jobs

`GET /api/projects/{project_id}/tasks/{task_id}/prompt_optimization_jobs?update_status=false`

Returns all local jobs for the task. When `update_status=true`, the endpoint tries to refresh non-final jobs from the remote server in batches of five. Individual refresh errors are logged and swallowed so one bad job does not block the list response.

Final statuses are:

- `succeeded`
- `failed`
- `cancelled`

Final jobs are not refreshed.

### Get one local job

`GET /api/projects/{project_id}/tasks/{task_id}/prompt_optimization_jobs/{prompt_optimization_job_id}`

Returns the local job. If it is not final, the endpoint tries to refresh status and create artifacts on a new success transition.

### Public remote status

`GET /api/prompt_optimization_jobs/{job_id}/status`

Returns only:

```json
{
  "job_id": "remote_job_id",
  "status": "running"
}
```

Use this for remote status by remote job ID when local task/project context is not needed.

### Public remote result

`GET /api/prompt_optimization_jobs/{job_id}/result`

Returns only:

```json
{ "optimized_prompt": "..." }
```

If the remote job completed without an optimized prompt in the result payload, the endpoint returns an error.

## Success artifact creation

When a job's status transitions to succeeded, Kiln creates local artifacts under a per-job async lock.

### Locking and idempotence

`update_prompt_optimization_job_and_create_artifacts` acquires a shared async lock keyed by remote `job_id`. After acquiring it, it reloads the local job and checks whether `created_prompt_id` is already set. This prevents duplicate prompt/run-config artifacts when multiple status requests race.

### Prompt artifact

`create_prompt_from_optimization(job, task, optimized_prompt_text)` creates a `Prompt` with:

- `name`: job name,
- `generator_id`: `kiln_prompt_optimizer`,
- `prompt`: optimized prompt text,
- parent task.

The job records `created_prompt_id` as `id::{prompt.id}`.

### Run config artifact

`create_run_config_from_optimization(job, task, prompt)`:

1. Resolves the parent project.
2. Loads the original target run config.
3. Copies its run config properties.
4. Requires the copied properties to be `KilnAgentRunConfigProperties`.
5. Sets `prompt_id` to the new prompt ID with `id::` prefix.
6. Creates and saves a new `TaskRunConfig` with a generated memorable name.
7. Records the new run config ID on the job.

If prompt or run-config creation fails after partially creating an artifact, cleanup attempts to delete the partial artifact and clears the job's created artifact fields so a future status call can retry.

## Interaction with evals

Prompt optimization depends on evals in two ways:

- The selected eval IDs are packaged as optimization objectives.
- Each eval should have a default judge config (`current_config_id`) and a training-set filter (`train_set_filter_id`) for readiness checks.

Recommended preparation:

1. Build or choose evals with stable output score keys.
2. Run or calibrate judge configs if human-rated data exists.
3. Set `current_config_id` on each chosen eval.
4. Ensure `train_set_filter_id` selects suitable training examples.
5. Confirm target run config does not use tools.
6. Call readiness checks before starting the expensive job.

## Provider-account boundaries

Prompt optimization is optional and cloud-backed. It requires a configured Kiln Copilot API key. Treat missing Copilot credentials as a service readiness issue, not as a failure of local eval or fine-tune datamodels.

Do not start jobs silently. The route requires approval because it uploads a project package and uses credits.

Do not assume local provider credentials are enough. Prompt optimization checks model support against the remote Kiln service and may reject a locally runnable model.

## Safe operating pattern

1. Read target task and candidate run config.
2. Verify the run config is a Kiln-agent config and has no tools.
3. Read candidate evals and confirm each has a default judge config and train filter.
4. Run `check_run_config` and `check_eval` for every dependency.
5. Ask for approval before `start` because it uses remote credits and uploads packaged project data.
6. After start, track the local `PromptOptimizationJob` ID and remote `job_id`.
7. Poll with `update_status=true` or get the job directly.
8. On success, use `created_prompt_id` and `created_run_config_id` instead of creating duplicate artifacts manually.
9. Evaluate the created run config with normal eval comparison before promoting it.

## Common mistakes

- Starting with a tool-enabled target run config. The API rejects this because prompt optimization does not support tools.
- Forgetting `current_config_id` on evals. Readiness returns `has_default_config=false`.
- Forgetting `train_set_filter_id`. Readiness returns `has_train_set=false`.
- Treating `latest_status` as live. It is cached and refreshed only by status/list calls that contact the remote service.
- Creating prompt/run-config artifacts manually after success. Let the success transition create them under lock.
- Assuming success artifacts are created if the remote result lacks `optimized_prompt`; the API reports an error instead.

## Evidence notes

Source evidence: `libs/core/kiln_ai/datamodel/prompt_optimization_job.py`, `app/desktop/studio_server/prompt_optimization_job_api.py`, `app/desktop/studio_server/eval_api.py`, `kiln_ai.cli.commands.package_project`, and prompt optimization API tests.
