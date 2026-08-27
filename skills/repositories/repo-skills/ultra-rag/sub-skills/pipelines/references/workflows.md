# UltraRAG Pipeline Workflows

## Purpose

Read this when you need to choose a workflow family or explain which server
combination belongs to a named UltraRAG recipe. The source file names here are
provenance labels; the usable guidance is distilled in this reference.

## Workflow families

| Family | Source-evidenced pipelines | Typical server mix | Notes |
| --- | --- | --- | --- |
| Install smoke | `examples/experiments/sayhello.yaml` | `sayhello` | Smallest end-to-end sanity check. |
| Plain LLM | `examples/demos/LLM.yaml`, `LLM_memory.yaml`, `examples/experiments/vanilla_llm.yaml` | `benchmark`, `prompt`, `generation`, sometimes `memory` | Good for prompt + generation wiring. |
| RAG | `examples/demos/RAG.yaml`, `RAG_memory.yaml`, `RAG_web.yaml`, `examples/experiments/vanilla_rag.yaml`, `rag_full.yaml`, `rag_loop.yaml`, `rag_branch.yaml`, `rag_wow.yaml` | `benchmark`, `retriever`, `prompt`, `generation`, often `custom`, `evaluation`, `memory` | Core retrieval-augmented answer workflows. |
| Corpus and indexing | `build_text_corpus.yaml`, `build_image_corpus.yaml`, `build_mineru_corpus.yaml`, `corpus_chunk.yaml`, `corpus_index.yaml`, `milvus_index.yaml`, `bm25_index.yaml` | `corpus`, `retriever` | Prepares searchable corpora and vector/bm25 indexes. |
| Corpus search and deployment | `corpus_search.yaml`, `deploy_corpus_search.yaml`, `bm25_search.yaml`, `hybrid_search.yaml`, `corpus_rerank.yaml` | `benchmark`, `retriever`, sometimes `reranker`, `dense`, `bm25` | Focused retrieval flows and service-style search. |
| Evaluation | `evaluate_results.yaml`, `eval_trec.yaml`, `eval_trec_pvalue.yaml` | `benchmark`, `evaluation` | Compare predictions or retrieval runs. |
| Iterative reasoning | `ircot.yaml`, `search_r1.yaml`, `r1_searcher.yaml`, `search_o1.yaml`, `iterretgen.yaml`, `rankcot.yaml` | `benchmark`, `generation`, `retriever`, `prompt`, `custom`, `router`, `evaluation` | Useful when the task has explicit search/reason/answer phases. |
| Long-form research | `LightResearch.yaml`, `AgentCPM-Report.yaml`, `AgentCPM-Report_web.yaml`, `webnote.yaml`, `webnote_websearch.yaml` | `benchmark`, `generation`, `retriever`, `prompt`, `router`, `custom` | Multi-step report generation with loop/branch control. |
| Multimodal | `visrag.yaml`, `evisrag.yaml`, `multimodal_rag.yaml`, `vanilla_vlm.yaml` | `benchmark`, `retriever`, `prompt`, `generation`, `custom`, `evaluation` | Text+image or visual QA flows. |
| Chat/memory | `multiturn_chat.yaml`, `RAG_memory.yaml`, `LLM_memory.yaml` | `generation`, `memory`, sometimes `retriever` | Good for session state and memory sync debugging. |

## Recommended path for a new task

1. Start with the smallest workflow family that matches the user request.
2. Use the distilled server mix and DSL rules here; inspect a checkout's source
   pipeline only when the user explicitly asks for source-level evidence.
3. If the request needs a new backend or service, hand off to the servers or UI
   sub-skill after confirming the pipeline shape.

## Common cues

- If the task mentions benchmark data, use a workflow that starts with
  `benchmark.get_data`.
- If it mentions indexed corpora, look first at the corpus/index families.
- If it mentions report-style reasoning or iterative search, use the iterative
  reasoning or long-form research families.
- If it mentions `memory_*.json`, the pipeline likely belongs to the chat/memory
  family or the UI case-study flow.
