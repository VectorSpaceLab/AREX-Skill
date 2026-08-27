# API and Plugin Reference

This reference covers the public-ish Python entry points that are useful when a future agent needs to inspect GPT Academic behavior without reading the whole checkout. Prefer the UI/plugin workflows for normal end-user tasks.

## App and configuration entry points

| Object | Verified signature / shape | Use |
| --- | --- | --- |
| `main.main()` | no arguments | Builds and launches the Gradio UI. Use the bundled `scripts/launch_app.sh --repo-root <checkout>` wrapper when starting the app from a checkout. |
| `toolbox.get_conf(*args)` | `(*args)` | Reads config values after applying environment variables, `config_private.py`, and `config.py`. Passing several names returns their values in order. |
| `toolbox.set_conf(key, value)` | `(key, value)` | Mutates one config value at runtime or in the private config mechanism. Treat as a write operation. |
| `toolbox.set_multi_conf(dic)` | `(dic)` | Mutates multiple config values. Treat as a write operation. |
| `check_proxy.get_current_version()` | `()` | Reads the local `version` JSON file and returns the version string/number. |
| `check_proxy.check_proxy(proxies, return_ip=False)` | `(proxies, return_ip=False)` | Probes the current proxy by querying public IP/geolocation endpoints. Network-dependent. |
| `check_proxy.auto_update(raise_error=False)` | `(raise_error=False)` | Interactive self-update routine; do not call unless the user explicitly wants repo self-update. |

## Function and plugin registries

| Object | Verified shape | Use |
| --- | --- | --- |
| `core_functional.get_core_functions()` | `()` -> dict | Returns basic prompt-button definitions. Verified keys include `学术语料润色`, `总结绘制脑图`, `查找语法错误`, `中译英`, `学术英中互译`, `解释代码`, and hidden helpers. |
| `crazy_functional.get_crazy_functions()` | `()` -> dict | Returns 56 plugin definitions. Each metadata record includes fields such as `Group`, `AsButton`, `AdvancedArgs`, `Info`, `Function`, and sometimes a wrapper `Class`. |
| `crazy_functional.get_multiplex_button_functions()` | `()` -> dict | Maps the submit-dropdown modes to plugin names: regular chat, internet search, multi-model chat, RAG, and multimedia query. |
| `toolbox.get_plugin_handle(plugin_name)` | `(plugin_name)` | Resolves plugin handles. Tests use strings such as `crazy_functions.SourceCode_Comment->注释Python项目`. |
| `toolbox.get_plugin_default_kwargs()` | `()` -> dict | Returns baseline plugin keyword arguments used by the test harness. |
| `toolbox.get_chat_handle()` | `()` | Returns the normal chat callable. |
| `toolbox.get_chat_default_kwargs()` | `()` -> dict | Returns baseline chat kwargs, including `llm_kwargs` and history/chatbot fields. |

## Model routing objects

| Object | Use |
| --- | --- |
| `request_llms.bridge_all.model_info` | Registry of model names, tokenizer/max-token metadata, provider routing hints, and local/remote model aliases. The inspected environment reported 70 entries. |
| `request_llms.bridge_all.predict` | Main Gradio-facing prediction dispatcher. It consumes UI state and routes calls through `bridge_all` to the selected provider. Use through the UI or test helpers rather than hand-calling unless debugging. |
| `request_llms.bridge_*` modules | Provider-specific bridges for OpenAI, Azure, Qwen/DashScope, GLM/Zhipu, DeepSeek, Gemini, Claude, Ollama, vLLM/OpenAI-compatible services, ChatGLM, Qwen local, MOSS, JittorLLMs, and others. |

## Plugin handle examples

These names come from `crazy_functional.py` and are useful for tests or scripted smoke checks:

| Domain | Plugin examples |
| --- | --- |
| Conversation | `查互联网后回答`, `询问多个GPT模型`, `询问多个GPT模型（手动指定询问哪些模型）`, `Rag智能召回`, `构建知识库（先上传文件素材,再运行此插件）`, `保存当前的对话`, `生成多种Mermaid图表(...)` |
| Academic docs | `Arxiv论文翻译`, `PDF论文翻译`, `批量总结PDF文档`, `理解PDF文档内容 （模仿ChatPDF）`, `批量文件询问 (支持自定义总结各种文件)`, `速读论文`, `Latex英文纠错+高亮修正位置 [需Latex]`, `精准翻译PDF文档（NOUGAT）` |
| Programming | `解析整个Python项目`, `解析整个C++项目（.cpp/.hpp/.c/.h）`, `解析Jupyter Notebook文件`, `注释Python项目`, `批量生成函数注释`, `Markdown翻译（指定翻译成何种语言）` |
| Agent tools | `虚空终端`, `动态代码解释器（CodeInterpreter）`, `Commandline_Assistant`-backed flows, dynamic function generation demos |
| Media | `🎨图片生成（DALLE2/DALLE3, 使用前切换到GPT系列模型）`, `🎨图片修改_DALLE2`, `实时语音对话`, `批量总结音视频（输入路径或上传压缩包）`, `多媒体智能体`, `数学动画生成（Manim）` |

Run `scripts/inspect_runtime.py --repo-root <checkout>` to print the exact currently loaded registry rather than relying on this static snapshot.