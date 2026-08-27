---
name: llm-workflows
description: "Guide DeepKE-LLM instruction KGC, OneKE, ICL/API, CodeKGC, and
  large-model workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DeepKE LLM workflows

Use this sub-skill when a task asks for DeepKE-LLM, instruction-based knowledge graph construction, OneKE, InstructKGC, LLM in-context extraction, LLM-powered data augmentation, UnleashLLMRE, CodeKGC, CPM-Bee, or large-model fine-tuning/inference around information extraction.

## Route by intent

- **Choose among OneKE, InstructKGC, ICL/API, CodeKGC, UnleashLLMRE, or CPM-Bee**: read [references/workflows.md](references/workflows.md) for the workflow decision table and resource expectations.
- **Prepare instruction data or inspect JSONL schemas**: read [references/data-formats.md](references/data-formats.md) and use [scripts/convert_ie_instruction.py](scripts/convert_ie_instruction.py) for a safe, standalone conversion path for common NER/RE/SPO-style records.
- **Check local large-model dependencies, API environment variables, CUDA visibility, and optional paths**: run [scripts/check_llm_workflow_env.py](scripts/check_llm_workflow_env.py). It does not load models or call remote APIs.
- **Debug GPU memory, LoRA/P-tuning, OpenAI-compatible API, JSONL, prompt, or converter failures**: read [references/troubleshooting.md](references/troubleshooting.md).
- **Compare model/runtime families**: read [references/model-and-runtime-overview.md](references/model-and-runtime-overview.md) before mixing dependencies from classic DeepKE and DeepKE-LLM.

## What this sub-skill owns

- DeepKE-LLM instruction-based information extraction and knowledge graph construction.
- InstructKGC-style conversion, LoRA fine-tuning, P-tuning, and OpenDelta workflows for LLaMA/ZhiXi, ChatGLM, MOSS, Baichuan, Qwen, CPM-Bee, and related large models.
- OneKE schema-based bilingual information extraction planning and inference readiness.
- LLMICL-style OpenAI-compatible in-context information extraction, data augmentation, and CCKS instruction KGC.
- UnleashLLMRE few-shot relation-extraction prompting/data augmentation.
- CodeKGC code-style prompts and schema/in-context/test-example files for code LLMs.

## What this sub-skill does not own

- Classic BERT/CRF/CNN/RNN/GCN supervised NER, RE, AE, EE, multimodal, document, few-shot, or cnSchema quick-load workflows; route those to `supervised-extraction`.
- PRGC, PURE, ASP, and MT5 non-LLM triple-extraction workflows; route those to `triple-extraction`.
- Generic weak supervision and distant supervision data prep for classic DeepKE examples; route those to `data-preparation`.
- Deploying the DeepKE MCP server/client wrapper; route that to `mcp-tools`.

## Quick operating pattern

1. Decide whether the user wants **data conversion**, **prompt/API inference**, **local model inference**, **LoRA/P-tuning/OpenDelta fine-tuning**, **evaluation**, or **troubleshooting**.
2. Confirm resources before expensive work: GPU type/memory/count, model checkpoint availability, API credentials, dataset size, output directory, and network/cache policy.
3. Run `python scripts/check_llm_workflow_env.py --workflow <workflow>` to inspect packages and environment variables without loading the model.
4. For instruction data, inspect JSONL line-by-line. DeepKE-LLM tooling commonly writes JSONL, not one large JSON array.
5. Use the workflow reference to set task-specific fields: `task`, `source`, `instruction`, `schema`, `input`, `output`, model name/path, LoRA/output directories, API endpoint, and prompt templates.
6. Do not silently start model downloads, API calls, DeepSpeed jobs, or multi-GPU fine-tuning. Confirm cost and runtime first.

## Safety and verification stance

The bundled scripts are safe diagnostics and data shapers. They do not train models, call OpenAI-compatible APIs, download model weights, run OneKE, or launch DeepSpeed. Large-model runtime success still requires user-provided checkpoints or API credentials and suitable hardware.
