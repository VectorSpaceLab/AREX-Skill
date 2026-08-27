# Troubleshooting Generation and Model Components

Use this matrix when a Haystack prompt builder, generator, embedder, classifier, sampler, or validator fails. Start by checking the component family and data type: text generators consume `str`; chat generators consume `list[ChatMessage]`; text embedders consume `str`; document embedders/classifiers/samplers consume `list[Document]`.

## Install and Import Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError` for `openai`, `huggingface_hub`, `transformers`, `torch`, `sentence_transformers`, `jsonschema`, or language-detection libraries | Optional dependency for the selected component family is not installed | Install the package extras or integration package needed by that component; do not switch component types just to hide the missing dependency. |
| Lazy import message says `Run 'pip install ...'` | Haystack deferred an optional dependency until component construction or `warm_up()` | Install the dependency shown by the message, then rerun a minimal import/warm-up check. |
| Sentence Transformers or Transformers component emits a deprecation warning about moving to an integration package | Haystack 2.x still exposes the component but plans a Haystack 3.0 move | For current Haystack 2.31 code, public imports still work; for future-proof code, document the integration package import path. |
| `ImportError` for `arrow` when using time formatting in prompts | Jinja time extension optional dependency is missing | Install `arrow>=1.3.0` if prompt templates use time extension features; otherwise ordinary prompt rendering works without it. |

## Credential and Provider Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `OPENAI_API_KEY` missing or secret resolution fails | OpenAI generator/embedder default `Secret.from_env_var("OPENAI_API_KEY")` is strict | Export `OPENAI_API_KEY` or pass `api_key=Secret.from_env_var("OTHER_VAR")`; never hard-code the key in serialized pipeline files. |
| Azure component raises `Please provide an Azure endpoint...` | `azure_endpoint` argument and `AZURE_OPENAI_ENDPOINT` are both absent | Pass `azure_endpoint="https://...openai.azure.com/"` or set `AZURE_OPENAI_ENDPOINT`. |
| Azure component raises `Please provide an API key or an Azure Active Directory token` | Neither `api_key`, `azure_ad_token`, nor token provider resolves | Set `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_AD_TOKEN`, or pass an Azure AD token provider. |
| Azure request returns deployment/model not found | Confused provider model name with Azure deployment name | Use the Azure deployment name in `azure_deployment`; keep model names only where Azure docs require them. |
| Hugging Face private model download fails | Missing `HF_API_TOKEN`/`HF_TOKEN` or insufficient token scope | Use `Secret.from_env_var(["HF_API_TOKEN", "HF_TOKEN"], strict=False)` and verify token access to the model. |
| Provider rejects a generation parameter | `generation_kwargs` key is unsupported by that model/API version | Remove or rename the parameter for the target provider; test with a minimal call using only `max_completion_tokens` or `max_new_tokens`. |
| Timeouts or retries are too long/short | Default `OPENAI_TIMEOUT`, `OPENAI_MAX_RETRIES`, or provider HTTP client settings are unsuitable | Set constructor `timeout`, `max_retries`, or relevant env vars explicitly; keep retry behavior bounded in workflows. |

## Backend and Device Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Local generator or embedder is slow on first call | Model loads lazily during `run()` | Call `warm_up()` before serving traffic or measuring latency. |
| CUDA/MPS/XPU device errors | Requested device is unavailable or incompatible | Use `ComponentDevice.from_str("cpu")` to confirm correctness, then switch to `cuda:0`, `mps`, or `xpu` only after backend availability is proven. |
| Out-of-memory loading a local model | Model size, precision, or batch size exceeds hardware | Use a smaller model, lower `batch_size`, quantized `precision`, CPU/offload strategy, or an API-backed component. |
| `huggingface_pipeline_kwargs` appears to ignore constructor `model`, `task`, `device`, or `token` | Pipeline kwargs intentionally override those constructor parameters | Inspect and remove conflicting keys from `huggingface_pipeline_kwargs`, or move all settings into that dict consistently. |
| Local offline deployment tries to download from Hugging Face | Model is not cached or `local_files_only` is false | Preload model files and set `local_files_only=True` where supported. |
| `trust_remote_code` warning or model load failure | Model requires custom model code | Keep `trust_remote_code=False` for untrusted repositories; set it true only for reviewed model code. |

