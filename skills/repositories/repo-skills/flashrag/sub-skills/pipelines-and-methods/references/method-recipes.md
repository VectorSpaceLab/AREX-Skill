# Method Recipes and Reproduction Planning

FlashRAG centralizes many method reproductions in an experiment-runner pattern: a base YAML config supplies global paths and defaults, and each method applies a small `config_dict` override before constructing a pipeline.

Use this page to plan a run without triggering model downloads or full benchmark execution.

## Safe planning workflow

1. Identify `method_name`, `dataset_name`, `split`, and intended `gpu_id` or CPU fallback.
2. Inspect the method row below for extra model/index/training-data requirements.
3. Validate the config with `skills/flashrag/sub-skills/pipelines-and-methods/scripts/validate_pipeline_config.py` before importing model-heavy components.
4. For a smoke test, set `test_sample_num` to a tiny number, `retrieval_topk` to 1-2, short generation tokens, and avoid full evaluation if not needed.
5. Only run the actual method after the user confirms model weights, corpora, indexes, and hardware are available.

## Experiment-runner interface

Typical command shape:

```bash
python run_exp.py --method_name METHOD --split test --dataset_name nq --gpu_id 0
```

The supported method keys in the runner include:

`naive`, `zero-shot`, `AAR-contriever`, `AAR-ANCE`, `llmlingua`, `recomp`, `selective-context`, `ret-robust`, `sure`, `replug`, `skr`, `selfrag`, `flare`, `iterretgen`, `ircot`, `trace`, `spring`, `adaptive`, `rqrag`, `r1-searcher`, `search-r1`, `autorefine`, `o2-searcher`, `rearag`, `corag`, and `simpledeepsearcher`.

## Method matrix

| Method key | Pipeline/component | Extra prerequisites | Cost/risk notes |
| --- | --- | --- | --- |
| `naive` | `SequentialPipeline.run` with normal RAG settings | Base retriever, corpus, index, generator | Despite the name, runner version performs retrieval. |
| `zero-shot` | `SequentialPipeline.naive_run` with no retrieval prompt | Generator only | Good baseline and cheap smoke test. |
| `AAR-contriever`, `AAR-ANCE` | `SequentialPipeline` with AAR retriever | AAR retriever checkpoint and matching index; pooling differs by model | Index must match retriever model. |
| `llmlingua` | `SequentialPipeline` with LongLLMLingua refiner | Llama2-7B-style refiner model and `llmlingua_config` | Refiner can be expensive; ensure `refiner_input_prompt_flag` matches intended behavior. |
| `recomp` | `SequentialPipeline` with RECOMP refiner | Dataset-specific abstractive compressor checkpoint when available | Check fallback checkpoint choices for unsupported datasets. |
| `selective-context` | `SequentialPipeline` with Selective Context refiner | GPT2-style refiner model and spaCy model/package availability | Requires extra NLP dependency setup. |
| `ret-robust` | `SelfAskPipeline` plus LoRA generator | Llama2-13B base and Ret-Robust LoRA | Set `single_hop` by dataset; multi-hop datasets should allow decomposition. |
| `sure` | `SuRePipeline` | Base RAG resources | Multiple generation passes per sample. |
| `replug` | `REPLUGPipeline` | REPLUG-specific model loading and document scores | Depends on logits processor support; GPU memory can be higher. |
| `skr` | `ConditionalPipeline` | SKR judger encoder and inference-time training data | Training data format must include questions and judgement labels. |
| `selfrag` | `SelfRAGPipeline` | Self-RAG checkpoint, vLLM framework, special control tokens | Requires logprobs/raw outputs; not a generic checkpoint. |
| `flare` | `FLAREPipeline` | Base RAG resources and generator scoring support | Active retrieval increases generation calls. |
| `iterretgen` | `IterativePipeline` | Base RAG resources | Repeats retrieval/generation for `iter_num` rounds. |
| `ircot` | `IRCOTPipeline` | Base RAG resources and IRCoT-style prompt examples | Multi-hop reasoning can be token-expensive. |
| `trace` | `SequentialPipeline` with `kg-trace` refiner | Few-shot triple extraction prompts and HF framework | Requires logits/refiner behavior; not vLLM-only. |
| `spring` | `SequentialPipeline` with virtual tokens | Virtual token embedding file and HF framework | Model/tokenizer compatibility is critical. |
| `adaptive` | `AdaptivePipeline` | Adaptive-RAG classifier/judger | Classifier checkpoint may not be official; report provenance. |
| `rqrag` | `RQRAGPipeline` | RQRAG generator checkpoint and vLLM | Long outputs; set small samples first. |
| `r1-searcher` | `ReasoningPipeline` | R1-Searcher checkpoint and vLLM | Requires strict query/answer tag format. |
| `search-r1` | `SearchR1Pipeline` | SearchR1 checkpoint and vLLM | Query parsing is tag-sensitive. |
| `autorefine` | `AutoRefinePipeline` | AutoRefine checkpoint and vLLM | Adds refinement steps after search. |
| `o2-searcher` | `O2SearcherPipeline` | O2-Searcher checkpoint and vLLM | Can emit multiple search queries per round. |
| `rearag` | `ReaRAGPipeline` | ReaRAG checkpoint and vLLM-style settings | Function/action parsing must be valid. |
| `corag` | `CoRAGPipeline` | CoRAG checkpoint, `task_desc`, vLLM | Choose `task_desc` based on dataset type. |
| `simpledeepsearcher` | `SimpleDeepSearcherPipeline` | SimpleDeepSearcher checkpoint and long context | Very long context; smoke-test with tiny samples. |

## Adaptive-RAG reproduction plan

Use this plan when asked to reproduce Adaptive-RAG but avoid expensive execution by default.

1. Confirm base resources: dataset split, retrieval corpus, E5 or chosen retriever model, matching index, and generator model.
2. Confirm Adaptive-RAG classifier availability and record whether the classifier is official or community-trained.
3. Prepare safe overrides: `method_name=adaptive`, `test_sample_num=5`, `retrieval_topk=1`, short `generation_params`, and a temporary `save_note`.
4. Run the validator with `--method adaptive --dry-run-plan`; fix missing `judger_name`, `judger_config.model_path`, generator, retriever, corpus, or index settings before execution.
5. If execution is approved, run only the small sample first and inspect `judge_result`, `retrieval_result`, and `pred` before scaling.
6. For full reproduction, restore benchmark settings such as the intended sample count, retrieval top-k, framework, and GPU assignment.

## Method-specific reminders

- `ret-robust` with `SelfAskPipeline` needs the `single_hop` decision aligned to dataset complexity. Single-hop QA can use `single_hop=True`; HotpotQA/2Wiki-style multi-hop QA generally requires `single_hop=False`.
- `selfrag` depends on special control tokens such as `[Retrieval]`, `[No Retrieval]`, relevance, utility, and support tokens; a normal Llama checkpoint is not enough.
- `REPLUGPipeline` asks the retriever for document scores; if the retriever cannot return scores, REPLUG planning is incomplete.
- `trace` and `spring` use HF-only behaviors in the reference settings; do not silently switch to vLLM.
- Reasoning/search methods usually require `framework: vllm`, long input lengths, and `skip_special_tokens: False` in generation settings.
