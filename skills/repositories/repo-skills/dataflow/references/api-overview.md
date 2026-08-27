# API Overview

## Purpose

Use this as the root public-surface map before opening a focused sub-skill reference. It summarizes the verified classes, CLI groups, and helper objects that the generated skill routes most often.

## Core abstractions

- `dataflow.core.operator.OperatorABC`
  - `run(self) -> None`
  - Implement `run(storage, input_*, output_*)` style parameters in concrete operators so pipeline key validation can track data flow.
- `dataflow.core.prompt.PromptABC`
- `dataflow.core.prompt.DIYPromptABC`
- `dataflow.core.prompt.prompt_restrict(*allowed_prompts)`
  - Adds `ALLOWED_PROMPTS` to the decorated class.
  - Runtime checks allow the whitelist plus any `DIYPromptABC` subclass.
- `dataflow.core.llm_serving.LLMServingABC`
  - `generate_from_input(user_inputs, system_prompt)`
  - `start_serving()`
  - `cleanup()`
  - `load_model(model_name_or_path, **kwargs)` is optional and may raise `NotImplementedError` in subclasses.

## Pipeline objects

- `PipelineABC`
  - `compile()` builds operator nodes, validates key flow, and installs the compiled forward path.
  - `draw_graph(port=0, hide_no_changed_keys=True)` renders a graph when `pyvis` is installed.
- `BatchedPipelineABC`
  - adds batch-oriented compiled forward behavior with `resume_step`, `batch_size`, and `resume_from_last`.
- `StreamBatchedPipelineABC`
  - extends batched behavior with chunk streaming via storage support.
- `dataflow.pipeline.nodes.OperatorNode`
  - internal structure that records `input_*` and `output_*` keys for compile-time validation.

## Storage objects

- `FileStorage(first_entry_file_name, cache_path='./cache', file_name_prefix='dataflow_cache_step', cache_type='jsonl')`
- `LazyFileStorage(first_entry_file_name, cache_path='./cache', file_name_prefix='dataflow_cache_step', cache_type='jsonl', save_on_exit=True, flush_all_steps=False)`
- `DummyStorage(cache_path=None, file_name_prefix=None, cache_type=None)`
- `BatchedFileStorage(...)`
- `StreamBatchedFileStorage(...)`
- `MyScaleDBStorage(db_config, pipeline_id=None, input_task_id=None, output_task_id=None, parent_pipeline_id=None, page_size=10000, page_num=0)`

Common storage behavior:

- `step()` advances the step counter and returns a shallow copy for the operator call.
- Step 0 reads the first input source.
- Later steps write to cached files named from the step index.
- Supported local formats include JSON, JSONL, CSV, Parquet, Pickle, and XLSX behavior through the storage implementation.
- `hf:` and `ms:` prefixes are remote dataset sources and are not offline-safe.

## CLI groups

Top-level command groups discovered from help output:

- `env`
- `chat`
- `webui`
- `init`
- `eval`
- `pdf2model`
- `text2model`

Selected subcommands:

- `init repo`
- `eval init`
- `eval api`
- `eval local`
- `pdf2model init`
- `pdf2model train`
- `text2model init`
- `text2model train`

## Serving helpers

Frequently used constructors:

- `APILLMServing_request(api_url='https://api.openai.com/v1/chat/completions', key_name_of_api_key='DF_API_KEY', model_name='gpt-4o', temperature=0.0, max_workers=10, max_retries=5, connect_timeout=10.0, read_timeout=120.0, **configs)`
- `LiteLLMServing(...)`
- `LocalModelLLMServing_vllm(...)`
- `LocalModelLLMServing_sglang(...)`
- `LocalHostLLMAPIServing_vllm(...)`
- `LocalModelLALMServing_vllm(...)`
- `LocalVLMServing_vllm(...)`
- `APIVLMServing_openai(...)`
- `APIGoogleVertexAIServing(...)`
- `PerspectiveAPIServing(...)`
- `LocalEmbeddingServing(...)`
- `LightRAGServing(...)`

## RayOrch helper

- `RayAcceleratedOperator(op_cls, replicas=1, num_gpus_per_replica=0.0, env=None)`
- The wrapper is for deterministic row-wise operators that can be accelerated without changing the surrounding pipeline contract.

## Where the deep details live

- Pipeline and storage semantics: `sub-skills/pipeline-foundations/references/`
- CLI and serving detail: `sub-skills/serving-cli/references/`
- Text workflow operators and data shapes: `sub-skills/text-workflows/references/`
- Document / PDF / RAG detail: `sub-skills/document-vision-rag/references/`
- Ray acceleration detail: `sub-skills/rayorch-acceleration/references/`
