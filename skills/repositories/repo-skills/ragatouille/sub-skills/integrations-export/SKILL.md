---
name: integrations-export
description: "Integrate RAGatouille with LangChain or LlamaIndex-style pipelines
  and plan Hugging Face or Vespa exports safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RAGatouille Integrations and Export

Use this sub-skill when a task asks to connect RAGatouille to another RAG framework, expose an indexed or reranking model through LangChain adapters, load documents through LlamaIndex/LlamaHub-style loaders, or prepare a model export handoff.

## Route Here For

- LangChain adapters: `RAGPretrainedModel.as_langchain_retriever`, `as_langchain_document_compressor`, `RAGatouilleLangChainRetriever`, and `RAGatouilleLangChainCompressor`.
- LlamaIndex/LlamaHub-style loader patterns that turn external loader documents into strings for RAGatouille indexing.
- Export planning with `export_to_huggingface_hub` and `export_to_vespa_onnx`, including auth, repo naming, optional ONNX generation, and no-upload dry-run checks.
- Compatibility checks for legacy `langchain` imports, `langchain_core`, `llama_index`, `huggingface_hub`, `onnx`, and credential/network side effects.

## Route Away

- Use `../pretrained-indexing-search/SKILL.md` for loading checkpoints, building/updating indexes, metadata indexing, and `search` result schemas.
- Use `../index-free-reranking/SKILL.md` for in-memory `rerank`, `encode`, `search_encoded_docs`, and result-shape details behind compressor behavior.
- Use `../training-data-finetuning/SKILL.md` for training, synthetic training data, and checkpoint creation before export.

## Start Here

1. From this sub-skill directory, run the bundled compatibility checker before debugging framework wiring:
   `python scripts/check_integration_imports.py --json`
2. Read `references/api-reference.md` for exact adapter and export signatures.
3. Read `references/workflows.md` for framework recipes and safe export handoffs.
4. Read `references/troubleshooting.md` when imports, loaders, auth, uploads, tokenizer, or ONNX conversion fail.

## Safety Defaults

- Do not call `from_pretrained`, `from_index`, loader APIs, `export_to_huggingface_hub`, or `export_to_vespa_onnx` during lightweight verification unless the user explicitly approves model loads, network calls, local checkpoint reads, or uploads.
- Treat LlamaHub/LlamaIndex loaders, Hugging Face Hub uploads, OpenAI/instructor-style examples, and Semantic Scholar/PubMed/PDF loaders as external-network or credential-bound unless proven otherwise.
- Keep credentials in environment variables or the target service login state; never paste API tokens into notebooks, scripts, or skill content.
