# DeepKE repo overview

DeepKE is a knowledge extraction toolkit that groups classic supervised extraction, joint triple extraction, large-language-model knowledge extraction, data-preparation helpers, and an MCP wrapper. This generated skill focuses on user-facing operating workflows rather than repository maintenance.

## Capability map

| Area | Covered by | Main workflows |
| --- | --- | --- |
| Supervised NER/RE/AE/EE | `sub-skills/supervised-extraction` | Standard NER, few-shot NER, cross-domain NER, multimodal NER, standard RE, few-shot RE, document RE, multimodal RE, standard AE, standard EE, cnSchema quick-load. |
| Data preparation | `sub-skills/data-preparation` | Doccano/manual annotation planning, JSON/DOCX/XLSX conversion, BIO text, RE/AE CSV, weak NER from dictionaries, distant RE from triples. |
| Triple extraction | `sub-skills/triple-extraction` | PRGC, PURE, ASP, MT5/CCKS, cnSchema triple workflows, MT5 prediction conversion. |
| LLM knowledge extraction | `sub-skills/llm-workflows` | DeepKE-LLM, OneKE, InstructKGC, LLMICL/API, UnleashLLMRE, CodeKGC, CPM-Bee, LoRA/P-tuning/OpenDelta planning. |
| MCP wrapper | `sub-skills/mcp-tools` | Local FastMCP stdio server, client/tool-call flow, environment variables, TSV helper, security/mutation caveats. |

## Environment families

DeepKE's examples span several incompatible runtime families. Use isolated environments when necessary:

1. **Classic supervised DeepKE**: PyTorch/Transformers/Hydra plus task-specific NER/RE/AE/EE dependencies.
2. **Triple extraction**: PRGC/PURE/ASP/MT5 each has its own stack; PURE is AllenNLP-sensitive, ASP is Apex/CUDA-sensitive, and MT5 is DeepSpeed-heavy.
3. **DeepKE-LLM**: model-family-specific LoRA/P-tuning/OpenDelta, Accelerate/DeepSpeed, API clients, and large-model checkpoints.
4. **MCP wrapper**: MCP/FastMCP plus a configured local DeepKE checkout and predictor environments.

A single CPU environment can verify imports and bundled converters, but it cannot prove every GPU, Apex, DeepSpeed, multimodal, or large-model workflow.

## Safe bundled operations

The generated scripts intentionally do safe work only:

- Import and dependency diagnostics.
- Local path/file-existence checks.
- Pure JSON/CSV/TXT/DOCX/XLSX/TSV format conversion.
- MT5 prediction string parsing.
- Instruction JSONL shaping.

They do **not** train, download, call APIs, launch DeepSpeed, build Apex, load large model weights, or mutate source DeepKE configs.

## Resource-dependent operations

Ask for explicit user approval before starting:

- Any training or prediction that loads BERT/BART/T5/CLIP/OneKE/LLM checkpoints.
- Multimodal, document-level, event, ASP/Apex, MT5/DeepSpeed, or large-model LoRA/P-tuning jobs.
- API/LLM calls requiring credentials, endpoint access, or per-token cost.
- MCP server operation against a real checkout because the source wrapper shells out and mutates local files.

## Known coverage limits

- Full model-quality reproduction was not attempted during skill creation.
- GPU-only and large-model workflows are documented and diagnosed but not fully runtime-verified without the required hardware, data, and checkpoints.
- The bundled converters cover common, source-backed schemas but cannot normalize every custom annotation export or model-output format without a task-specific schema decision.
- MCP guidance is conservative because the source server uses local subprocesses and mutable config/data files.

## Recommended first response pattern for downstream users

When a user asks a DeepKE question:

1. Name the selected sub-skill and why it matches the task.
2. Ask for only the missing concrete runtime inputs: data path/schema, model/checkpoint path, API credentials availability, GPU availability, or desired output format.
3. Run a bundled checker/converter when safe and useful.
4. If the requested operation is long-running or resource-dependent, present the exact command plan and ask for approval before execution.
5. Report whether the result proves syntax/import readiness, data readiness, or actual model runtime readiness.