## API Misuse and Type Errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Text generator receives `messages` or chat generator receives `prompt` | Mixed text and chat component families | Use `PromptBuilder -> OpenAIGenerator` for string prompts, or `ChatPromptBuilder -> OpenAIChatGenerator` for chat messages. |
| Embedder says it expected a string but received documents | Used text embedder for document indexing | Switch to the matching document embedder, such as `OpenAIDocumentEmbedder` or `SentenceTransformersDocumentEmbedder`. |
| Document embedder/classifier errors on input type | Input is not `list[Document]` | Wrap content in `haystack.Document` objects and pass a list. |
| `PromptBuilder` silently renders an empty section | Missing optional Jinja variable | Set `required_variables="*"` or list required names so missing variables raise early. |
| `ChatPromptBuilder` raises about non-`ChatMessage` entries | Template list contains dicts/strings instead of `ChatMessage` objects | Build list templates with `ChatMessage.from_system(...)`, `ChatMessage.from_user(...)`, and related constructors. |
| `ChatPromptBuilder` raises about `templatize_part` in list template | Mixed-content filter is only valid in string templates | Convert to a string template using `{% message %}` blocks or remove the filter. |
| `AnswerBuilder` raises about regex capture groups | `pattern` has more than one capture group | Use one capture group, non-capturing groups `(?:...)`, or no groups if the full match is desired. |
| `AnswerBuilder` references wrong documents | Model citations are not 1-based document indices matching input order | Prompt the model to cite `[1]`, `[2]`, etc. and pass the same ordered `documents` list to `AnswerBuilder`. |
| `TopPSampler` raises `top_p must be between 0 and 1` | Invalid threshold | Clamp or validate `top_p` before calling the component. |

## JSON and Validation Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `JsonSchemaValidator` returns `validation_error` saying message is not valid JSON | LLM returned prose, markdown fences, or malformed JSON | Prompt for raw JSON only; use provider `response_format`; feed the validation error back for repair. |
| `JsonSchemaValidator` raises `Provide a JSON schema...` | No schema passed to constructor or `run()` | Instantiate `JsonSchemaValidator(json_schema=schema)` or call `run(..., json_schema=schema)`. |
| `JsonSchemaValidator` validates the wrong message | It validates only the last `ChatMessage` in the list | Put the candidate assistant JSON response last. |
| Validator raises because `ChatMessage` has no text | Message contains tool calls, images, or non-text content | Extract or generate a text JSON message before validation. |
| OpenAI/Azure structured output with streaming fails | Pydantic response format is not supported for streaming structured output | Use JSON schema response format for streaming, or disable streaming for Pydantic structured output. |
| OpenAI function-calling schema validation fails unexpectedly | The validator treats schemas with `name`, `description`, and `parameters` as function schemas | Validate the nested `parameters` schema and ensure the generated payload has the expected `function.arguments` structure. |

## Streaming Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Streaming with `n > 1` raises or produces unexpected behavior | Components generally stream one response at a time | Set response count to one for streaming, or disable streaming for multiple completions. |
| Callback type error in async code | Sync callback used where async callback is required, or vice versa | Match callback type to `run()` or `run_async()`; use async callbacks only with async generator methods that support them. |
| No chunks are collected | Callback was not passed to the component/run call actually used | Pass `streaming_callback` at init or at runtime; runtime callback overrides init callback. |
| Tool calls plus streaming fail on Hugging Face chat generator | Some tool/streaming combinations are unsupported | Disable streaming for tool calls or use a provider/generator class that supports the desired combination; agent/tool orchestration belongs in `../agents-tools-and-hitl/SKILL.md`. |

## Workflow-Specific Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Pipeline runs before prompt has all data | Prompt variables were optional and no required inputs block execution | Set required variables on `PromptBuilder`/`ChatPromptBuilder` and route graph mechanics to `../pipelines-and-components/SKILL.md`. |
| Retrieval results disappear after sampling | Scores are missing, non-numeric, or top-p is too low | Ensure retriever/ranker sets `Document.score` or configure `score_field`; use `min_top_k` to preserve enough context. |
| Classifier result missing from documents | Expected a top-level output but classifier writes into document metadata | Read `document.meta["classification"]`; do not expect a separate `labels` output. |
| Embeddings have wrong dimensionality for a document store | Model or `dimensions` changed after indexing | Re-index documents with the same embedder configuration used at query time; retrieval/store details belong in `../retrieval-and-rag/SKILL.md`. |
| Generator output format breaks downstream parser | Prompt, provider parameters, and validator are inconsistent | Align prompt instructions, provider structured output, `JsonSchemaValidator` schema, and `AnswerBuilder` regex/citation pattern. |

## Deterministic Local Check

Run the bundled smoke check before debugging credentials:

```bash
python scripts/model_component_smoke_check.py
```

The script uses only public Haystack imports and non-network behavior. If it fails, fix local installation/import or API-shape issues first. If it passes but provider calls fail, focus on credentials, model names, endpoints, quotas, network access, and provider-specific `generation_kwargs`.
