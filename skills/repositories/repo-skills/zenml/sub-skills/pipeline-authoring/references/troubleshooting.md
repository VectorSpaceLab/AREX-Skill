# Pipeline Authoring Troubleshooting

Use this guide when ZenML pipeline code imports, compiles, or runs incorrectly. Start with the closest symptom, then run the safe bundled scripts from this sub-skill when practical.

## Fast Triage

1. Run `python scripts/inspect_pipeline_api.py --check-imports` to confirm the active environment can import core ZenML APIs.
2. Run `python scripts/inspect_pipeline_api.py --json` when decorator or settings arguments may have changed.
3. Run `python scripts/pipeline_smoke.py --check-imports` before any local execution.
4. Run `python scripts/pipeline_smoke.py --run` only when a temporary local ZenML repository and local store are acceptable.
5. Disable cache for one validation run if hooks, retries, or step bodies appear not to execute.
6. For remote, Docker, schedule, step-operator, or stack-component failures, route infrastructure setup to `../stacks-and-integrations/SKILL.md` after confirming the pipeline code is valid.

## Import or Optional Extra Missing

Symptoms:

- `ModuleNotFoundError` for an integration SDK, materializer dependency, Docker backend, local server dependency, or experiment tracker.
- Code works locally but fails in a remote or Docker orchestrator.
- A custom materializer cannot import its associated data type in the step container.

Likely causes:

- Base `zenml` is installed but the optional extra or integration package is not.
- The active Docker image omits a package that exists in the author's local environment.
- `DockerSettings.required_integrations` or `DockerSettings.requirements` is missing or too broad.

Recovery:

- Install only the narrow extra or dependency needed for the workflow, such as local/server capabilities or a specific integration, instead of broad development extras.
- Add remote-container dependencies with `DockerSettings(required_integrations=[...])` or `DockerSettings(requirements=[...])`.
- Keep optional SDK imports inside steps, materializers, or integration-specific code paths when possible; do not make base pipeline imports require optional cloud SDKs.
- Run `inspect_pipeline_api.py --check-imports` after changing the environment.

## Invalid Materializer Keys

Symptoms:

- ZenML rejects `output_materializers`.
- A materializer is ignored or applied to the wrong output.
- A multi-output step returns tuple values but configuration uses `"output"`.

Likely causes:

- Mapping keys do not match the actual output names.
- Multi-output names defaulted to `output_0`, `output_1`, etc. because `Annotated` names were omitted.
- A single tuple output was confused with multiple outputs.

Recovery:

- Add explicit output names with `typing.Annotated` before assigning materializers.
- For a step returning `tuple[Annotated[A, "left"], Annotated[B, "right"]]`, use `output_materializers={"left": LeftMaterializer, "right": RightMaterializer}`.
- If the intended output is one tuple artifact, annotate the tuple as a single return value and use one materializer.
- Run a tiny local smoke after changing output names because downstream unpacking may also need updates.

## Custom Materializer Definition Fails

Symptoms:

- Class creation raises a materializer interface error.
- Artifact saves locally but fails on remote artifact stores.
- Dynamic mapping over a custom sequence artifact fails.

Likely causes:

- `ASSOCIATED_TYPES` is empty or contains a non-class object.
- `ASSOCIATED_ARTIFACT_TYPE` is not a valid artifact type.
- The materializer uses direct filesystem I/O instead of `self.artifact_store.open(...)`.
- `get_item_count(...)` or `load_item(...)` is missing for dynamic item loading.

Recovery:

- Set `ASSOCIATED_TYPES = (MyType,)` and keep `MyType` importable in the execution image.
- Use `self.uri` as the artifact directory and write files through `self.artifact_store.open(...)`.
- Save visualizations under `self.uri` and return valid `VisualizationType` values.
- Add `compute_content_hash(...)` for custom objects whose content should affect caching.
- Add both `get_item_count(...)` and `load_item(...)` before using `.map(...)` or `.chunk(...)` over that custom artifact.

## Cache, Retry, and Hook Confusion

Symptoms:

- A step body does not run.
- `on_start` or `on_success` did not fire.
- Hooks fire more often than expected during retries.
- A failing hook does not fail the run.

Likely causes:

- A cache hit reused prior outputs and skipped the step body plus step-level hooks.
- Retry attempts fire `on_start` and `on_end` per attempt; terminal hooks fire once.
- Hook exceptions are recorded and swallowed by design.
- Static and dynamic pipeline-level hooks have different semantics.

Recovery:

- Temporarily set `@step(enable_cache=False)`, `@pipeline(enable_cache=False)`, or `pipeline.with_options(enable_cache=False)` while validating behavior.
- Use `StepRetryConfig(max_retries=..., delay=..., backoff=...)` and document expected hook counts.
- Test alert/notification hooks directly if notification failure should stop deployment or release logic.
- Remember: static pipeline hooks become step defaults; dynamic pipeline hooks fire once at run scope.
- Query hook invocation records with the client when auditing hook outcomes; CLI/client-heavy audits route to `../cli-and-client/SKILL.md`.

## Dynamic `.load()`, `.chunk()`, `.map()`, and `unmapped(...)` Errors

Symptoms:

- A dynamic pipeline passes concrete Python values where lineage is expected.
- A mapped step complains about sequence lengths or asks for `unmapped(...)`.
- Large artifacts are loaded into the orchestration process and slow or fail the run.
- Downstream reducers receive the wrong object shape.

Likely causes:

- `.load()` was used for wiring instead of decisions.
- `.chunk(index=...)` was omitted after deciding which items to process.
- A list-like artifact should have been broadcast with `unmapped(...)`.
- A mapped multi-output result was not split with `unpack()`.

Recovery:

- Use `.load()` only to inspect a value for Python control flow.
- Use `.chunk(index=...)` to create downstream dependencies on individual collection items.
- Use `step.map(...)` for aligned fan-out and `step.product(...)` for Cartesian fan-out.
- Wrap broadcast inputs with `unmapped(...)`.
- Call `mapped_result.unpack()` before separately consuming outputs from a mapped multi-output step.

## Dynamic Child Pipeline Duplicate Runs

Symptoms:

- Resuming or retrying a parent dynamic run creates duplicate child work.
- Child run keys shift from `pipeline:child` to `pipeline:child_2` or later names unexpectedly.
- A previously completed child pipeline reruns after a source edit.

Likely causes:

- Child pipeline calls or submitted step calls were reordered, inserted, or removed before existing calls.
- The child pipeline's own configuration was expected to apply while using `embed(...)`.
- Dynamic source functions are not importable at module scope, causing source resolution or resume issues.

Recovery:

- Keep child pipeline call order stable across retries and resumes.
- Append new child calls after existing stable calls when compatibility matters.
- Use `child_pipeline(...)` or `child_pipeline.submit(...)` when the child needs its own run and configuration.
- Use `child_pipeline.embed(...)` only when inline execution under the parent configuration is intended.
- Keep dynamic pipeline definitions and custom materializers importable at module scope.
- Before a risky refactor, record existing child call order and expected child keys in the task notes.

## Orchestrator Run ID Stability

Symptoms:

- A custom or modified orchestrator creates multiple ZenML runs for one backend run.
- Downstream steps cannot find the run created by the first step.
- Dynamic retries fail to reconnect to the intended parent/child run.

Likely causes:

- `get_orchestrator_run_id()` returns a different value for different steps in the same pipeline run.
- The ID is not unique across backend runs.
- A dynamic orchestration container uses a retry-unstable pod/container ID instead of a stable parent job ID.

Recovery:

- This is orchestrator implementation work; route code changes to `../stacks-and-integrations/SKILL.md`.
- When authoring pipelines, keep dynamic child call order stable so the orchestrator can reuse existing runs.
- When reviewing orchestrator behavior, require one unique backend run ID per pipeline run and the same value for every step in that run.
- For dynamic containerized orchestrators, prefer a stable parent orchestration job ID over a retry-varying hostname or pod ID.

## Docker Settings Errors

Symptoms:

- Docker build fails, the image lacks dependencies, or remote steps cannot import user modules.
- `skip_build=True` fails before submission.
- A materializer works locally but not remotely.

Likely causes:

- `skip_build=True` was set without `parent_image`.
- Required integrations, materializer dependencies, or local package files are not included in the image.
- The image relies on broad local environment replication instead of explicit requirements.
- A child dynamic pipeline is expected to build a different image, but child runs inherit the parent build/image.

Recovery:

- Set an explicit `parent_image` when using `skip_build=True`.
- Add narrow `requirements=[...]` or `required_integrations=[...]` to `DockerSettings`.
- Keep custom step, pipeline, and materializer modules under the source root copied into the image.
- Avoid relying on `replicate_local_python_environment=True` for reproducible examples.
- For child pipelines, put all child dependencies in the parent pipeline's image or route step-specific remote execution to stack/component settings.

## Resource Settings Errors

Symptoms:

- GPU/CPU/memory requests are ignored.
- Resource validation rejects memory strings.
- Deployed pipeline scaling settings do not behave as expected.

Likely causes:

- The active orchestrator or deployer does not enforce the requested fields.
- `memory` lacks a supported unit or uses a lowercase/unsupported unit.
- Deployment-only fields are used for ordinary step execution.
- Step resource settings override or merge with pipeline settings in a surprising way.

Recovery:

