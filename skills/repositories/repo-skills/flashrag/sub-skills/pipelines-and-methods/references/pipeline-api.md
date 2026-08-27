# Pipeline API Reference

FlashRAG pipelines combine `Config`, datasets, prompt templates, retrievers, generators, refiners, judgers, and evaluators into end-to-end RAG flows. Most text pipelines inherit from `BasicPipeline`; multimodal pipelines inherit from `BasicMultiModalPipeline`.

## Common lifecycle

1. Create a `Config` from a YAML file and/or `config_dict` overrides.
2. Load a dataset split with `get_dataset(config)`.
3. Optionally create a `PromptTemplate` or modality-specific prompt template.
4. Instantiate a pipeline with the config and optional injected retriever/generator/template.
5. Call `pipeline.run(dataset, do_eval=...)` or a specialized method such as `naive_run`.
6. Inspect dataset outputs such as `retrieval_result`, `prompt`, `pred`, and method-specific intermediate fields.

## Core text pipelines

| Pipeline | Best for | Key behavior | Required components |
| --- | --- | --- | --- |
| `BasicPipeline` | Custom pipeline base class | Stores `config`, `device`, `Evaluator`, `PromptTemplate`, and retrieval cache flag | Config with `device`, evaluation, and cache defaults |
| `SequentialPipeline` | Standard retrieve-then-generate RAG | `batch_search` over `dataset.question`, formats retrieved docs into prompts, optionally runs a refiner, then generates predictions | Retriever, generator, corpus/index or retrieval cache |
| `SequentialPipeline.naive_run` | Zero-shot/no-retrieval baseline | Builds prompts from questions only and generates predictions | Generator only; retrieval config may still be present in `Config` |
| `ConditionalPipeline` | SKR-like retrieve-or-not decisions | Uses `judger.judge(dataset)`, routes positive items through `SequentialPipeline.run` and negative items through `naive_run` | Judger, retriever, generator |
| `AdaptivePipeline` | Adaptive-RAG query routing | Classifies each item into no-RAG, single-hop sequential RAG, or multi-hop `IRCOTPipeline` | Adaptive judger/classifier, retriever, generator |

Important outputs:

- `retrieval_result`: top-k documents used for RAG; present for retrieval pipelines.
- `prompt`: final prompts sent to the generator.
- `pred`: generated prediction used by evaluation.
- `judge_result`: conditional/adaptive routing decision.
- `refine_result`: refined document text when a refiner runs before generation.

## Active and branching pipelines

| Pipeline | Control flow | Notes |
| --- | --- | --- |
| `IterativePipeline` | Repeats retrieval and generation for `iter_num` rounds | Later retrieval queries append prior generated output to the original question. Final `pred` is the last generation. |
| `SelfRAGPipeline` | Uses Self-RAG control tokens to decide retrieval and rank evidence paths | Expects a Self-RAG checkpoint, special tokens, logprobs, and vLLM-style raw outputs for adaptive retrieval. |
| `FLAREPipeline` | Active retrieval while generation confidence is uncertain | Use for FLARE reproduction; check generator scoring/logprob support. |
| `SelfAskPipeline` | Iterative self-ask decomposition | Set `single_hop` carefully: simple QA often uses single-hop; HotpotQA/2Wiki-style tasks often need multi-hop decomposition. |
| `IRCOTPipeline` | Interleaves retrieval with chain-of-thought style intermediate reasoning | Good for multi-hop QA; recipes often cap iterations for cost. |
| `REPLUGPipeline` | Branches one prompt per retrieved document and combines logits with document scores | Loads REPLUG-specific model wrapper; depends on logits processor support. |
| `SuRePipeline` | Generates candidates, creates candidate-conditioned summaries, validates/ranks them | Uses multiple generator calls per item; expensive at large scale. |

## Reasoning/search pipelines

