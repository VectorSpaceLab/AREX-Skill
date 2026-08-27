# FlashRAG Capability Map

## Purpose

Use this map when a task spans several FlashRAG components or when deciding which sub-skill owns a workflow, source artifact, or failure mode.

## Ownership Matrix

| Capability | Public entry points | Primary evidence | Skill owner |
| --- | --- | --- | --- |
| Config construction and override priority | `flashrag.config.Config` | `flashrag/config/config.py`, `flashrag/config/basic_config.yaml`, configuration docs | `data-and-config` |
| Dataset rows and JSONL fixtures | `flashrag.dataset.Item`, `flashrag.dataset.Dataset`, dataset utils | dataset source, quick-start dataset/corpus fixtures | `data-and-config` |
| Corpus validation and chunking | corpus JSONL, chunk/preprocess scripts | indexing docs, corpus scripts | `retrieval-and-indexing` |
| BM25 and dense index building | `python -m flashrag.retriever.index_builder`, `Index_Builder` | retriever source, index docs, `scripts/build_index.sh` | `retrieval-and-indexing` |
| Retriever and reranker objects | `get_retriever`, `get_reranker`, `BM25Retriever`, `DenseRetriever`, `MultiRetrieverRouter` | retriever/reranker source and component docs | `retrieval-and-indexing` |
| Text and multimodal generators | `get_generator`, `BaseGenerator`, `HFCausalLMGenerator`, `VLLMGenerator`, `OpenaiGenerator`, multimodal generator classes | generator source and docs | `generation-and-refinement` |
| Prompts, refiners, judgers | `PromptTemplate`, `get_refiner`, `get_judger`, refiner/judger classes | prompt/refiner/judger source and component docs | `generation-and-refinement` |
| Standard, adaptive, active, branching pipelines | `SequentialPipeline`, `ConditionalPipeline`, `AdaptivePipeline`, `SelfRAGPipeline`, `FLAREPipeline`, `REPLUGPipeline` | pipeline source, quick-start examples, reproduce docs | `pipelines-and-methods` |
| Reasoning and multimodal pipelines | `ReasoningPipeline`, `SearchR1Pipeline`, `ReaRAGPipeline`, `CoRAGPipeline`, `MMSequentialPipeline` | reasoning/multimodal source and examples | `pipelines-and-methods` |
| Metrics and prediction parsing | `Evaluator`, metric classes, `pred_parse` helpers | evaluator source, config docs | `evaluation-and-webui` |
| WebUI chat/evaluate flows | `webui/interface.py`, UI components/configs | WebUI docs and modules | `evaluation-and-webui` |

## Cross-Skill Workflows

- **Build and run a basic RAG demo**: validate config/data in `data-and-config`, prepare corpus/index in `retrieval-and-indexing`, choose generator in `generation-and-refinement`, then execute with `pipelines-and-methods`.
- **Reproduce a method**: start in `pipelines-and-methods`, then follow links to retrieval, generation/refinement, and evaluation as prerequisites arise.
- **Diagnose bad answers**: use the root troubleshooting page, then inspect retrieval/index quality, generator prompt/backend settings, pipeline control flow, and metric choice in that order.
- **Launch or debug WebUI**: validate config and component prerequisites first, then use `evaluation-and-webui` for UI-specific routes.

## Source Script Decisions

| Source artifact | Runtime replacement | Owner | Decision |
| --- | --- | --- | --- |
| `scripts/chunk_doc_corpus.py` | corpus validation/data-preparation references plus `validate_corpus_jsonl.py` | `retrieval-and-indexing` | adapted/distilled; full chunking can rewrite large files |
| `scripts/preprocess_wiki.py` | data-preparation reference | `retrieval-and-indexing` | reference-only; external dumps and large writes |
| `scripts/build_index.sh` | `inspect_index_builder_args.py` plus indexing workflow commands | `retrieval-and-indexing` | wrapped/adapted; source script had environment-specific paths |
| quick-start examples | config and pipeline validators plus recipe references | `pipelines-and-methods` | adapted; full runs can load models/indexes |
| `examples/run_refiner.py` | refiner references and generation config inspector | `generation-and-refinement` | adapted/reference; model-dependent execution |
| method reproduction examples | method recipe references and pipeline validator | `pipelines-and-methods` | reference-only for large benchmark execution |
| WebUI modules | WebUI reference and environment checks | `evaluation-and-webui` | reference/wrap; service launch is user-approved runtime action |
