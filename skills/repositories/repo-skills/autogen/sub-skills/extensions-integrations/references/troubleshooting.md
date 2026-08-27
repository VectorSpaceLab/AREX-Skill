# Extensions Troubleshooting

Use this matrix after identifying the integration surface and running the safe inspection script. Keep diagnosis staged: package import, constructor validation, configuration/credentials, service availability, then real execution only when explicitly allowed.

## Symptom Matrix

| Symptom | Likely cause | Safe first checks | Fix direction |
| --- | --- | --- | --- |
| `ModuleNotFoundError` or `ImportError` for `openai`, `anthropic`, `mcp`, `docker`, `chromadb`, `redis`, `semantic_kernel`, `llama_cpp`, `ollama`, `azure.*` | Narrow extra not installed | Run `inspect_extensions.py --json`; map import to `references/optional-extras.md` | Install the exact `autogen-ext[...]` extra for the surface |
| OpenAI custom endpoint raises `model_info is required` | Unknown/custom model lacks capabilities metadata | Constructor-only check with placeholder key and explicit `model_info` | Provide `vision`, `function_calling`, `json_output`, `structured_output`, and `family` metadata |
| OpenAI/Azure config logs expose secrets | Config or exception printed directly | Check dumped component config for redaction before logging | Avoid printing raw kwargs; rely on secret-aware config models and scrub logs |
| Azure OpenAI authentication fails | Wrong key/token provider, endpoint, deployment, API version, or RBAC role | Verify field names: `azure_endpoint`, `azure_deployment`, `api_version`, `model`; inspect credential type | Correct deployment/API version; assign required role; choose key vs token auth intentionally |
| Azure AI Inference/GitHub Models config fails | Missing `endpoint`, `credential`, `model_info`, or GitHub `model` | Constructor validation without network call | Provide required fields and compatible Azure credential |
| Anthropic or Bedrock fails | Missing direct key vs AWS Bedrock credentials/region | Distinguish `AnthropicChatCompletionClient` from `AnthropicBedrockChatCompletionClient` | Configure the right provider credential path and model metadata |
| Ollama client imports but calls fail | Ollama service not running or model not pulled | Import/spec check only; separately check service/model under user approval | Start Ollama and pull model, or use explicit host/model |
| llama.cpp import/build error | Native wheel/platform/compiler/GPU mismatch or missing model file | Package spec check and model-path existence check | Install compatible `llama-cpp-python`; verify model path and runtime settings |
| Semantic Kernel adapter rejects feature | Connector lacks structured output/tool-choice support | Check adapter warnings and connector docs; inspect settings object | Use a supported connector/setting combination or disable unsupported feature |
| MCP `Actor is not initialized` | Workbench start failed or server connection invalid | Review server params, command availability, env, cwd, URL/headers; do not run untrusted server | Fix transport params and trust boundary; start only after review |
| MCP stdio hangs | Server process never starts, waits for input, wrong args, or mixed stdout protocol noise | Inspect command/args and server help offline if trusted | Use known-good server command, timeout, and clean stdio protocol output |
| MCP tool returns error content | Server-side exception or argument schema mismatch | Inspect tool schema and arguments; use mocked workbench tests if possible | Fix schema/arguments or server implementation |
| MCP roots/sampling/elicitation unsupported | Missing `McpSessionHost` capabilities | Check if server requires host callbacks | Configure `McpSessionHost` with sampler, elicitor, and roots provider as needed |
| Docker executor import fails | Missing `docker` extra | Import check | Install `autogen-ext[docker]` |
| Docker executor start fails | Docker daemon unavailable, image problem, or container startup failure | Do not ping/start in static checks; inspect daemon policy and image name | Start Docker, choose/pull image, fix permissions, avoid privileged mounts |
| Local executor warning/fallback surprises user | `create_default_code_executor()` fell back to local because Docker unavailable | Check warning text and backend type | Install/start Docker or explicitly choose local only for trusted code |
| Jupyter executor cannot run | Missing kernel, executor not started, invalid output directory, timeout too low | Import check and kernel list under approval | Install kernel, use async context manager/start, set output dir/timeout |
| Docker-Jupyter cannot connect | Docker image/gateway/token/port issue | Check package specs and intended image/port without starting | Fix image, port, token, gateway connection info; start only under explicit plan |
| Azure Dynamic Sessions fails | Endpoint, credential, role, or pool unavailable | Check constructor args and Azure auth mode; avoid service call in import checks | Use valid pool endpoint and credential with required permissions |
| Redis cache/memory misses silently | Redis connection/serialization errors are swallowed or return defaults | Inspect Redis config and service health under approval | Fix host/port/db/auth/SSL; add observability around cache misses |
| ChromaDB memory import/config fails | Missing `chromadb`, invalid persistent path/HTTP config, embedding function issue | Import check and config field review | Install `chromadb`, fix path/server, configure embedding provider |
| mem0 memory fails | Cloud key missing or local config omitted | Check `is_cloud` mode and config/API key choice | Provide `MEM0_API_KEY`/key for cloud or local config plus services for local mode |
| Web surfer import/runtime fails | Missing Playwright/browser deps or browser binaries | Import check; do not launch browser in static checks | Install `web-surfer` extra and browser binaries under approved setup |
| File/video surfer fails | Missing MarkItDown/Magika/media deps or invalid file policy | Import check and local file path policy | Install exact surfer extra; verify file/media paths and allowed access |
| gRPC runtime import fails | Missing `grpc` extra | Import `autogen_ext.runtimes.grpc` | Install `autogen-ext[grpc]`; route distributed design to `core-runtime` |

## Diagnosis Workflow

1. Run the inspection script and identify missing packages by surface.
2. Read the relevant reference file for the integration class and exact extra.
3. Perform constructor-only validation with placeholder credentials only when that constructor does not call the provider.
4. Review secrets and serialized configs before logging.
5. Only then run provider/service smoke tests, and only for the service the user explicitly authorized.

## Version Boundary Notes

- The verified 0.7.x library packages are `autogen-core`, `autogen-agentchat`, and `autogen-ext` at `0.7.5`.
- `pyautogen` is a compatibility package and should be handled through `tools-studio-bench` when the task involves old 0.2-style APIs.
- Magentic-One CLI and AutoGen Studio have dependency boundaries that may conflict with 0.7.x libraries; do not install them into the same environment without explicit compatibility planning.

## When to Switch Sub-Skills

- Use `agentchat-workflows` for `AssistantAgent`, teams, streaming, termination, handoffs, state, and model-client usage inside AgentChat.
- Use `core-runtime` for routed agents, message handlers, topics/subscriptions, component serialization design, and distributed runtime architecture.
- Use `tools-studio-bench` for Studio, Magentic-One CLI, AG Bench, and `pyautogen` compatibility decisions.
