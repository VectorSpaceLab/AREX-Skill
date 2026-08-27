# LLM and Extraction Troubleshooting

## Quick diagnostics

1. Confirm `--use_llm` or `{"use_llm": true}` is present.
2. Run `scripts/llm_config_probe.py` with the same config flags, using dummy credentials if you only need shape validation.
3. Validate `page_schema` with `scripts/validate_extraction_schema.py` before calling `ExtractionConverter`.
4. For provider-specific failures, reduce the page range and retry with debug logging or a simpler schema.

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `llm_service` is `None` | `use_llm` omitted. `ConfigParser.get_llm_service()` intentionally returns `None` unless `use_llm` is true. | Add `--use_llm` or `{"use_llm": true}`. |
| Service init assertion names missing config keys | Required provider fields are `None`. Marker validates annotated string config fields. | Supply the provider’s required keys; see `llm-services.md`. |
| Class import error for `llm_service` | Wrong full class path or provider package not installed. | Use exact paths such as `marker.services.openai.OpenAIService`; route broader class-path debugging to `../configuration-extension/`. |
| Gemini default fails unexpectedly | Default backend is Gemini and needs `gemini_api_key` or `GOOGLE_API_KEY`. | Provide Gemini credentials or explicitly set another `llm_service`. |
| OpenAI-compatible image rejection | Endpoint may not accept WEBP image payloads. | Set `openai_image_format=png` and confirm the model supports vision and structured responses. |
| Azure request uses wrong model | Azure service sends `deployment_name` as the model. | Use the deployment name, not the base model name, and set `azure_api_version`. |
| Ollama returns empty JSON | Local service/model unavailable, model lacks vision/JSON capability, or schema is too complex. | Check `ollama_base_url`, model availability, and simplify schema; run an Ollama health check outside the skill. |
| Extraction raises `Page schema must be defined` | `page_schema` is empty or omitted. | Pass a JSON schema object/string through config. |
| Output `document_json` fails validation | Provider returned JSON that does not match your target model, or schema is underspecified. | Parse `document_json`, validate with Pydantic, then tighten field types/descriptions or increase retries. |
| Existing markdown reuse returns poor or empty extraction | Markdown lacks Marker pagination separators or came from a different document/page set. | Reuse only `original_markdown` from `ExtractionOutput`; keep page range assumptions aligned. |
| LLM processor appears to do nothing | The relevant block type was not detected, image extraction settings skip the processor, or prerequisite table cells were absent. | Inspect non-LLM JSON/markdown first; for image descriptions set `--disable_image_extraction`; for forms/tables ensure table processing runs. |
| Rate limits, timeouts, or invalid JSON retries | Provider throttling or schema/prompt complexity. | Tune `timeout`, `max_retries`, `retry_wait_time`, narrow `page_range`, simplify schema, or switch providers. |

## Provider config names

- Gemini: `gemini_api_key`, `gemini_model_name`, `thinking_budget`.
- Vertex: `vertex_project_id`, `vertex_location`, `gemini_model_name`, `vertex_dedicated`.
- Ollama: `ollama_base_url`, `ollama_model`.
- Claude: `claude_api_key`, `claude_model_name`, `max_claude_tokens`.
- OpenAI-compatible: `openai_api_key`, `openai_model`, `openai_base_url`, `openai_image_format`.
- Azure OpenAI: `azure_endpoint`, `azure_api_key`, `azure_api_version`, `deployment_name`.
- Shared service controls: `timeout`, `max_retries`, `retry_wait_time`, `max_output_tokens`.

## Schema root problems

For Python schema files, the safest shape is one root class that inherits from `pydantic.BaseModel`. If multiple model classes exist, pass `--root-class`. Avoid executing untrusted schema code; Python schema validation imports and executes the file to obtain `model_json_schema()`.

## Privacy and credentials

Remote providers receive document-derived text and possibly page/block images. Do not enable remote LLM services for sensitive documents unless the user has approved that provider. Do not log real API keys; when probing config, use placeholder values and rely on provider-side execution only in the actual private environment.
