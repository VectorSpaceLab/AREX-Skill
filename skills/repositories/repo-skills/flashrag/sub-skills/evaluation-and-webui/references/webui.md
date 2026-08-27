# WebUI Guidance

FlashRAG WebUI is a Gradio interface with chat, evaluation, config preview/save/load, and index-building components. Treat WebUI guidance as configuration triage unless the user explicitly asks to launch the service.

## Module Map

| Area | Main Modules | What to Inspect |
| --- | --- | --- |
| UI assembly | `webui/interface.py` | Builds the Gradio Blocks app and registers basic, retrieval, rerank, generator, method, preview, chat, evaluate, and index builder tabs. |
| State and dispatch | `webui/engine.py`, `webui/manager.py`, `webui/runner.py` | Component registry, language switching, config parsing, pipeline loading, chat/evaluate actions. |
| Evaluation tab | `webui/components/evaluate.py` | Dataset path/name/split controls, metric dropdown, save flags, preview and run buttons. |
| Chat tab | `webui/components/chat.py`, `webui/chatter.py` | Single-query chat input, chatbot output, pipeline loading. |
| Config mapping | `webui/components/constants.py`, `webui/locales.py` | UI choices, component-to-config key mapping, labels/tooltips/default display text. |
| Saved configs | `webui/webui_configs/*.yaml` | Example generated YAML config format from the WebUI save action. |
| Chat pipelines | `webui/chat_pipelines/*.py` | Gradio-friendly pipeline wrappers that yield intermediate results. |

## Non-Launch Triage Workflow

1. Inspect `webui/components/constants.py` to confirm whether a method or metric appears in the UI choices.
2. Inspect `webui/runner.py` to see how UI component values are converted into FlashRAG `Config` keys.
3. Use the preview behavior rather than launching models: pipeline preview calls config generation; evaluation preview shows evaluation-only args.
4. Validate a saved YAML config for required keys before asking the user to launch chat or evaluate.
5. If a chat/evaluate issue mentions missing model, index, or dataset, triage config values first; most failures occur before user-facing output is produced.

## Chat Flow

The chat path parses pipeline args, creates a FlashRAG `Config` with `disable_save`, loads or reloads generator/retriever/pipeline objects, then sends a single query through the chosen chat pipeline. The runner reloads generator when `generator_model_path` changes and reloads retriever when retriever model, index, or corpus settings change.

Chat usually needs:

```yaml
method_name: Naive RAG
framework: hf
retrieval_method: e5
retrieval_model_path: intfloat/e5-base-v2
index_path: path-or-name-to-index
corpus_path: path-to-corpus-jsonl
generator_model: llama3-8B-instruct
generator_model_path: model-or-local-path
generation_params:
  max_tokens: 32
```

If using `Vanila Generation`, retriever loading is skipped. For RAG methods, missing `index_path`, `corpus_path`, or retrieval model settings typically prevents useful chat responses.

## Evaluate Flow

The evaluate tab gathers dataset and metric settings, merges them with pipeline settings, sets `split` from `dataset_split`, builds a FlashRAG `Config`, loads the dataset, prepares the pipeline, attaches `Evaluator(config)`, and runs the pipeline on the selected split. The terminal Markdown streams stdout/stderr from a worker thread.

Evaluation-specific keys include:

```yaml
dataset_name: nq
data_dir: dataset
dataset_split: test
save_intermediate_data: true
save_dir: output
save_note: experiment
seed: 2024
test_sample_num: 10
random_sample: false
metrics: [em, f1, acc, precision]
save_metric_score: true
```

The UI metric dropdown includes `em`, `f1`, `acc`, `precision`, `recall`, `input_tokens`, `bleu`, `rouge-l`, `rouge-1`, `rouge-2`, `zh_rouge-1`, `zh_rouge-2`, and `zh_rouge-l`. Retrieval metrics, `llm_judge`, and `gaokao_acc` may be available in the evaluator but not exposed in the default WebUI dropdown; users can still configure them in code or edited YAML if the runtime path supports it.

## Config Save and Load

- The WebUI save action merges pipeline and evaluation args and writes a timestamped YAML file under the WebUI config directory used by the running service.
- Loading a saved config flattens the YAML and maps keys back into components using `CONPONENTS2ARGKEY`.
- When troubleshooting a saved config, compare UI component names to FlashRAG config names because the UI has aliases such as `generator_name` → `generator_model` and `use_metrics` → `metrics`.
- For OpenAI settings, verify both API key and base URL fields, and confirm the resulting `openai_setting` dictionary is not accidentally empty when an OpenAI backend is intended.

## Service Caveats

- Do not run `create_ui().launch()` or equivalent service commands as a default diagnostic step.
- If the user asks to launch the WebUI, confirm dependencies, working directory, model/index/data availability, port expectations, and whether long-running service output is acceptable.
- WebUI imports require `gradio`; some environments may also need `streamlit` for related UI/documentation workflows, but the current Gradio interface imports are the primary launch dependency.
- Launching chat/evaluate may load large models, allocate GPU memory, access local indexes, or call external APIs depending on the chosen backend and config.
