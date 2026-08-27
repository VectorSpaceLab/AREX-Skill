# Optional integrations and provider boundaries

Harbor's base distribution keeps provider SDKs optional. The installed factory
loads built-in environment modules lazily, so importing the factory should not
require every cloud SDK. Select the smallest extra for the requested provider;
verify its import and `preflight()` with credentials mocked or supplied only
under an explicit execution gate.

## Installation policy

Use one of these patterns, matching the package manager that owns the Harbor
installation:

```bash
uv tool install 'harbor[daytona]'
# or
pip install 'harbor[daytona]'
```

Replace `daytona` with the selected extra. `harbor[cloud]` is a convenience
bundle, not a default debugging step: it increases dependency conflicts and
can obscure which provider is missing. Do not install `all` just to inspect a
class. The required core environment is Python 3.12+ with Harbor imported and
its CLI entry point available.

## Current provider extra map

The current project metadata exposes these provider or feature extras. Names
are version-sensitive; check the installed package help and metadata before
writing a claim.

| Surface | Extra | Main gate |
|---|---|---|
| Hugging Face datasets | `huggingface` | dataset SDK and credentials as needed |
| Container/cloud environments | `e2b`, `daytona`, `islo`, `modal`, `runloop`, `gke`, `ec2`, `novita`, `cwsandbox`, `wandb`, `use-computer`, `blaxel`, `opensandbox`, `beam`, `skypilot`, `hf-sandbox`, `hyperbrowser`, `vercel` | selected provider SDK plus provider auth |
| LangSmith environment/plugin | `langsmith` | LangSmith SDK, API/profile, endpoint, and quota |
| Tensor/hosted sandbox | `tensorlake` | TensorLake SDK and account configuration |
| Computer-1 native SDKs | `computer-1` | selected OpenAI/Anthropic/Google SDK and model auth |
| CUA or adapter workflows | `cua`, `adapter` | vendor SDK or adapter-specific agent SDK |
| DSPy / Tinker workflows | `dspy`, `tinker` | research/training dependencies and service credentials |
| Bundle | `cloud`, `all` | all transitively selected provider surfaces; avoid for minimal checks |

This table describes package boundaries, not successful support. Capability
matrices, network policy support, compose support, GPU support, and credential
requirements remain provider-specific.

## Provider preflight sequence

For an environment type, `EnvironmentFactory.run_preflight(type)` lazily loads
the provider and invokes its class-level `preflight()`. A custom
`EnvironmentConfig.import_path` can be preflighted by passing the import path.
Use this before `Job.create()` queues trials. Typical outcomes:

1. `ImportError` or `MissingExtraError`: SDK/extra is absent. Install the
   narrow extra or choose Docker; do not add credentials yet.
2. `SystemExit` naming an API key, profile, CLI, or config: dependency loaded,
   but authentication/configuration is absent. Ask for the credential gate.
3. A provider request or endpoint error: authentication, account, network,
   endpoint, or quota is invalid. Preserve the provider's error; do not hide it
   with Docker fallback if the requested experiment depends on that provider.
4. Preflight passes: only credentials/config presence was checked. It does not
   prove that the task image, Compose mode, resource policy, network policy,
   or model API will run.

Never print secret values. Use a fake client or monkeypatch provider SDK calls
in tests. For actual cloud smoke tests, record provider, region/workspace,
image, network mode, resource request, cleanup (`delete`), and the explicit
approval that permitted external spend.

## LangSmith boundaries

LangSmith appears in two separate integration surfaces:

- `EnvironmentType.LANGSMITH` loads `LangSmithEnvironment` and requires the
  `langsmith` extra. Its `preflight()` accepts an API key, alternate LangChain
  key, configured profile, or SDK profile. The environment constructor supports
  explicit API key/endpoint and sandbox options; a prebuilt image is required
  for the provider's direct environment path. Compose support and network
  policy are capabilities of the selected installed version, not assumptions.
- The `harbor-langsmith` package supplies a `LangSmithPlugin` registered under
  the `harbor.plugins` entry-point name `langsmith`. It attaches job/trial
  hooks, may synchronize a dataset, creates or reuses an experiment session,
  and publishes trial phase runs. It needs `LANGSMITH_API_KEY` unless an
  explicit key is passed. Constructor kwargs include `dataset_name`,
  `experiment_name`, `experiment_id`, `endpoint`, `api_key`, `workspace_id`,
  `sync_dataset`, and `fail_fast`.

Choose environment versus plugin deliberately: the environment changes where
containers run; the plugin observes/publishes job lifecycle. The plugin's
network requests and dataset/session mutations are external side effects. Use
`sync_dataset=false`, a test endpoint, or mocked requests for tests; never
claim LangSmith telemetry was verified from a local plugin import alone.

## RewardKit boundaries

RewardKit is a first-party grading toolkit, not a job plugin or agent provider.
Task-side verifier authoring belongs to `author-benchmarks`: a task's test
entry point can invoke the `rewardkit` CLI or import `rewardkit` criteria and
must write Harbor's reward JSON/text contract. Its own optional extras are
narrow (`documents`, `image`, or `all`) and are separate from Harbor's cloud
extras.

RewardKit judges may call a LiteLLM model or an agent CLI and may use MCP
servers declared in the judge configuration. Treat those as verifier-side
model/network/credential gates. Do not route a RewardKit criterion into a
framework extension merely because it calls a model. Test criteria and score
aggregation with local fixtures and mocked judges; run real judges only under
an explicit evaluation approval.
