# Provider Recipes

Read this reference before constructing `ModelFactory` objects. The repository
contains near-duplicate Workforce examples for several CAMEL model platforms;
they all create separate models for specialist workers and coordinator/task
agents, then add workers to one `Workforce`.

## Provider matrix

| Provider route | CAMEL platform in source | Environment signal | Important caveat |
|---|---|---|---|
| OpenAI default | `ModelPlatformType.OPENAI` | `OPENAI_API_KEY`; optional `OPENAI_API_BASE_URL` | The canonical example uses a tool-capable GPT model and temperature `0`. |
| Anthropic | `ModelPlatformType.ANTHROPIC` | `ANTHROPIC_API_KEY` | Use a Claude model available in the installed CAMEL release and confirm tool calling. |
| Qwen | `ModelPlatformType.QWEN` | `QWEN_API_KEY`; optional `QWEN_API_BASE_URL` | The source uses a string model type such as `qwen3.5-plus`. |
| DeepSeek | `ModelPlatformType.DEEPSEEK` | `DEEPSEEK_API_KEY`; optional `DEEPSEEK_API_BASE_URL` | The example uses `ModelType.DEEPSEEK_CHAT`; tool and multimodal support vary. |
| Gemini | `ModelPlatformType.GEMINI` | Check the installed CAMEL provider expectation; source comments use `GOOGLE_API_KEY`, while the checked-in template labels `GEMINI_API_KEY` | Treat this naming disagreement as a preflight issue, not a reason to paste both secrets into code. |
| Groq | `ModelPlatformType.GROQ` | `GROQ_API_KEY`; optional `GROQ_API_BASE_URL` or `OPENAI_API_BASE_URL` | The source uses a larger Llama model for tool workers and a smaller one for coordinator/task agents. |
| OpenAI-compatible/VLLM | `ModelPlatformType.OPENAI_COMPATIBLE_MODEL` | `VLLM_API_URL` defaulting to `http://localhost:8000/v1`, optional `VLLM_API_KEY`, and `VLLM_MODEL_NAME` | The endpoint must be running and expose the requested model name; the example does not start the server. |

The project template also mentions Azure, PPIO, Novita, Google Search,
Chunkr, and Firecrawl variables. Those are optional integrations or provider
variants, not proof that every corresponding example exists in this checkout.
Use only the variables required by the selected model and toolkit.

## Common construction shape

```python
model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=ModelType.GPT_5_2,
    model_config_dict={"temperature": 0},
)
```

Provider examples repeat this for web, document, reasoning, image, browsing,
and planning roles. For a compatible endpoint, the source passes `model_type`
as the configured model name plus `url=VLLM_API_URL` and `api_key=VLLM_API_KEY`.
Keep the endpoint URL and model name in environment/config, not in prompts.

## Preflight sequence

1. Run `validate_provider_config.py --provider <name> --env-file <file>`; it
   reports names and status, never values.
2. Confirm the model supports tool calling for every worker that receives
   `FunctionTool` objects. Confirm multimodal support for image/video tasks.
3. Start with a trivial, non-sensitive task and a small round limit. Verify
   the answer, tool calls, and token accounting before attempting browser or
   file-writing tasks.
4. If the selected provider fails, change provider/model configuration rather
   than silently using a CPU import as a substitute for a remote model.

Never commit `.env`, print its values, or include an API key in a generated
workforce skeleton. See [troubleshooting.md](troubleshooting.md) for missing
key and endpoint symptoms.
