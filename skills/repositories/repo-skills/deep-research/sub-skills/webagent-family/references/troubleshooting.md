# WebAgent Family Troubleshooting

Use this reference when family routing is unclear or a chosen variant is blocked. Keep fixes self-contained: do not depend on the original checkout, and do not expose local machine paths or private environment prefixes.

## Project path confusion

Symptoms:

- User says “DeepResearch” but asks about WebDancer/WebSailor/WebWatcher behavior.
- User says “WebAgent” but needs root Tongyi DeepResearch ReAct `.env` or OpenRouter setup.
- User asks for “evaluation” but mixes rollout generation with official judging.

Resolution:

1. Treat `DeepResearch` root as the Tongyi DeepResearch 30B-A3B model and root ReAct/evaluation stack.
2. Treat `WebAgent` as the family umbrella containing WebDancer, WebSailor, WebWatcher, WebWalker, WebWeaver, WebResummer/ReSum, and experimental variants.
3. Treat `Agent` as related training/scaling methodology docs: AgentFounder and AgentScaler.
4. Route detailed root inference configuration to `../react-inference/`.
5. Route official benchmark metric mechanics to `../benchmark-evaluation/`.
6. Use `scripts/choose_webagent_variant.py` when the user describes capabilities rather than names.

## Unpublished or incomplete checkpoints/data/code

Disclose these gaps before promising a run:

- WebSailor README exposes sample/eval workflow and mentions public smaller-model releases in family docs, while some large-model/trajectory assets are described as coming soon or external.
- WebSailor-V2 is README/paper-method evidence in this checkout, not a complete local implementation.
- ReSumTool-30B is described as a specialized summary tool with release pending; ReSum execution is blocked without an equivalent summary tool endpoint.
- WebResearcher, WebLeaper, AgentFounder, and AgentScaler are mostly method/reference documents in the inspected tree.
- ParallelMuse and AgentFold contain experimental code with placeholders and hard-coded model/service assumptions; review and patch before execution.
- NestBrowse requires an external browser MCP server and explicit tokenizer/model paths.

Safe response pattern:

- “This route is evidence-backed for method selection, but not immediately runnable from the bundled skill alone.”
- “To execute, provide or approve model weights/endpoints, data, credentials, and hardware; otherwise I can produce a route/prerequisite plan only.”

## Missing API or service credentials

Credential names are public requirements, not values. Never echo secrets. Common requirements by route:

| Route | Common credential/service names |
|---|---|
| DeepResearch root ReAct | Serper search, Jina page reading, OpenAI-compatible summary API, Dashscope file parsing, SandboxFusion interpreter endpoint. |
| WebDancer | Google/Serper search, Jina, Dashscope. |
| WebSailor | Google/Serper search, Jina; evaluation/judge credentials if scoring. |
| WebResummer/ReSum | Google/Serper search, Jina, summary API endpoint/key, Dashscope judge key. |
| WebWeaver | Serper search, ScraperAPI page reading, Dashscope planning/writing endpoint/key. |
| WebWatcher | Image search, text search, Jina, judge API/base/model, optional Alibaba OSS credentials for uploading searched images. |
| WebWalker | OpenAI-compatible, Dashscope, or other provider keys for demo/RAG; GPT-style key for evaluation. |
| NestBrowse | Browser MCP server URL plus local model endpoint. |

Troubleshooting steps:

1. Validate that the task truly needs the credentialed service; some route-selection and schema checks are stdlib-only.
2. Prefer dry-run validation and prerequisite reporting before spending API credits.
3. For judge APIs, route metric mechanics to `../benchmark-evaluation/` and validate rollout shape before judging.

## Large images, model weights, and archives

- WebWatcher image tasks require benchmark image folders and may involve large archives. Do not start downloads without user approval and storage planning.
- WebWatcher VLM inference also requires both the trained model and a summary model; missing either blocks execution.
- WebWeaver report writing requires a strong planner/writer model and a separate summary model; README states at least 4x80G GPUs for summary-model serving.
- Root DeepResearch local inference and AgentFold/ParallelMuse/NestBrowse local serving can require multiple vLLM ports and high context length; hosted OpenAI-compatible routes may avoid local GPUs but still need credentials.
- WebWalkerQA and official BrowseComp/GAIA/xbench-style datasets may be external even when sample JSONL files are present.

## Generated, vendored, or broad SDK areas

- WebWatcher includes a forked/vendored qwen-agent area used by the visual-search inference scripts. Treat it as project-specific runtime plumbing; do not copy broad vendored code into generated skills.
- WebWeaver includes generated-looking TopSDK request/client stubs and a local redis wheel. Treat these as implementation details for the original workflow, not general family-routing knowledge.
- Family shell scripts frequently start long-running model servers, modify packages, or assume fixed ports. This sub-skill records prerequisites; it does not bundle those shell scripts because they are not safe standalone helpers.

## Port and GPU failures

Common causes:

- Root DeepResearch launcher assumes eight vLLM servers on ports 6001-6008 and one visible CUDA device per server.
- WebWeaver summary launcher uses eight GPUs for a vLLM summary service and the README states at least 4x80G GPUs for summary serving.
- WebWatcher splits the trained VLM and summary model across two vLLM services.
- ReSum scripts serve separate inference, visit-summary, and ReSum-tool models.
- AgentFold serve helper starts multiple OpenAI-compatible endpoints and a summary model endpoint.

Fixes:

1. Check whether the user can use an OpenAI-compatible hosted endpoint instead of local serving.
2. Confirm model weights, context length, tensor parallel size, and available devices before launching servers.
3. Check for existing processes on the required ports.
4. If the route is only selection or planning, avoid launching servers entirely.

## When to route back to siblings

Route to `../react-inference/` when the user asks for:

- Root `.env` variables, dataset JSON/JSONL validation, file-corpus references, ReAct tools, `run_multi_react` behavior, OpenRouter adaptation, or root vLLM launcher details.

Route to `../benchmark-evaluation/` when the user asks for:

- `iter1.jsonl`/`iter2.jsonl`/`iter3.jsonl` rollout validation, official HLE/deep-search judging, Pass@k/round metrics, invalid answer rates, action statistics, or judge API troubleshooting.

Stay in this sub-skill when the user asks for:

- Which family variant fits an underspecified task, what prerequisites/blockers that variant has, or how to compare methods across the DeepResearch/WebAgent/Agent family.
