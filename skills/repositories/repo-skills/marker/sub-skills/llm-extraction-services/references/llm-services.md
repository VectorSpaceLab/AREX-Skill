# LLM Services

Marker enables LLM behavior only when `use_llm` is true. In CLI form, pass `--use_llm`; in API form, include `{"use_llm": true}` in the config dict. If `use_llm` is omitted, `ConfigParser.get_llm_service()` resolves to `None` and the LLM processors return without doing work.

## Provider selection

| Provider | `llm_service` class path | Required config | Common optional config | Notes |
| --- | --- | --- | --- | --- |
| Gemini developer API | `marker.services.gemini.GoogleGeminiService` | `gemini_api_key` or `GOOGLE_API_KEY` environment fallback | `gemini_model_name`, `thinking_budget`, `timeout`, `max_retries`, `retry_wait_time`, `max_output_tokens` | Default when `--use_llm` is set and `--llm_service` is omitted. Default model is `gemini-2.0-flash`. |
| Google Vertex | `marker.services.vertex.GoogleVertexService` | `vertex_project_id` | `vertex_location`, `gemini_model_name`, `vertex_dedicated`, retry/timeout keys | Uses Vertex AI client mode. Default location is `us-central1`; default model is `gemini-2.0-flash-001`. |
| Ollama | `marker.services.ollama.OllamaService` | none by Marker validation | `ollama_base_url`, `ollama_model` | Defaults to `http://localhost:11434` and `llama3.2-vision`. Requires a running local Ollama service and a model that can satisfy JSON/image prompts. |
| Claude | `marker.services.claude.ClaudeService` | `claude_api_key` | `claude_model_name`, `max_claude_tokens`, retry/timeout keys | Uses Anthropic messages API and validates responses against the requested Pydantic response schema. |
| OpenAI-compatible | `marker.services.openai.OpenAIService` | `openai_api_key` | `openai_model`, `openai_base_url`, `openai_image_format`, retry/timeout keys | Supports OpenAI-like endpoints. Defaults to `https://api.openai.com/v1`, `gpt-4o-mini`, and `webp` images. Use `openai_image_format=png` for endpoints that reject WEBP images. |
| Azure OpenAI | `marker.services.azure_openai.AzureOpenAIService` | `azure_endpoint`, `azure_api_key`, `azure_api_version`, `deployment_name` | retry/timeout keys | Sends `deployment_name` as the model value through the Azure OpenAI client. |

## CLI patterns

Default Gemini hybrid conversion:

```bash
marker_single input.pdf --use_llm --gemini_api_key "$GOOGLE_API_KEY" --output_format markdown
```

OpenAI-compatible endpoint:

```bash
marker_single input.pdf \
  --use_llm \
  --llm_service marker.services.openai.OpenAIService \
  --openai_api_key "$OPENAI_API_KEY" \
  --openai_base_url "https://api.openai.com/v1" \
  --openai_model "gpt-4o-mini"
```

Local Ollama:

```bash
marker_single input.pdf \
  --use_llm \
  --llm_service marker.services.ollama.OllamaService \
  --ollama_base_url "http://localhost:11434" \
  --ollama_model "llama3.2-vision"
```

Table-focused conversion with LLM cleanup:

```bash
marker_single input.pdf \
  --use_llm \
  --force_layout_block Table \
  --converter_cls marker.converters.table.TableConverter \
  --output_format json
```

## API pattern

```python
from marker.config.parser import ConfigParser
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict

options = {
    "use_llm": True,
    "llm_service": "marker.services.openai.OpenAIService",
    "openai_api_key": "...",  # inject outside shared code
    "openai_model": "gpt-4o-mini",
    "output_format": "markdown",
}
parser = ConfigParser(options)
converter = PdfConverter(
    artifact_dict=create_model_dict(),
    config=parser.generate_config_dict(),
    processor_list=parser.get_processors(),
    renderer=parser.get_renderer(),
    llm_service=parser.get_llm_service(),
)
rendered = converter("input.pdf")
```

## Safe dry-run check

From this sub-skill directory, use the bundled probe before running a conversion:

```bash
python scripts/llm_config_probe.py \
  --use_llm \
  --llm_service marker.services.openai.OpenAIService \
  --openai_api_key dummy \
  --openai_model gpt-4o-mini
```

The probe imports Marker, resolves the service class path, checks required config fields, and reports defaults. It does not create a client or send a request.
