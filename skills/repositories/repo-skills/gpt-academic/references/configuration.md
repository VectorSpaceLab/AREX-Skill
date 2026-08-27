# Configuration Reference

GPT Academic reads configuration in this order:

```text
environment variables > config_private.py > config.py
```

Use `config_private.py` for local secrets and per-machine settings. It is the safest place for API keys, proxy values, local model paths, audio credentials, search endpoints, and ports.

## Minimum local startup

```bash
python -m pip install -r requirements.txt
python -m pip install 'setuptools<81'  # only if gradio/pkg_resources import fails
python main.py
```

The app expects the repository root to be the working directory when started. The UI will open on `WEB_PORT` if set; otherwise it selects a random port.

## Core runtime knobs

| Setting | Use |
| --- | --- |
| `LLM_MODEL` | Default model selected in the UI. It must also appear in `AVAIL_LLM_MODELS`. |
| `AVAIL_LLM_MODELS` | Models shown in the toolbar. Add every provider/model you want selectable. |
| `API_KEY` | OpenAI and OpenAI-compatible services. Multiple keys may be comma-separated. |
| `DASHSCOPE_API_KEY`, `DEEPSEEK_API_KEY`, `ZHIPUAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` | Provider-specific online model keys. |
| `USE_PROXY`, `proxies` | Network proxy for OpenAI, Hugging Face, search, Arxiv, or other blocked services. |
| `API_URL_REDIRECT` | Redirects OpenAI-style requests to One-API, vLLM, Ollama, or custom endpoints. |
| `DEFAULT_WORKER_NUM` | Parallel LLM requests for translation, summarization, and code/document batch tasks. Lower it when rate-limited. |
| `TIMEOUT_SECONDS`, `MAX_RETRY` | Request timeout and retry behavior for API calls. |
| `WEB_PORT`, `AUTO_OPEN_BROWSER`, `CUSTOM_PATH`, `SSL_KEYFILE`, `SSL_CERTFILE` | Web service binding, browser opening, reverse-proxy path, and HTTPS settings. |
| `DEFAULT_FN_GROUPS` | Plugin groups visible by default: usually `['对话', '编程', '学术', '智能体']`. |
| `NUM_CUSTOM_BASIC_BTN` | Number of custom prompt buttons shown in the UI. |

## Provider patterns

| Pattern | Required config | Notes |
| --- | --- | --- |
| OpenAI GPT | `API_KEY`, `LLM_MODEL` such as `gpt-4o`, proxy when needed | Required for DALL-E image generation and many GPT-family workflows. |
| Qwen/DashScope | `DASHSCOPE_API_KEY`, `LLM_MODEL` such as `qwen-max` | Good no-proxy option for Chinese users. |
| DeepSeek | `DEEPSEEK_API_KEY`, `LLM_MODEL` such as `deepseek-chat` or `deepseek-reasoner` | Useful for lower-cost reasoning or coding. |
| GLM/Zhipu | `ZHIPUAI_API_KEY`, `LLM_MODEL` such as `glm-4` | Supports Chinese models and some vision variants. |
| Azure OpenAI | `AZURE_ENDPOINT`, `AZURE_API_KEY`, `AZURE_ENGINE` or `AZURE_CFG_ARRAY`; model names normally start with `azure-` | Use array config for multiple Azure deployments. |
| One-API/OpenRouter | OpenAI-compatible `API_KEY`, model prefix such as `one-api-` or `openrouter-`, often `API_URL_REDIRECT` | Confirm supported model names and max-token suffixes. |
| Ollama | model names such as `ollama-llama3(max_token=4096)`, local Ollama service address when required | Good for local/private data if the model service is running. |
| vLLM | `LLM_MODEL = "vllm-/path/or/name(max_token=4096)"`, placeholder `API_KEY`, `API_URL_REDIRECT` to the vLLM OpenAI-compatible server | vLLM server and GPU environment are external to GPT Academic. |
| Native ChatGLM/Qwen local | `CHATGLM_LOCAL_MODEL_PATH`, `QWEN_LOCAL_MODEL_SELECTION`, `LOCAL_MODEL_DEVICE`, `LOCAL_MODEL_QUANT` | GPU is strongly recommended; CPU may be impractical for large models. |

## Conversation, search, and RAG settings

| Workflow | Settings to check |
| --- | --- |
| Internet search | `SEARXNG_URLS`, `JINA_API_KEY` optional, proxy/network access. Public SearXNG can rate-limit. |
| Multi-model query | `MULTI_QUERY_LLM_MODELS`, each listed model in `AVAIL_LLM_MODELS`, matching provider keys. |
| Knowledge base / RAG | `EMBEDDING_MODEL`, provider key for embeddings, `llama-index` dependencies, local vector-store path. |
| Conversation export/import | `PATH_LOGGING`, browser LocalStorage availability, file output permissions. |
| URL extraction | Network access and pages that do not block automated extraction. |

## Academic document settings

| Workflow | Settings / tools |
| --- | --- |
| PDF translation and QA | `pymupdf`, GROBID service URLs, optional `DOC2X_API_KEY`, optional `MATHPIX_APPID` / `MATHPIX_APPKEY`. |
| Arxiv translation | Network access to Arxiv, optional LaTeX toolchain for PDF rebuilds, `ARXIV_CACHE_DIR`. |
| LaTeX proofread/translate/polish | `pdflatex` and `latexdiff` on `PATH` for compiled outputs and diff PDFs. |
| Word summary | `python-docx`; legacy `.doc` requires Windows + `pywin32`, otherwise convert to `.docx`. |
| NOUGAT PDF parsing | Optional `nougat-ocr`, Hugging Face model download, GPU recommended but CPU possible and slow. |
| Batch file query | LlamaIndex reader dependencies, supported file formats, 10 MB per-file practical limit. |

Run `scripts/check_doc_backends.py --repo-root <checkout>` to inspect local document-related imports and external commands.

## Media settings

| Workflow | Settings / tools |
| --- | --- |
| Image generation | OpenAI-compatible `API_KEY`, GPT-family model selected, proxy if required. |
| Image understanding | A vision model such as `gpt-4o`, `gpt-4o-mini`, `gpt-4-vision-preview`, `glm-4v`, or equivalent. |
| Voice assistant | `ENABLE_AUDIO = True`, Aliyun speech credentials (`ALIYUN_APPKEY`, `ALIYUN_TOKEN` or AccessKey/Secret), browser microphone permission. |
| Edge TTS | `TTS_TYPE = "EDGE_TTS"`, `EDGE_TTS_VOICE`, `edge-tts`, `pydub`, `ffmpeg`. |
| SoVITS TTS | `TTS_TYPE = "LOCAL_SOVITS_API"`, `GPT_SOVITS_URL`, external SoVITS service, usually GPU/Docker. |
| Audio/video summary | API key, supported audio/video format, `ffmpeg` for media conversion when needed. |

Run `scripts/check_media_backends.py --repo-root <checkout>` before media workflows.

## Safety notes

- Never paste real API keys into public chat, generated docs, or test fixtures.
- Put secrets in `config_private.py` or environment variables; keep them out of version control.
- Treat Void Terminal config mutation and source-code docstring insertion as write operations requiring explicit user approval or a clean backup.
- Do not increase `DEFAULT_WORKER_NUM` blindly; high parallelism can trigger provider rate limits and partial outputs.