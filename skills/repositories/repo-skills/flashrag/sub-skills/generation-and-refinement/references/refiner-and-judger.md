# Refiners, Compressors, and Judgers

## Refiner Factory

Use `flashrag.utils.get_refiner(config, retriever=None, generator=None)` for factory construction. The factory inspects `refiner_name`, `refiner_model_path`, model config architecture when available, and special names such as `kg-trace`.

| Refiner family | Selected class | Required shape |
| --- | --- | --- |
| `recomp` with T5-like model | `AbstractiveRecompRefiner` | Seq2Seq compressor over retrieved documents. |
| `recomp` with embedding-like model or BERT architecture | `ExtractiveRefiner` | Sentence extraction by similarity to the question. |
| T5/BART architecture | `AbstractiveRecompRefiner` | Abstractive summary-style compression. |
| `lingua` in `refiner_name` | `LLMLinguaRefiner` | LongLLMLingua-style prompt/document compression. |
| `selective-context` or `sc` | `SelectiveContextRefiner` | Selective Context compression. |
| `kg-trace` | `KGTraceRefiner` | Knowledge-graph TRACE-style refinement using retriever/generator. |

`get_refiner` has built-in default model identifiers for several RECOMP names when `refiner_model_path` is omitted, but production configs should set paths explicitly for reproducibility.

## Dataset Requirements

Most refiners use `refiner.batch_run(dataset)` and expect a FlashRAG `Dataset` or dataset-like object whose items expose these attributes:

- `question`: required by all major refiners.
- `retrieval_result`: required when compressing retrieved documents; each document should include a `contents` string with title on the first line and body after that.
- `prompt`: required when `LLMLinguaRefiner` uses `refiner_input_prompt_flag: true`.

If a refiner fails with missing attributes, first verify that the upstream retrieval or prompt-building stage populated the dataset fields before blaming the model.

## Refiner Config Cheat Sheet

| Class | Key config fields | Notes |
| --- | --- | --- |
| `ExtractiveRefiner` | `refiner_name`, `refiner_model_path`, `refiner_topk`, `refiner_pooling_method`, `refiner_encode_max_length`, optional `refiner_mini_batch_size` | Uses FlashRAG encoder utilities to score split sentences against questions. |
| `AbstractiveRecompRefiner` | `refiner_name`, `refiner_model_path`, `refiner_max_input_length`, `refiner_max_output_length`, `device` | Loads `AutoModelForSeq2SeqLM` and `AutoTokenizer`. |
| `LLMLinguaRefiner` | `refiner_name`, `refiner_model_path`, optional `refiner_input_prompt_flag`, optional `llmlingua_config` | Uses `PromptCompressor`; config may include `rate`, `rank_method`, `condition_in_question`, `context_budget`, and `use_llmlingua2`. |
| `SelectiveContextRefiner` | `refiner_name`, `refiner_model_path`, optional `sc_config` | Uses GPT-2-style Selective Context settings such as `reduce_ratio` and `reduce_level`. |
| `KGTraceRefiner` | `refiner_name: kg-trace`, `trace_config`, plus compatible retriever/generator | This is a method-like refiner; use pipeline guidance when composing it end to end. |

Example for prompt compression without running a full pipeline:

```python
from flashrag.config import Config
from flashrag.dataset import Dataset, Item
from flashrag.refiner import LLMLinguaRefiner

config = Config("my_config.yaml", config_dict={
    "refiner_name": "longllmlingua",
    "refiner_model_path": "model-or-local-path",
    "refiner_input_prompt_flag": True,
    "llmlingua_config": {"rate": 0.55, "rank_method": "longllmlingua"},
})

refiner = LLMLinguaRefiner(config)
dataset = Dataset(config=config, data=[Item({"question": "...", "prompt": "...", "retrieval_result": []})])
compressed_prompt = refiner.batch_run(dataset)[0]
```

## Judger Factory

Use `flashrag.utils.get_judger(config)` when a method needs a retrieval gate or query classifier.

| `judger_name` contains | Selected class | Output |
| --- | --- | --- |
| `skr` | `SKRJudger` | `List[bool]`; `True` means retrieval is expected to help. |
| `adaptive` | `AdaptiveJudger` | Label-like outputs from the Adaptive-RAG classifier implementation. |

The shared config shape is:

```yaml
judger_name: skr
judger_config:
  model_path: model-or-local-path
  training_data_path: training-data.json
  topk: 5
  batch_size: 64
  max_length: 128
```

Adaptive-RAG uses a classifier model path instead of training data:

```yaml
judger_name: adaptive
judger_config:
  model_path: model-or-local-path
  batch_size: 16
  max_length: 512
```

## Judger Inputs

Both judgers expose `judge(dataset_or_questions)`. Supported inputs are a FlashRAG `Dataset`, `List[str]`, or a single `str`. For `Dataset`, the judger uses the `.question` field. The SKR judger also requires a JSON training data file with `question` and `judgement` fields where judgements include `ir_better` and `ir_worse`.

## Composition Guidance

- Use refiners after retrieval has populated `retrieval_result` and before prompt construction or final generation.
- Use judgers before retrieval when a method wants to skip retrieval for known/simple questions.
- Keep standalone component debugging separate from full method reproduction; once the task involves a named end-to-end method, route to the pipelines/methods sub-skill.
