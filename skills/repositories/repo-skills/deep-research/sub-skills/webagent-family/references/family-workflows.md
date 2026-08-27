# Family Workflows, Prerequisites, and Blockers

Use this reference to turn a chosen family route into an evidence-backed prerequisite checklist. It intentionally summarizes the original project facts instead of linking to source READMEs.

## Prerequisite matrix

| Route | Python / package notes | Required services and credentials | Model/data prerequisites | GPU / serving notes | Practical status |
|---|---|---|---|---|---|
| DeepResearch root ReAct | Python 3.10 recommended; root requirements include the local inference stack. | Serper key for web/Scholar search, Jina keys for page reading, OpenAI-compatible key/base for summarization, Dashscope key for file parsing, SandboxFusion endpoint for Python interpreter. | Tongyi-DeepResearch-30B-A3B weights for local serving; JSON or JSONL data with `question` and `answer`; optional `eval_data/file_corpus/` for file-parser references. | Local launcher starts eight vLLM servers on ports 6001-6008, one per CUDA device 0-7; hosted OpenRouter/OpenAI-compatible route avoids local GPUs. | Use sibling `../react-inference/` for exact config/data workflow. |
| WebDancer | Python 3.12; `sglang[all]`; `qwen-agent[gui,rag,code_interpreter,mcp]`. | Google/Serper search key, Jina key, Dashscope key for demo. | WebDancer-32B model; sample QA and trajectory JSONL are present. | Deploy helper uses sglang with tensor parallelism 4 on port 8004. | Demo/deploy code exists but needs model, GPU, and credentials; training details reference LLaMA-Factory and verl. |
| WebSailor | Python 3.11; `sglang[all]`; `qwen-agent[gui,rag,code_interpreter,mcp]`. | Google search key and Jina key for tools. | WebSailor model weights; official BrowseComp/GAIA/xbench datasets must be obtained separately; sample `example.jsonl` remains to avoid test leakage; summary model currently Qwen2.5-72B-Instruct in the test script. | Evaluation script launches local SGLang servers for both evaluation model and summary model, then performs three inference passes. | Runnable only after heavyweight prerequisites; training method includes RFT cold start and DUPO RL. |
| WebSailor-V2 | README-only in inspected tree. | Not specified in local code. | Paper/model method: SailorFog-QA-2, Qwen3-30B-A3B backbone, SFT + RL, dual-environment RL. | No local serving script inspected. | Method reference; do not claim local runnable code. |
| WebShaper | Dataset/reference only; no package install specified in README. | None for reading the local 500-example data. | `data/webshaper.500.jsonl` fields are `id`, `question`, `formalization`, `answer`, `urls`. | None for dataset inspection. | Useful for data-synthesis/task-formalization guidance, not inference serving. |
| WebWatcher | Uses vLLM plus a vendored/forked qwen-agent area for visual search; image-search code is broad. | Image search key, Jina key, text search key, judge API key/base/model, optional Alibaba OSS access keys when uploading searched images. | Trained WebWatcher model, summary model qwen-2.5-72b or larger, benchmark JSONL files, and image data under the expected image folders. | Eval shell script serves model on port 8001 with CUDA devices 0-3 and summary model on port 6002 with CUDA devices 4-7; visual prompts allow many images per prompt. | Multimodal route; blocked by model, images, credentials, and vendored SDK complexity. |
| WebResearcher | README-only in inspected tree. | Not specified in local code. | Iterative Deep-Research Paradigm with `Think`, `Report`, `Action`; training uses RFT and RLVR; TTS uses last-k-fusion. | No local run script inspected. | Conceptual route for unbounded reasoning/report-memory design. Prefer WebWeaver for runnable report-writing code. |
| WebResummer / ReSum | `sglang[all]`; `qwen-agent[gui,rag,code_interpreter,mcp]`; source scripts under `src/`. | Google/Serper search key, Jina key, Dashscope key for evaluation/judging, summary API endpoint/key. | Three models for ReSum: inference model, visit-summary model, and ReSumTool-30B; official BrowseComp/GAIA data must be supplied. ReSumTool release is noted as pending. | `run_react.sh` serves infer model on GPUs 0-3 and summary model on GPUs 4-7; `run_resum.sh` serves infer model GPUs 0-3, summary model GPUs 4-5, and ReSum model GPUs 6-7. | Best route for context compression/restartable search, but blocked by model/tool releases and multi-vLLM services. |
| WebWeaver | Python 3.12; installs a local redis wheel, `vllm==0.10.2`, and `modelscope`; planner/writer scripts use local modules. | Serper key, ScraperAPI key, Dashscope key/base for planning and writing. | Summary model in HF format; README recommends at least qwen3-30b or gpt-oss-120b as summary model; planner/writer examples use qwen3-235b-a22b-instruct-2507. | README states at least 4x80G GPUs for serving the summary model. The included launcher uses eight visible GPUs for vLLM summary service on port 6002. | Best runnable route for open-ended reports with dynamic outlines, but very heavyweight. |
| WebWalker | Python 3.10; `crawl4ai`, `qwen-agent`, Streamlit-related stack; run `crawl4ai-setup` and `crawl4ai-doctor` before local demo/RAG. | OpenAI-compatible or Dashscope key for demo; RAG system can use OpenAI, Gemini, Ark, Moonshot, Baidu, or Dashscope-style providers; evaluation uses GPT-style API. | WebWalkerQA has 680 human-verified queries over 1373 webpages; silver split has about 14k QA pairs; local code expects output paths for RAG/eval. | API-based; no local model GPU required unless user chooses a local provider. | Best route for traversal/RAG benchmark experiments, not for root DeepResearch official metrics. |
| WebLeaper | README/method only. | Not specified in local code. | Entity-intensive tasks with Basic, Union, Reverse-Union variants; SFT filters by ISR/ISE; RL uses hybrid reward and GRPO; backbone noted as Qwen3-30B-A3B-Thinking-2507. | No local run script inspected. | Method reference for efficient information seeking; do not promise executable pipeline. |
| AgentFold | Python code imports OpenAI client, transformers tokenizer, requests, Jinja2, Search/Visit tools, tqdm. | Search/visit APIs through its tool modules; local OpenAI-compatible vLLM endpoints. | Dataset JSONL files under `datasets/`; model/tokenizer path placeholders. | `serve.sh` launches six one-GPU vLLM endpoints on ports 8000-8005 plus a gpt-oss-120b summary endpoint on port 8006 using GPUs 6-7. | Experimental route for proactive compression; inspect/patch before running. |
| ParallelMuse | Python code imports AsyncOpenAI, transformers, NumPy, json/json5, aiohttp, Search/Visit tools. | Local OpenAI-compatible endpoint for rollouts and convergence. | Sample data placeholders; convergence script expects rollout JSONL with `question`, `answer`, `prediction`, and `rollout`. | vLLM deploy helper uses tensor parallel size 4 and max model length 131072. | Experimental route for test-time scaling; source contains TODO placeholders and rough edges, so treat as adaptable pattern. |
| NestBrowse | Python code uses Async/browser tooling, MCP client, transformers tokenizer, Search/Visit/Click/Fill tools. | Browser MCP server URL, local OpenAI-compatible model endpoint. | Tokenizer path, benchmark JSONL under `data/`, model name, output under `results/`. | vLLM deploy helper uses tensor parallel size 4 and max model length 131072; runtime constants use 128K agent context and 16 workers. | Best family route for nested browser-use; blocked until MCP browser service is available. |
| AgentFounder | README/method only. | Not specified in local code. | Agentic CPT with 32K/128K contexts, open-world memory, planning/reasoning/decision action synthesis, AgentFounder-30B results. | No local run script inspected. | Method route for continual pretraining/scaling-law discussions. |
| AgentScaler | README/method only. | Not specified in local code. | Simulated heterogeneous environment construction and two-phase agent fine-tuning for function-calling benchmarks. | No local run script inspected. | Method route for environment scaling rather than web-search inference. |

