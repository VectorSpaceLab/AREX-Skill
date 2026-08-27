# UltraRAG Server API Reference

## Purpose

Read this when you need the verified server-level signatures, output keys, or
module responsibilities for UltraRAG's MCP servers.

## Shared wrapper

### `ultrarag.server.UltraRAG_MCP_Server`

- Extends `FastMCP`.
- Records tool and prompt metadata so `build` can generate `server.yaml`.
- Registers a `build` tool automatically.
- Used by every server module in `servers/`.

## Benchmark server

### `servers/benchmark/src/benchmark.py`

- `get_data(benchmark: Dict[str, Any]) -> Dict[str, List[Any]]`
- Registered as a tool with output `q_ls,gt_ls`.
- Loads benchmark datasets from the configured path and supports key mapping,
  shuffling, and truncation.

## Retriever server

### `servers/retriever/src/retriever.py`

`Retriever` registers the public tools below.

| Tool | Signature | Output |
| --- | --- | --- |
| `retriever_init` | `(model_name_or_path, backend_configs, batch_size, corpus_path, gpu_ids=None, is_multimodal=False, backend='sentence_transformers', index_backend='faiss', index_backend_configs=None, is_demo=False, collection_name='')` | `None` |
| `retriever_embed` | `(embedding_path=None, overwrite=False, is_multimodal=False)` | `None` |
| `retriever_index` | `(embedding_path, overwrite=False, collection_name='', corpus_path='')` | `None` |
| `retriever_search` | `(query_list, top_k=5, query_instruction='', collection_name='')` | `ret_psg` |
| `retriever_batch_search` | `(batch_query_list, top_k=5, query_instruction='', collection_name='')` | `ret_psg_ls` |
| `retriever_project_memory_search` | `(query_list, top_k=5, query_instruction='', current_user_id='')` | `project_memory_content` |
| `retriever_deploy_search` | `(retriever_url, query_list, top_k=5, query_instruction='')` | `ret_psg` |
| `bm25_index` | `(overwrite=False)` | `None` |
| `bm25_search` | `(query_list, top_k=5)` | `ret_psg` |
| `retriever_websearch` | `(query_list, top_k=5, retrieve_thread_num=1, websearch_backend='tavily', websearch_backend_configs=None)` | `ret_psg` |
| `retriever_batch_websearch` | `(batch_query_list, top_k=5, retrieve_thread_num=1, websearch_backend='tavily', websearch_backend_configs=None)` | `ret_psg_ls` |

### Retriever backend knobs

- `backend`: `sentence_transformers`, `infinity`, `openai`, `bm25`
- `index_backend`: `faiss`, `milvus`
- `websearch_backend`: `tavily`, `exa`, `zhipuai`

## Generation server

### `servers/generation/src/generation.py`

`Generation` registers the public tools below.

| Tool | Signature | Output |
| --- | --- | --- |
| `generation_init` | `(backend_configs, sampling_params, extra_params=None, backend='vllm')` | `None` |
| `generate` | `(prompt_ls, system_prompt='')` | `ans_ls` |
| `multiturn_generate` | `(messages, system_prompt='')` | `ans_ls` |
| `multimodal_generate` | `(multimodal_path, prompt_ls, system_prompt='', image_tag=None)` | `ans_ls` |
| `vllm_shutdown` | `()` | `None` |

### Generation backend knobs

- `backend`: `vllm`, `openai`, `hf`
- `openai` backend is used for hosted API calls.
- `vllm` backend is the GPU serving path.
- `hf` backend is the local Hugging Face path.

## Corpus server

### `servers/corpus/src/corpus.py`

| Tool | Signature | Output |
| --- | --- | --- |
| `build_text_corpus` | `(parse_file_path, text_corpus_save_path)` | `None` |
| `build_image_corpus` | `(parse_file_path, image_corpus_save_path)` | `None` |
| `mineru_parse` | `(parse_file_path, mineru_dir, mineru_extra_params=None)` | `None` |
| `build_mineru_corpus` | `(mineru_dir, parse_file_path, text_corpus_save_path, image_corpus_save_path)` | `None` |
| `chunk_documents` | `(raw_chunk_path, chunk_backend_configs, chunk_backend='token', tokenizer_or_token_counter='character', chunk_size=256, chunk_path=None, use_title=True)` | `None` |

## Evaluation server

### `servers/evaluation/src/evaluation.py`

| Tool | Signature | Output |
| --- | --- | --- |
| `evaluate` | `(pred_ls, gt_ls, metrics, save_path)` | `eval_res` |
| `evaluate_trec` | `(run_path, qrels_path, metrics, ks, save_path)` | `eval_res` |
| `evaluate_trec_pvalue` | `(run_new_path, run_old_path, qrels_path, metrics, ks, n_resamples, save_path)` | `eval_res` |

