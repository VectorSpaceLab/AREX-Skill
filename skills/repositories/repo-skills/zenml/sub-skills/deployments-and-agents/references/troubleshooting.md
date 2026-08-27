# ZenML Deployment and Agent Troubleshooting

Use this reference when deployment or agent examples fail, when local and remote behavior are confused, or when settings validate but the service does not run as expected.

## Examples Need API Keys, LLM Providers, or Network

Symptoms:

- `OPENAI_API_KEY`, provider, Langfuse, or cloud API key errors.
- Provider SDK raises authentication, rate limit, model not found, timeout, or network failures.
- Agent examples return mock/fallback responses instead of real LLM output.
- Framework examples pass locally only when provider credentials are exported.

Actions:

- Do not treat missing credentials as a skill gap. Classify the branch as `skipped` or `fallback` and report the exact missing capability without printing secret values.
- Prefer deterministic fallback paths for smoke tests. If an example already includes a rule-based or mock branch, preserve it for credential-free validation.
- Keep provider calls in a narrow step/helper so tests can stub the provider or set a fake client.
- If observability is optional, run the agent without Langfuse or tracing keys first, then add telemetry after the base path works.
- Ask before making network calls, downloading models, or using paid LLM APIs.

## Docker, Services, or Cloud Credentials Required

Symptoms:

- Docker daemon/socket errors, image build failures, or missing `uv`/package installer.
- Local deployment works, remote deployment cannot pull image or read artifacts.
- App Runner, Cloud Run, Kubernetes, or other deployers fail with auth/permission/region errors.
- Deployment is created but status stays `PENDING`, `ERROR`, or `UNKNOWN`.

Actions:

- Separate settings validation from actual deployment. `DeploymentSettings` and `DockerSettings` can often be instantiated without Docker or cloud access.
- For remote deployers, route component registration, service connectors, image builder, container registry, and cloud IAM issues to `../stacks-and-integrations/SKILL.md`.
- Verify the active stack has a deployer and that the deployment was created with the same deployer/stack expected for updates.
- Check deployment logs and metadata only after the user authorizes access to the active ZenML server/deployer.
- Do not run destructive lifecycle operations such as deprovision, delete, or force cleanup unless the user explicitly asks.

## Local vs Remote Deployment Confusion

Symptoms:

- User expects `http://localhost:8000` for a cloud deployment, or expects a public URL from a local deployer.
- A local artifact store or local ZenML store is used with a remote stack component.
- A deployment update fails because the original deployment belongs to another stack/deployer.
- A service works in batch mode but not as a long-running HTTP endpoint.

Actions:

- Identify the deployer flavor and deployment URL source first. Local process/Docker deployers usually expose localhost; remote deployers expose platform-managed URLs.
- Confirm whether the task is a pipeline deployment, snapshot deployment, or ordinary batch pipeline run.
- For remote deployments, check artifact store, registry, image builder, and server reachability before debugging application code.
- For updates, keep the original deployment name, stack, and deployer aligned. If the stack changed, create a new deployment or deliberately delete/recreate the old one.
- Make every deployed pipeline parameter JSON-serializable and defaulted; batch pipelines often accept objects that cannot become HTTP inputs.

## DeploymentSettings and DockerSettings Mismatch

Symptoms:

- CORS, docs paths, health path, or dashboard routing changes do not affect image builds.
- Dependencies are installed but endpoints or middleware are unchanged.
- `dashboard_files_path` works locally but not remotely.
- Custom endpoint/middleware source strings fail during deployment startup.

Actions:

- Put ASGI app behavior in `DeploymentSettings`; put package/image behavior in `DockerSettings`.
- Ensure `DeploymentSettings` is attached under `settings={"deployment": ...}` at pipeline level, not a step-level setting.
- Ensure `DockerSettings` is attached where the deployer/build path expects it and includes only required serving dependencies.
- For dashboard files, use a source-root-relative directory that will be included in the deployment image and contains `index.html`.
- For source-loadable hooks, endpoints, middleware, app extensions, app runners, or deployment services, ensure the dotted source path is importable inside the deployment image.
- Use `validate_deployment_settings.py --json` for schema-level checks before deployment.

