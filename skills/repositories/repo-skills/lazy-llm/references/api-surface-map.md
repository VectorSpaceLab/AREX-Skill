# LazyLLM API Surface Map

## When to read

Read this when a user names a LazyLLM class/function or you need to route from an API to the right sub-skill. Signatures below were inspected from the installed package and should be treated as orientation, not exhaustive API documentation.

## Core module and flow surfaces

| Surface | Verified signature or shape | Owning sub-skill |
| --- | --- | --- |
| `lazyllm.pipeline` | `(*args, post_action=None, auto_capture=False, save_result=None, **kw)` | [flow-orchestration](../sub-skills/flow-orchestration/SKILL.md) |
| `lazyllm.parallel` | `(*args, _scatter=False, _concurrent=True, multiprocessing=False, auto_capture=False, **kw)` | [flow-orchestration](../sub-skills/flow-orchestration/SKILL.md) |
| `lazyllm.bind` | `(__bind_func=<None>, *args, **kw)` | [flow-orchestration](../sub-skills/flow-orchestration/SKILL.md) |
| `lazyllm.diverter`, `switch`, `ifs`, `loop`, `warp`, `barrier`, `graph` | Flow composition primitives tested in LazyLLM flow tests | [flow-orchestration](../sub-skills/flow-orchestration/SKILL.md) |
| `lazyllm.config` and `lazyllm.namespace` | Mutable config object with env-backed keys and namespace contexts | [core-runtime](../sub-skills/core-runtime/SKILL.md) |
| `lazyllm.Prompter`, `AlpacaPrompter`, `ChatPrompter` | Prompt template helpers with OpenAI-format output modes | [core-runtime](../sub-skills/core-runtime/SKILL.md) |

## Model and serving surfaces

| Surface | Verified signature or shape | Notes |
| --- | --- | --- |
| `TrainableModule` | `(base_model='', target_path='', *, stream=False, return_trace=False, trust_remote_code=True, type=None, source=None, use_model_map=True)` | Local model/fine-tune/deploy abstraction; backend packages and model paths are optional requirements. |
| `OnlineModule` | `(model=None, source=None, *, type=None, url=None, **kwargs)` | Online provider wrapper; requires provider configuration for real calls. |
| `OnlineChatModule` | `(model=None, source=None, url=None, stream=True, return_trace=False, skip_auth=False, type=None, api_key=None, static_params=None, id=None, name=None, group_id=None, dynamic_auth=False, timeout=180, **kwargs)` | Provider chat module; message/tool-call merge and sanitization can be tested without network. |
| `ServerModule` | `(m=None, pre=None, post=None, stream=False, return_trace=False, port=None, pythonpath=None, launcher=None, url=None, num_replicas=1, security_key=None)` | Wraps modules/functions/services; port and launcher choices affect side effects. |
| `ActionModule` | `(*action, return_trace=False)` | Action wrapper for module workflows. |
| `get_model_type` | maps provider model names into categories such as `llm`, `vlm`, `stt`, `tts`, `embed`, `sd`, `text2video`, `cross_modal_embed` | [model-deployment](../sub-skills/model-deployment/SKILL.md) owns details. |

## RAG and document surfaces

| Surface | Verified signature or shape | Notes |
| --- | --- | --- |
| `Document` | `(*args, **kw)` | Main RAG document/index container; import requires the `rag` extra. |
| `Retriever` | `(doc, group_name, similarity=None, similarity_cut_off=-inf, index='default', topk=6, embed_keys=None, target=None, output_format=None, join=False, weight=None, priority=None, **kwargs)` | Retrieves from document node groups/indexes; external embeddings/stores may be optional. |
| `Reranker` | `(name='ModuleReranker', *args, **kwargs)` | Reranking wrapper; may require module/backend depending on name. |
| `DocNode`, `BM25`, readers/transforms/stores/doc-service models | Data and retrieval helpers | [rag-document-processing](../sub-skills/rag-document-processing/SKILL.md) owns recipes and formats. |

## Agent and tool surfaces

| Surface | Verified signature or shape | Notes |
| --- | --- | --- |
| `fc_register` | `(f, *, rewrite_func=None, **kwargs)` | Decorator/factory for function-call tools. Options include sandbox and file-parameter metadata validated by tests. |
| `ToolManager` | `(tools, return_trace=False, sandbox=None)` | Manages registered/callable tools. |
| `SkillManager` | `(dir=None, skills=None, max_skill_md_bytes=None, fs=None, sandbox=None)` | Loads LazyLLM skills from skill directories. |
| `ReactAgent` | `(llm, tools=None, max_retries=5, return_trace=False, prompt=None, stream=False, return_last_tool_calls=False, skills=None, desc='', workspace=None, sandbox=None, force_summarize=False, force_summarize_context='', keep_full_turns=0, fs=None, skills_dir=None, enable_builtin_tools=True, extra_stop_condition=None, on_max_retries=None)` | Provider/model call is required for a real agent run; schema checks can be no-network. |
| `ReWOOAgent` | `(llm=None, tools=[], *, plan_llm=None, solve_llm=None, return_trace=False, stream=False, return_last_tool_calls=False, skills=None, desc='', workspace=None, sandbox=None, fs=None, skills_dir=None, enable_builtin_tools=True)` | Multi-step reasoning agent. |
| `PlanAndSolveAgent` | `(llm=None, tools=[], *, plan_llm=None, solve_llm=None, max_retries=5, return_trace=False, stream=False, return_last_tool_calls=False, skills=None, desc='', workspace=None, sandbox=None, fs=None, skills_dir=None, enable_builtin_tools=True)` | Planning/solve agent. |
| `MCPClient` and CLI `deploy mcp_server` | MCP integration surface | External MCP processes are optional and side-effecting. |

## Writer and review surfaces

Writer workflows use Pydantic-style data models under `lazyllm.tools.writer.data_models`, artifact helpers under `lazyllm.tools.writer.utils`, and tool bases under `lazyllm.tools.writer.tools`. Core artifact classes include `WriterDocument`, `WriterBlock`, `WriterSpan`, `WritingContext`, `ResourceProfile`, and `WriterToolBase`.

CLI review commands are exposed as `lazyllm review` and `lazyllm review-local`. Keep posting/commenting side effects optional unless the user explicitly asks for them.

## CLI command families

The dispatcher recognizes these top-level command families:

- `lazyllm install <extra1> <extra2> <pkg1> ...`
- `lazyllm deploy modelname`
- `lazyllm deploy mcp_server <command> [args ...] [options]`
- `lazyllm run graph.json`, `lazyllm run chatbot`, `lazyllm run rag`
- `lazyllm skills init/list/info/delete/add/import/install`
- `lazyllm review ...`
- `lazyllm review-local ...`

The dispatcher prints usage and exits with error for bare `--help`; use concrete commands or inspect command files through the core-runtime sub-skill.