| Pipeline | Query/action format | Typical method name | Planning notes |
| --- | --- | --- | --- |
| `ReasoningPipeline` | `<|begin_of_query|>...<|end_of_query|>` and `<answer>...</answer>` | `r1-searcher` style base | Stops on query or answer tags; fails closed after `max_retrieval_num`. |
| `SearchR1Pipeline` | `<search>...</search>`, `<information>...</information>`, `<answer>...</answer>` | `search-r1` | Uses search-tag stop tokens; retrieved docs are formatted as numbered docs. |
| `AutoRefinePipeline` | `<search>`, `<documents>`, `<refine>`, `<answer>` | `autorefine` | Adds refinement prompt contract after each search. |
| `O2SearcherPipeline` | `<search><query>...</query></search>` and `<learnings>` | `o2-searcher` | Can issue multiple queries per round; invalid format triggers repair prompt. |
| `ReaRAGPipeline` | Function-call-like `search` / `finish` actions in fenced blocks | `rearag` | Uses agent action parsing, observation turns, and a final short-answer extraction pass. |
| `CoRAGPipeline` | Generates subqueries and intermediate/final answers | `corag` | Requires `task_desc` in config; suited to controllable multi-hop reasoning. |
| `SimpleDeepSearcherPipeline` | `<|begin_search_query|>...<|end_search_query|>` | `simpledeepsearcher` | Long context settings and repeated searches can be costly. |

Reasoning pipelines are sensitive to prompt-token contracts. When a model emits malformed tags, inspect `finish_reason`, `retrieval_results`, and the accumulated `prompt` before changing retrieval settings.

## Multimodal pipeline

| Pipeline | Best for | Key behavior |
| --- | --- | --- |
| `BasicMultiModalPipeline` | Base class for multimodal RAG | Uses `MMPromptTemplate` by default and `Evaluator`. |
| `MMSequentialPipeline` | Text/image retrieval followed by multimodal generation | Retrieves over configured modalities, merges results per sample, builds multimodal prompts, and generates predictions. |
| `MMSequentialPipeline.naive_run` | Multimodal no-retrieval baseline | Builds prompts directly from multimodal dataset items. |

`MMSequentialPipeline.run` accepts `perform_modality_dict`, defaulting to text-to-text and image-to-image retrieval: `{'text': ['text'], 'image': ['image']}`. You can restrict retrieval, for example text-only retrieval for a multimodal dataset, by passing `{'text': ['text']}`.

## Minimal standard RAG skeleton

```python
from flashrag.config import Config
from flashrag.utils import get_dataset
from flashrag.pipeline import SequentialPipeline
from flashrag.prompt import PromptTemplate

config = Config("my_config.yaml", config_dict={
    "dataset_name": "nq",
    "split": ["test"],
    "test_sample_num": 10,
    "retrieval_topk": 1,
    "save_intermediate_data": True,
})
dataset = get_dataset(config)["test"]
prompt_template = PromptTemplate(
    config,
    system_prompt="Answer the question based on the given document. Only give me the answer.\n{reference}",
    user_prompt="Question: {question}\nAnswer:",
)
pipeline = SequentialPipeline(config, prompt_template=prompt_template)
result = pipeline.run(dataset, do_eval=False)
```

## Choosing by task

- Need a plain baseline: `SequentialPipeline.naive_run` or `SequentialPipeline.run`.
- Need retrieve-or-not classification: `ConditionalPipeline` for SKR-style binary routing, `AdaptivePipeline` for Adaptive-RAG three-way routing.
- Need multi-hop retrieval: `IRCOTPipeline`, `SelfAskPipeline(single_hop=False)`, or reasoning/search pipelines.
- Need method-paper reproduction: use `examples/methods`-style recipes from [method recipes](method-recipes.md), not a custom pipeline first.
- Need multimodal retrieval/generation: `MMSequentialPipeline` with a multimodal prompt template and `multi_retriever_setting`.
