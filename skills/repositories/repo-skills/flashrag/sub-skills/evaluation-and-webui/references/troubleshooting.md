# Troubleshooting Evaluation and WebUI

## Metric Import Failures

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `No module named rouge` | English ROUGE metric selected without `rouge`. | Install the metric dependency or remove `rouge-1`, `rouge-2`, `rouge-l`. |
| `No module named rouge_chinese` | Chinese ROUGE metric selected without `rouge_chinese`. | Install `rouge_chinese` or choose non-ZH metrics. |
| `No module named jieba` | Chinese ROUGE needs segmentation. | Install `jieba` together with `rouge_chinese`. |
| `No module named tiktoken` | `input_tokens` uses OpenAI-like tokenizer. | Install `tiktoken` or set `metric_setting.tokenizer_name` to a Hugging Face tokenizer and ensure `transformers` is available. |
| Transformers model load error in `llm_judge` | Missing judge model path or incompatible runtime. | Provide `metric_setting.llm_judge_setting.model_path` or `model2path[model_name]`; warn that this metric loads a model. |
| OpenAI/API credential error | Backend or generator path uses an API provider. | Configure `openai_setting.api_key` and `openai_setting.base_url` only when the selected framework needs them; avoid embedding secrets in public configs. |

## Metric Selection Problems

- For Chinese free-form generation, prefer `zh_rouge-1`, `zh_rouge-2`, and `zh_rouge-l` over English `rouge-*`.
- For English free-form generation, use `rouge-*`, `bleu`, or token-level `f1` depending on task style.
- For short answer QA, start with `em`, `acc`, and `f1`; add `precision`/`recall` when partial overlap matters.
- For retrieval quality, use `retrieval_recall` and `retrieval_precision`, and set `metric_setting.retrieval_recall_topk`.
- For mixed English/Chinese corpora, split evaluation by language or report separate metric families; one ROUGE family will not be uniformly fair.

## Prediction Format Mismatches

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Exact match is unexpectedly zero | Reasoning text remains in `pred`. | Apply `selfask_pred_parse`, `ircot_pred_parse`, or `basic_pred_parse` before scoring. |
| SelfAsk scores empty answers | Output lacks exact `So the final answer is: ` prefix. | Adjust generation template or use a custom parser matching the actual final-answer marker. |
| IRCoT output includes extra rationale | Parser keeps everything after `So the answer is:`. | Post-process to isolate only the final answer if the pipeline appends more text. |
| Gaokao answers parse incorrectly | Options are not uppercase A-D or use a nonstandard marker. | Normalize option labels or adapt the parser for the dataset's answer format. |
| Retrieval metric raises key errors | Retrieved docs lack `contents`. | Convert retrieval results to dictionaries with `contents` strings before evaluation. |

## Evaluator Output Surprises

- `Evaluator.evaluate` continues after a metric exception, so missing aggregate keys indicate failure even when the run completes.
- `retrieval_precision` reads `metric_setting.retrieval_recall_topk`; use that key for both retrieval metrics.
- `Recall_Score.calculate_metric` uses a local variable named `precision`, but the returned key is still `recall`.
- `llm_judge` rescales extracted 0-10 ratings using `score / 10 + 1`; verify the intended interpretation before comparing to conventional 0-1 metrics.
- `BaseMetric.get_dataset_answer` treats non-empty `choices` as multiple-choice indexes; mixed choice formats can produce wrong gold answers.

## WebUI Import and Launch Failures

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `No module named gradio` | WebUI dependency missing. | Install UI extras/dependencies before launch. |
| Config dropdown is empty | No saved YAML configs in the WebUI config directory. | Save a config from the preview tab or provide a valid YAML file through the expected WebUI path. |
| Dataset dropdown is empty | `data_dir` does not exist or dataset subfolders are missing. | Point `data_dir` at a directory containing dataset subfolders with `train`, `dev`, or `test` files. |
| Evaluate split dropdown is empty | Dataset folder lacks files starting with valid split names. | Rename/provide files starting with `train`, `dev`, or `test`. |
| Chat loads but returns no useful retrieval context | Missing or wrong `index_path`, `corpus_path`, or retrieval model path. | Validate the index/corpus pair and retrieval model settings before loading chat. |
| Pipeline reload does not reflect config change | The changed field is not one of the reload keys. | Restart the WebUI or force reload if changing settings outside generator/retriever/method keys. |
| Port is occupied or service hangs | Gradio server conflict or long model load. | Choose a free port, use a lightweight config first, and tell the user service launch is long-running. |

## WebUI Chat With No Index or Model

1. Check whether `method_name` is `Vanila Generation`; if not, a retriever and index/corpus settings are usually required.
2. Confirm `retrieval_model_path`, `index_path`, and `corpus_path` are non-empty for RAG methods.
3. Confirm `generator_model_path` is set or resolvable through `model2path`/config logic.
4. Preview or save the config and inspect the resulting YAML before launching chat.
5. If using OpenAI or another API backend, verify `framework`, `generator_model`, and `openai_setting` are consistent.
6. Avoid repeatedly launching the WebUI while debugging; static config inspection is usually enough to find missing paths.
