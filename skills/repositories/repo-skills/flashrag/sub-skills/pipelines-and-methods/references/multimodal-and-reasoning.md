# Multimodal, Reasoning, Active, and Branching Pipelines

Use this page when the requested workflow goes beyond a plain retrieve-then-generate run.

## Multimodal RAG

`MMSequentialPipeline` runs multimodal retrieval and generation over dataset items that may include text questions, text fields, and images. It uses a multimodal prompt template by default, and task-specific prompt templates can be used for datasets such as MathVista or Gaokao-MM.

### Multimodal config checklist

- `dataset_name` is one of the intended multimodal datasets, such as `mathvista`, `gaokao_mm`, or `mmqa`.
- `data_dir` points to multimodal dataset files with expected text/image columns.
- `generator_model` supports the input modality and prompt template.
- `use_multi_retriever=True` when combining text and image retrievers.
- `multi_retriever_setting.merge_method` is set, commonly `concat`.
- Each retriever in `multi_retriever_setting.retriever_list` has compatible `retrieval_method`, `corpus_path`, index path, and `retrieval_topk`.
- CLIP-style retrievers use `multimodal_index_path_dict` with the modalities they retrieve, commonly `image` and `text`.
- Hardware supports the generator and image/text retrievers; multimodal generators often require more memory than text-only smoke tests.

### Multimodal run modes

- No retrieval: instantiate `MMSequentialPipeline(config, prompt_template=...)` and call `naive_run(dataset)`.
- Full multimodal retrieval: call `run(dataset)` with the default modality map.
- Text-only retrieval for a multimodal task: call `run(dataset, perform_modality_dict={'text': ['text']})`.
- Custom modality routing: pass a map such as `{'text': ['text', 'image'], 'image': ['image']}` only when retrievers support those query/target modalities.

### Safe multimodal request routing

When a user asks for a multimodal RAG run:

1. Ask or infer the dataset (`mathvista`, `gaokao_mm`, `mmqa`, or custom).
2. Check whether requested mode is `no-ret` or retrieval-enabled.
3. Validate multimodal retriever settings and index paths; do not build indexes unless requested.
4. Check generator modality support and GPU/memory expectations.
5. Run `validate_pipeline_config.py --method mmqa --multimodal --dry-run-plan` or the matching dataset method name before execution.
6. If dependencies are incomplete, provide a skip-expensive plan listing missing weights, indexes, and extras.

## Reasoning/search pipeline planning

Reasoning pipelines repeatedly generate an action/query, retrieve documents, append observations, and continue until an answer appears or a max retrieval count is reached.

| Pipeline | Best fit | Watchpoints |
| --- | --- | --- |
| `ReasoningPipeline` | R1-style answer/search loop | Requires `<|begin_of_query|>` and `<answer>` tags; malformed tags finish early or error. |
| `SearchR1Pipeline` | Search-R1 checkpoints | Stop tokens include `</search>` and `</answer>` variants. |
| `AutoRefinePipeline` | Search plus document refinement | Model must follow `<refine>` and `<answer>` conventions. |
| `O2SearcherPipeline` | Multiple queries per search action | Parses `<query>` tags inside `<search>`; empty parse triggers repair. |
| `ReaRAGPipeline` | Agent-like function calls | Requires valid function/action blocks and supports `search` or `finish`. |
| `CoRAGPipeline` | Controlled subquery/intermediate/final answer workflow | Requires dataset-specific `task_desc`. |
| `SimpleDeepSearcherPipeline` | Long-context repeated search | Requires long `generator_max_input_len`; use tiny sample counts. |

Reasoning smoke tests should cap `max_retrieval_num` or method-specific max iterations, set `test_sample_num` low, and inspect intermediate fields before evaluating metrics.

## Active and branching workflows

- `IterativePipeline`: choose when the generated answer should inform the next retrieval query. Cost scales with `iter_num`.
- `SelfRAGPipeline`: choose only with a Self-RAG checkpoint and vLLM logprob support. A generic generator will not emit the expected control tokens reliably.
- `FLAREPipeline`: choose for active retrieval based on generation uncertainty; verify that generator probability/scoring APIs are available.
- `SelfAskPipeline`: choose for decomposing a question into subquestions; set `single_hop` according to dataset complexity.
- `IRCOTPipeline`: choose for interleaved retrieval and reasoning over multi-hop QA.
- `REPLUGPipeline`: choose when per-document prompts should be combined with retrieval scores at generation time.
- `SuRePipeline`: choose when candidate generation, summarization, validation, and ranking are desired.

## Reasoning failure signs

- `finish_reason` says max retrieval reached: increase max rounds only after checking whether the model followed query/answer tags.
- `retrieval_results` is empty: parsed query list may be empty, retrieval config may be incomplete, or cache/index paths may be wrong.
- `pred` contains raw tags: prediction postprocessing may not match the selected method.
- Output is a normal free-form answer when a query was expected: prompt template or checkpoint does not enforce the method’s action format.
- Retrieval repeatedly searches the same phrase: add query de-duplication in custom code or lower max rounds for smoke tests.