Evaluation metrics include QA metrics such as `acc`, `f1`, `em`, `coverem`,
`stringem`, `rouge-1`, `rouge-2`, `rouge-l`, plus retrieval metrics such as
`mrr`, `map`, `recall`, `ndcg`, and `precision`.

## Memory server

### `servers/memory/src/memory.py`

- `get_global_memory(user_id='default') -> Dict[str, str]`
- `save_memory(user_id, q_ls, ans_ls)`

Outputs are `global_memory_content` and `current_user_id` for the getter, and
no output for the saver.

## Prompt server

### `servers/prompt/src/prompt.py`

All prompt functions return `PromptMessage` lists and output `prompt_ls`.

| Prompt | Signature summary |
| --- | --- |
| `qa_boxed` | `(q_ls, template)` |
| `qa_with_memory` | `(q_ls, global_memory_content, project_memory_content, template)` |
| `qa_boxed_multiple_choice` | `(q_ls, choices_ls, template)` |
| `qa_rag_boxed` | `(q_ls, ret_psg, template)` |
| `qa_rag_with_memory` | `(q_ls, global_memory_content, project_memory_content, ret_psg, template)` |
| `qa_rag_boxed_multiple_choice` | `(q_ls, choices_ls, ret_psg, template)` |
| `RankCoT_kr` | `(q_ls, ret_psg, template)` |
| `RankCoT_qa` | `(q_ls, kr_ls, template)` |
| `ircot_next_prompt` | `(memory_q_ls, memory_ret_psg, template)` |
| `webnote_init_page` | `(q_ls, plan_ls, template)` |
| `webnote_gen_plan` | `(q_ls, template)` |
| `webnote_gen_subq` | `(q_ls, plan_ls, page_ls, template)` |
| `webnote_fill_page` | `(q_ls, plan_ls, page_ls, subq_ls, psg_ls, template)` |
| `webnote_gen_answer` | `(q_ls, page_ls, template)` |
| `search_r1_gen` | `(prompt_ls, ans_ls, ret_psg, template)` |
| `r1_searcher_gen` | `(prompt_ls, ans_ls, ret_psg, template)` |
| `search_o1_init` | `(q_ls, template)` |
| `search_o1_reasoning_indocument` | `(extract_query_list, ret_psg, total_reason_list, template)` |
| `search_o1_insert` | `(q_ls, total_subq_list, total_final_info_list, template)` |
| `gen_subq` | `(q_ls, ret_psg, template)` |
| `check_passages` | `(q_ls, ret_psg, template)` |
| `evisrag_vqa` | `(q_ls, ret_psg, template)` |
| `surveycpm_search` | `(instruction_ls, survey_ls, cursor_ls, surveycpm_search_template)` |
| `surveycpm_init_plan` | `(instruction_ls, retrieved_info_ls, surveycpm_init_plan_template)` |
| `surveycpm_write` | `(instruction_ls, survey_ls, cursor_ls, retrieved_info_ls, surveycpm_write_template)` |
| `surveycpm_extend_plan` | `(instruction_ls, survey_ls, surveycpm_extend_plan_template)` |

## Custom server

### `servers/custom/src/custom.py`

The custom server contains several workflow families:

- **Citation helpers**: `assign_citation_ids`, `init_citation_registry`,
  `assign_citation_ids_stateful`, `surveycpm_init_citation_registry`
- **RAG extractors**: `output_extract_from_boxed`, `merge_passages`,
  `evisrag_output_extract_from_special`
- **IRCoT / search-R1 helpers**: `search_r1_query_extract`,
  `r1_searcher_query_extract`, `ircot_get_first_sent`, `ircot_extract_ans`
- **Search-o1 helpers**: `search_o1_init_list`, `search_o1_combine_list`,
  `search_o1_query_extract`, `search_o1_reasoning_extract`,
  `search_o1_extract_final_information`, `search_o1_combine_final_information`
- **SurveyCPM tools**: `surveycpm_process_passages_with_citation`,
  `surveycpm_parse_response`, `surveycpm_validate_action`,
  `surveycpm_update_position`, `surveycpm_get_position`,
  `surveycpm_state_init`, `surveycpm_parse_search_response`,
  `surveycpm_process_passages`, `surveycpm_after_init_plan`,
  `surveycpm_after_write`, `surveycpm_after_extend`, `surveycpm_update_state`,
  `surveycpm_check_completion`, `surveycpm_format_output`

### Common output keys

- Search/extraction helpers usually return `q_ls`, `ans_ls`, `pred_ls`, or
  family-specific list names.
- SurveyCPM helpers often return `state_ls`, `cursor_ls`, `survey_ls`,
  `step_ls`, `extend_time_ls`, `extend_result_ls`, `retrieved_info_ls`, or
  `parsed_ls`.

## Build metadata behavior

When a server module registers tools or prompts through `UltraRAG_MCP_Server`,
`build` can derive the corresponding `server.yaml` entries automatically.
That is why the tool and prompt names in this file matter to pipeline authors.