## Workflow selection patterns

### Text-only long-horizon QA

- For Tongyi DeepResearch 30B-A3B itself, choose the root ReAct sibling sub-skill.
- For WebAgent-family comparison or alternate model selection, start with WebDancer for autonomous ReAct search and WebSailor for high-uncertainty complex browse tasks.
- For context exhaustion or very long tool sequences, compare WebResummer/ReSum and AgentFold before adding more max context.

### Open-ended report writing

- Choose WebWeaver when the desired artifact is a structured report with citations, dynamic outline changes, and writer-side evidence retrieval.
- Treat WebResearcher as conceptual guidance for iterative `Think`/`Report`/`Action` memory, not as a local runnable implementation in this checkout.
- Block early if the user lacks summary-model serving capacity, planner/writer API access, or web scraping/search credentials.

### Multimodal deep research

- Choose WebWatcher when the query requires image search, visual reasoning, VQA datasets, or multimodal benchmarks.
- Do not try to repurpose text-only DeepResearch or WebSailor instructions for image tasks unless the image requirement is explicitly removed.
- Plan image data acquisition and credential checks before any model-serving command.

### Data synthesis and training

- Choose WebShaper for task formalization and the released 500-sample data format.
- Choose WebSailor/WebSailor-V2 for high-uncertainty SailorFog-style post-training and RL concepts.
- Choose WebLeaper for dense entity retrieval and efficiency-aware training signals.
- Choose AgentFounder for continual pretraining over agentic data and AgentScaler for simulated environment scaling/function-calling experiences.
- Clearly state when local code/data is not present and the plan is methodological rather than executable.

### Test-time scaling and convergence

- Choose ParallelMuse when the user already has multiple rollouts or wants report-based aggregation of independent problem-solving trajectories.
- Choose WebResearcher when the user asks about last-k-fusion conceptually.
- Choose AgentFold if the missing capability is not just aggregation but proactive context compression during each rollout.
- Route final metric computation to `../benchmark-evaluation/`.

### Nested browser-use

- Choose NestBrowse when the user wants click/fill/page-state interaction rather than Search/Visit-only retrieval.
- Confirm a browser MCP server and tokenizer/model endpoints before suggesting execution.
- If the user only needs RAG over WebWalkerQA webpages, prefer WebWalker instead.

## Minimal blocker checklist before proposing execution

Ask or inspect for these blockers before recommending a concrete run:

1. **Exact route:** family variant plus whether the task is inference, data synthesis, training, evaluation, aggregation, or report writing.
2. **Runnable evidence:** code present versus README/method note only.
3. **Model weights:** primary inference model, summary model, ReSum tool, VLM, or planner/writer model as applicable.
4. **Serving mode:** local vLLM/SGLang, OpenAI-compatible remote endpoint, Dashscope/OpenRouter-style endpoint, or no model serving needed.
5. **Credentials:** search, page reading, scraper, image search, judge API, OSS, SandboxFusion, browser MCP service.
6. **Data:** JSON/JSONL task data, official benchmark files, image folders, WebWalkerQA data, or generated rollout files.
7. **Hardware:** root eight-port DeepResearch launcher, WebWeaver 4x80G summary note, WebWatcher split model/summary GPUs, ReSum three-service vLLM setup, or no GPU for hosted API routes.
8. **Output contract:** inference rollouts, final report JSONL, benchmark predictions, synthesized data, or method summary.
