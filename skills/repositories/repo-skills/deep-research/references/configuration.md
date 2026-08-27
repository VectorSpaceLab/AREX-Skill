# Configuration and Environment Reference

Use this reference before running any DeepResearch or WebAgent-family workflow. It summarizes public prerequisites and safe validation steps; it does not contain secrets or local environment paths.

## Python and Dependencies

| Workflow | Python/package guidance | Notes |
|---|---|---|
| Root DeepResearch ReAct inference | Python 3.10 is recommended; root requirements include OpenAI client, qwen-agent, transformers, vLLM, torch/CUDA packages, Dashscope, SandboxFusion, Jina/Serper-related clients, and evaluation dependencies | Installing the full requirements file is heavyweight and GPU/serving oriented; do it only for real inference, not simple file validation |
| WebDancer / WebSailor | Python 3.12 for WebDancer, Python 3.11 for WebSailor; both document `sglang[all]` and `qwen-agent[gui,rag,code_interpreter,mcp]` | Requires model weights and tool credentials |
| WebWalker | Python 3.10; `crawl4ai`, `qwen-agent`, Streamlit/provider dependencies | Run crawl4ai setup/doctor in a real WebWalker environment |
| WebWeaver | Python 3.12; local redis wheel, `vllm==0.10.2`, `modelscope`; planner/writer APIs | README-level requirement of at least 4x80G GPUs for the summary model |
| Safe generated helpers | Python 3.10+ stdlib | Bundled validators and choosers avoid imports from the source checkout |

Do not mutate a user’s existing Python environment to install the full GPU stack unless they explicitly approve. For diagnostic work, prefer a private environment and the bundled stdlib helpers.

## Root ReAct `.env` Groups

The root ReAct workflow reads a `.env`-style file. Use the `react-inference` helper to build or validate one:

```bash
python sub-skills/react-inference/scripts/build_react_env.py --print-template
python sub-skills/react-inference/scripts/build_react_env.py --validate .env --route local-vllm
```

Important groups:

- **Model and rollout**: `MODEL_PATH`, `DATASET`, `OUTPUT_PATH`, `ROLLOUT_COUNT`, `TEMPERATURE`, `PRESENCE_PENALTY`, `MAX_WORKERS`.
- **Search and web reading**: `SERPER_KEY_ID` for Search/Scholar, `JINA_API_KEYS` for page reading, `API_KEY`/`API_BASE`/`SUMMARY_MODEL_NAME` for summarizing visited pages.
- **File parsing**: `DASHSCOPE_API_KEY`, optional Dashscope base/model variables, optional IDP variables.
- **Python sandbox**: `SANDBOX_FUSION_ENDPOINT` for the PythonInterpreter tool.
- **Torch/NCCL**: multi-GPU variables in the template may need local network-interface and GPU fabric changes.

Never paste real API keys into prompts, generated reports, or code snippets that will be stored.

## Model Serving Routes

### Local vLLM route

The root launcher is designed for eight local vLLM servers on ports `6001` through `6008`, one per CUDA device `0` through `7`. Before launching:

1. Confirm the model weights exist and the model is compatible with the chosen vLLM/torch stack.
2. Confirm GPU count and memory are adequate.
3. Confirm no existing service occupies the planned ports.
4. Validate dataset and output paths.
5. Confirm all tools likely to be called have credentials or are intentionally disabled/unused.

### Hosted or OpenAI-compatible route

The root README notes an OpenRouter route for Tongyi-DeepResearch-30B-A3B. For any hosted OpenAI-compatible route:

1. Treat `MODEL_PATH` in runner arguments as the provider model id when using the existing runner pattern.
2. Adjust the model-call code in the user’s working copy to use the provider base URL, API key, and model name.
3. Preserve the ReAct output contract: `<think>`, optional `<tool_call>`, tool observations, and final `<answer>`.
4. If the provider separates reasoning content from final content, concatenate it in the expected `<think>...</think>` wrapper before downstream parsing.
5. Do not start local vLLM servers unless the user also wants local serving.

## Data and Output Configuration

- Input files must be `.jsonl` or `.json` and contain records with `question` and `answer` strings.
- File-parser questions embed uploaded file names in the question text and require the matching files under a `file_corpus` directory supplied to the validator or runtime.
- The rollout runner writes outputs under `<output-base>/<model-basename>_sglang/<dataset-argument>/` and appends one JSONL line per completed record per rollout.
- Distributed runs write split-suffixed `iterN_splitXofY.jsonl` files that must be merged before official three-round DeepSearch judging.

## Credential and Cost Boundaries

Before any network, judge, or model-serving action, state:

- Which secrets are required.
- Whether the action may incur API charges.
- Whether the action may download data/models or run for a long time.
- Which local files will be written.
- How to stop or resume safely.

Use bundled validators first whenever possible.
