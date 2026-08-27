# Pipeline Troubleshooting

This page covers FlashRAG pipeline and method failures. Keep low-level schema, index-building, generator internals, and metric/UI debugging in their dedicated skill areas.

## Fast triage order

1. Confirm the selected pipeline matches the requested method and modality.
2. Validate required config keys with `skills/flashrag/sub-skills/pipelines-and-methods/scripts/validate_pipeline_config.py`.
3. Run the smallest safe sample: tiny `test_sample_num`, low `retrieval_topk`, short output tokens, and no full benchmark scaling.
4. Inspect intermediate outputs: `retrieval_result`, `prompt`, `pred`, `judge_result`, `finish_reason`, and method-specific fields.
5. Change one layer at a time: retriever/index, prompt/template, generator settings, then evaluation.

## Common symptoms

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Pipeline constructor fails while loading retriever | Missing `retrieval_method`, `corpus_path`, `index_path`, or model path | Validate config; ensure retriever and index were prepared together. |
| Generator loads unexpectedly or tries to download weights | `model2path` or `generator_model_path` points to a remote model or missing local value | Ask the user to confirm downloads; dry-run config only by default. |
| `SequentialPipeline.run` has no useful documents | Wrong corpus/index pairing, low-quality retrieval method, wrong language, or stale cache | Check retriever/index compatibility and try a single `retriever.search` after approval. |
| `naive_run` works but RAG run fails | Retrieval/index dependency is incomplete | Fix retrieval settings before debugging generation. |
| `ConditionalPipeline` routes all items one way | Judger config/training data is missing or mismatched | Inspect `judge_result`; verify SKR/adaptive classifier prerequisites. |
| Adaptive-RAG crashes on unknown symbol | Classifier output is not one of expected `A`, `B`, `C` labels | Check judger model and parsing; do not assume arbitrary classifiers work. |
| SelfAsk gives poor multi-hop answers | `single_hop` is wrong for the dataset | Use single-hop for simple QA and multi-hop mode for HotpotQA/2Wiki-style tasks. |
| Self-RAG errors on logprobs or tokens | Generic model or non-vLLM path lacks required Self-RAG control-token/logprob behavior | Use a Self-RAG checkpoint with compatible framework settings. |
| REPLUG fails in generation | REPLUG model wrapper or logits processor is unsupported | Verify REPLUG-specific model loading and document score availability. |
| SuRe is very slow | It performs candidate, summary, validation, and ranking generations | Smoke-test on 1-2 samples and short token limits. |
| Reasoning pipeline stops without retrieval | Model did not emit the expected query tags | Inspect the prompt and stop tokens; use the method-specific checkpoint. |
| Reasoning pipeline reaches max retrieval | Malformed tags, repeated queries, or insufficient evidence | Inspect `retrieval_results` by step before increasing max rounds. |
| Multimodal run fails before generation | Missing multimodal extras, image columns, CLIP indexes, or unsupported generator | Validate multimodal config and run no-retrieval mode first. |
| Output/cache paths collide | Reused `save_note`, `save_dir`, or cache path | Use unique `save_note` for each experiment and separate cache paths. |

## vLLM and framework issues

Some FlashRAG methods are planned around `framework: vllm`, including Self-RAG and several reasoning/search methods. Others require HF behavior, such as Trace or Spring in the reference recipes. Do not switch frameworks to make a config “look simpler” unless the method supports that framework.

Check:

- `framework` is appropriate for the method.
- `generation_params` uses the parameter names expected by the selected framework (`max_tokens` vs `max_new_tokens` can differ by path).
- `skip_special_tokens` is not hiding method-control tokens required for parsing.
- GPU assignment and memory are realistic for the selected generator.

## Cache and output paths

- `save_retrieval_cache=True` writes retriever cache on evaluation; ensure cache path is writable and method-specific.
- `use_retrieval_cache=True` can mask retrieval/index mistakes by returning old results; disable it when debugging retrieval changes.
- `save_dir` and `save_note` determine output organization; use unique notes for reproductions.
- If `save_intermediate_data=True`, inspect saved prompts and retrieval results for prompt/reference formatting errors.

## Reasoning query parsing checklist

- Query begin/end tokens in the prompt match the pipeline defaults or constructor overrides.
- Stop tokens include the query end token, otherwise generation may continue past the query boundary.
- The model checkpoint was trained or prompted to emit the expected tags.
- Parsed query text is non-empty and contains a single intended search query where required.
- Final answer tags match the pipeline’s `begin_of_answer_token` and `end_of_answer_token`.

## Multimodal checklist

- Dataset items contain the modality fields used by the prompt template.
- `perform_modality_dict` requests only modalities supported by configured retrievers.
- `multimodal_index_path_dict` includes entries for requested target modalities.
- CLIP/BM25 retrievers point to corpora with matching row ids/content.
- The generator can accept the prompt/template output and image references expected by the dataset.

## When to skip instead of run

Skip expensive execution and return a prerequisite plan when any of these are missing:

- Large generator or classifier checkpoint is not available.
- Retrieval corpus or index is missing or known incompatible.
- vLLM is required but not installed or no suitable GPU is available.
- Multimodal task lacks image data, CLIP index, or multimodal generator support.
- The user only asked for planning, validation, or reproduction instructions.
