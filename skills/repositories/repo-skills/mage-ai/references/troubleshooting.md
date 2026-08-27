# Cross-cutting troubleshooting

## Install and import problems

- Confirm the package is installed as `mage-ai`.
- Use the package-specific extras only when the workflow needs them, such as `mage-ai[ai]`, `mage-ai[streaming]`, or `mage-ai[dbt]`.
- If the CLI is missing, verify the environment imports `mage_ai` successfully first.

## Environment mismatch

- The repo's test helpers and data-directory behavior change when the environment is treated as test.
- If you are reproducing a repository test expectation that wants `.` as the data directory, set `ENV=test`.

## Workflow routing mistakes

- If a task needs `io_config.yaml` or profile resolution, route it to batch integrations.
- If it needs Kafka or another live stream, route it to streaming.
- If it needs dbt model orchestration, route it to dbt workflows.
- If it needs prompt-driven code generation, route it to AI workflows.
- If it needs block code or runtime-variable behavior, route it to pipeline authoring.

## External side effects

Do not run live cloud, database, broker, or model operations unless the user explicitly wants them.

Examples:

- EMR cluster creation
- Kafka or other broker connectivity
- dbt runs against a remote warehouse
- live AI model calls
- production database migrations

## Privacy and self-containment

- Do not copy local checkout paths or private environment locations into public skill content.
- Keep the runtime skill self-contained by using bundled scripts and bundled references, not by linking back into the source checkout.

## When the task needs a different route

If the user asks about a workflow that clearly belongs to another route, stop and hand them to that route instead of forcing the current one to absorb it.
