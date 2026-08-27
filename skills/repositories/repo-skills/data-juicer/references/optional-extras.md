# Optional extras

## Extra matrix
| Extra | Unlocks | Use it when | Caution |
| --- | --- | --- | --- |
| `tools` | `fastapi`, `mcp[cli]`, `rank-bm25`, `matplotlib` | You need the service surface, MCP tooling, or ranking helpers | Not required for plain local recipes |
| `distributed` | `ray[default]`, `pandas<3`, `uvloop`, `pyspark`, storage helpers | You need Ray-backed or Spark-adjacent workflows | Do not use as a substitute for the base package |
| `vision` | image/video operator families | Your workflow is image or video heavy | Can pull in large multimedia dependencies |
| `nlp` | text-oriented NLP operators and helpers | Your workflow is text heavy | Some packages are optional or large |
| `audio` | audio operators and helpers | Your workflow is audio heavy | Audio stacks may need extra system libraries |
| `generic` | model/runtime helpers and broader multimodal support | You need model-backed operators | Usually broader than local recipe work requires |
| `ai_services` | DashScope, OpenAI, Label Studio integrations | You need external service integrations | Requires the right credentials and endpoints |
| `dev` | docs/test/tooling support | You are maintaining the skill or repo | Not for normal end users |
| `all` | every optional group | You truly need a full development install | Avoid for routine troubleshooting |

## Default rule
Choose the smallest extra group that covers the workflow. Add more only when the selected sub-skill says they are needed.