- Use memory strings such as `"512MB"`, `"2GB"`, or `"4GiB"`.
- Keep ordinary step execution fields (`cpu_count`, `gpu_count`, `memory`) separate from deployment scaling fields (`min_replicas`, `max_replicas`, `autoscaling_metric`, `autoscaling_target`, `max_concurrency`).
- Check the active orchestrator/deployer support before promising enforcement.
- Route backend-specific resource support and stack registration to `../stacks-and-integrations/SKILL.md`.

## Schedule Does Not Trigger

Symptoms:

- `pipeline.with_options(schedule=...)()` returns no immediate run or does not trigger later.
- CLI schedule update/delete changes ZenML metadata but not the backend schedule.
- A schedule with interval and cron behaves unexpectedly.

Likely causes:

- The active orchestrator does not support schedules.
- Local or local Docker orchestrator is active.
- Both cron and interval/run-once fields were set; orchestrator behavior usually favors cron.
- Backend schedule lifecycle management is not supported natively by the orchestrator.

Recovery:

- Confirm orchestrator scheduling support before using schedules.
- Use exactly one schedule style: cron, interval, or run-once.
- Use timezone-aware datetimes for `start_time`, `end_time`, and `run_once_start_time`.
- Keep `catchup=False` unless duplicate backfill runs are intended.
- Route schedule CLI lifecycle and backend cleanup to `../cli-and-client/SKILL.md` or `../stacks-and-integrations/SKILL.md` depending on whether the task is user operation or component implementation.

## Wait/Resume Fails

Symptoms:

- `zenml.wait(...)` raises immediately.
- A run remains paused after resolving a wait condition.
- Manual resume targets the wrong run.
- Timeout does not pause as soon as expected.

Likely causes:

- `wait(...)` was called in a static pipeline or inside a step.
- The wait condition is still unresolved.
- The paused run is a child run; the parent must be resumed.
- Concurrent submitted steps, maps, or child runs keep the dynamic execution tree active past the timeout.
- Required snapshot or stack references are missing.

Recovery:

- Move `wait(...)` into the body of a `@pipeline(dynamic=True)` function.
- Resolve active wait conditions first, then resume.
- Resume the parent run when the error points to a parent.
- If fast pausing is required, wait on futures or child runs before calling `wait(...)`.
- Do not delete snapshots, stacks, or code references required by paused runs.

## Local Config Isolation Problems

Symptoms:

- A smoke test modifies the user's active ZenML repository or server configuration.
- A local test accidentally connects to a remote server.
- Repeated smoke runs see stale stacks, runs, or stores.

Likely causes:

- The process inherited `ZENML_CONFIG_PATH`, `ZENML_LOCAL_STORES_PATH`, `ZENML_REPOSITORY_PATH`, or `ZENML_STORE_*` variables from the user's environment.
- The smoke ran from inside an existing ZenML repository without isolation.
- A singleton `Client` instance was created before environment isolation.

Recovery:

- Use `pipeline_smoke.py --run`, which sets temporary config, local stores, and repository paths before importing the ZenML client.
- For custom tests, set isolated `ZENML_CONFIG_PATH`, `ZENML_LOCAL_STORES_PATH`, and `ZENML_REPOSITORY_PATH` before constructing `Client()` or running a pipeline.
- Remove remote `ZENML_STORE_*` variables for isolated local smoke tests.
- Prefer a temporary directory and clean it after the run unless debugging requires `--keep-temp`.

## Single Step or Entry Point Confusion

Symptoms:

- A user wants to test step logic without creating a full ZenML run.
- Running a single step creates unexpected ZenML metadata.
- Direct Python tests are slow because they start ZenML orchestration.

Likely causes:

- Calling a decorated step invokes ZenML step execution behavior.
- The underlying function should be tested through `step.entrypoint(...)` instead.

Recovery:

- Use `my_step.entrypoint(...)` to bypass ZenML and test pure function logic.
- Use direct step calls only when a one-step ZenML run is desired.
- Set `ZENML_RUN_SINGLE_STEPS_WITHOUT_STACK=True` only when that behavior is intentionally wanted for the process.

## Source Resolution and Packaging Errors

Symptoms:

- Dynamic pipeline source cannot be resolved.
- Remote orchestrator cannot import a step, pipeline, hook, or materializer.
- A function defined in a notebook, closure, or local factory fails in remote execution.

Likely causes:

- Decorated functions are not importable from module scope.
- Hook callables or materializer classes are nested inside another function.
- Source files are not copied into the image or code bundle.

Recovery:

- Move steps, pipelines, hooks, and materializers to importable modules.
- Use source strings only for functions importable from the execution environment.
- Keep factories thin: create configured copies, but leave decorated functions importable.
- For Docker/remote runs, confirm `DockerSettings.copy_files`, source root, requirements, and image contents include the modules.
