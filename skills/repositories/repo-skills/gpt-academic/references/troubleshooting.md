# Cross-Cutting Troubleshooting

Use this file for install, import, model routing, network, and config issues that affect several GPT Academic workflows. Domain-specific failures live in each sub-skill guide.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: 使用项目内置Gradio获取最优体验` or UI startup rejects Gradio | Runtime does not have the repo-pinned `gradio==3.32.15` | Reinstall with `python -m pip install -r requirements.txt`; then run `python -c "import gradio; print(gradio.__version__)"`. |
| `ModuleNotFoundError: No module named 'pkg_resources'` while importing Gradio | Newer `setuptools` build removed/does not expose `pkg_resources`, but Gradio 3.32.15 imports it | Install `setuptools<81` in the GPT Academic environment, then retry the import. |
| Config change appears ignored | Higher-precedence environment variable or `config_private.py` overrides `config.py` | Check precedence: environment variables > `config_private.py` > `config.py`. Put personal changes in `config_private.py` and restart. |
| `缺少 api_key`, `Incorrect API key`, or model replies fail immediately | Missing/wrong provider key, key for wrong model family, or whitespace in key | Match model family to key: OpenAI/compatible `API_KEY`, DashScope `DASHSCOPE_API_KEY`, DeepSeek `DEEPSEEK_API_KEY`, GLM `ZHIPUAI_API_KEY`, Azure `AZURE_*`. Strip spaces/newlines. |
| `Model does not exist` or selected model missing from dropdown | `LLM_MODEL` not present in `AVAIL_LLM_MODELS`, typo, or provider endpoint does not support that model | Add the exact model string to `AVAIL_LLM_MODELS`, verify prefix syntax such as `one-api-`, `openrouter-`, `ollama-`, `vllm-`, and provider access. |
| OpenAI, Arxiv, Hugging Face, GitHub, or web search times out | Proxy/network not configured or public service blocked/rate-limited | Set `USE_PROXY=True` and `proxies`, or select a domestic provider when possible. Run `scripts/check_proxy.py --repo-root <checkout>`. Reduce concurrency if rate-limited. |
| Internet search reports overuse or irrelevant results | Public SearXNG rate limit or poor search query | Configure private `SEARXNG_URLS`; optionally add `JINA_API_KEY`; enable search optimization only when token budget allows. |
| Plugin button is not visible | The plugin group is hidden by `DEFAULT_FN_GROUPS` or only appears in the dropdown | Add the relevant group (`对话`, `编程`, `学术`, `智能体`) to `DEFAULT_FN_GROUPS`; also inspect the “更多函数插件” dropdown. |
| Uploaded file path no longer works | Temporary upload expired, wrong server-local path, or path was removed | Re-upload the file or paste a fresh local server path. Do not assume a browser-local path is visible to the server. |
| Long translation/summarization partly fails | Model/API timeout, rate limit, or too much parallelism | Lower `DEFAULT_WORKER_NUM`, raise `TIMEOUT_SECONDS`, use a faster model for drafts, or split the document/codebase into smaller batches. |
| Local model is extremely slow or crashes | Running a large local model on CPU, wrong quantization, or missing model weights | Treat local models as optional backends. Check `LOCAL_MODEL_DEVICE`, `LOCAL_MODEL_QUANT`, model path, VRAM, and provider-specific requirement files. |
| `pip install -r requirements.txt` is slow or fails on a managed Linux Python | System Python is protected or network is slow | Use a virtual environment/conda env. For Chinese networks use a mirror index; avoid `--break-system-packages` unless the user explicitly accepts system mutation. |

## Safe diagnostic order

1. Run `scripts/inspect_runtime.py --repo-root <checkout>` to list loaded core buttons, plugin groups, model registry size, and selected config values.
2. Run `scripts/check_proxy.py --repo-root <checkout>` when any remote model, search, Arxiv, Hugging Face, GitHub, or OpenAI call fails.
3. For document workflows, run `scripts/check_doc_backends.py --repo-root <checkout>` before PDF/LaTeX/Word/NOUGAT work.
4. For media workflows, run `scripts/check_media_backends.py --repo-root <checkout>` before voice, TTS, video, or animation work.
5. Only run native plugin tests after you know the needed API keys, external services, and system tools are available.