## Model Deployer, Deployer, and Service Discovery Problems

Symptoms:

- Active stack has no deployer, or the code calls a model deployer when only a deployer is configured.
- `get_active_deployer()` or `get_active_model_deployer()` raises a stack component error.
- Service discovery returns no model server even though a deployment exists.
- A legacy model serving step cannot find, start, stop, or delete a `BaseService`.

Actions:

- Decide which abstraction is in use. Pipeline deployments use deployers and `zenml deployment ...`; specialized model servers use model deployers and service objects.
- Prefer pipeline deployments for new model/agent HTTP services unless an integration-specific model server is required.
- If using model deployers, verify the active stack has the right model deployer flavor and the service type/config fields match discovery criteria.
- Check whether continuous deployment mode, replacement behavior, model name/version, pipeline name, and step name are part of the lookup.
- Do not mix deployment IDs and model service IDs in client calls; route CLI/client resource audits to `../cli-and-client/SKILL.md`.

## Image Build and Container Registry Issues

Symptoms:

- Image build cannot find `requirements.txt`, source files, or dashboard assets.
- Remote backend cannot pull an image built locally.
- Registry push fails with unauthorized/not found/rate-limit errors.
- `DockerSettings` build options are ignored by the selected image builder.

Actions:

- Check paths relative to the ZenML source root and the deployment build context.
- Ensure remote backends use a registry reachable from the target platform, not a local-only image tag.
- Verify registry credentials through the container registry component or service connector without printing secrets.
- Match Docker build options to the selected image builder; some options only work with local Docker, Docker BuildKit, Kaniko, or cloud builders.
- Route detailed component/image-builder fixes to `../stacks-and-integrations/SKILL.md`.

## Agent Framework Matrix and Heavy Runner Skips

The repository's agent framework runner is a maintenance tool, not a runtime validation helper for this skill. Skip it by default because it:

- Creates fresh virtual environments for every framework example.
- Installs many optional dependencies.
- Often needs provider API keys and network.
- May write logs and summary files into the checkout.
- Can be slow and CI-oriented rather than a focused user smoke test.

When the user explicitly asks to run the matrix, first confirm provider credentials, network access, expected cost, Python version, environment isolation, and whether generated logs are acceptable.

## Credential-Free Adaptation Failure Modes

When adapting deployment examples without credentials, report outcomes precisely:

| Outcome | Meaning |
| --- | --- |
| `validated` | Settings or code shape passed safe local checks. |
| `fallback` | The workflow ran a deterministic branch intentionally because credentials were absent. |
| `skipped_credentials` | A real provider call was intentionally skipped because a key/token was missing. |
| `skipped_network` | A download, remote URL, or external API was intentionally skipped. |
| `skipped_infrastructure` | Docker, server, deployer, registry, or cloud infrastructure was not authorized or unavailable. |
| `skill_gap` | The skill lacked guidance or a bundled helper for a safe requested action. |
| `code_gap` | The user's code lacks defaults, JSON-safe inputs, fallback handling, or package settings needed for deployment. |

Do not collapse all skipped branches into failures. Skips with clear preconditions are often the correct safe result.

## Quick Triage Checklist

1. Can `zenml` and the relevant settings classes import in the active environment?
2. Are deployment pipeline inputs defaulted and JSON-serializable?
3. Are `DeploymentSettings` and `DockerSettings` attached under the right setting keys?
4. Is the task asking for a pipeline deployment, model deployer, snapshot, or batch run?
5. Does the active stack include the needed deployer/model deployer and remote dependencies?
6. Are provider/API/cloud credentials intentionally absent, present, or forbidden?
7. Is the failing operation safe schema validation, image build, deploy/provision, invocation, service logs, or deletion?
8. Should the issue route to pipeline authoring, stacks/integrations, CLI/client, server/stores, or maintenance instead of this sub-skill?
