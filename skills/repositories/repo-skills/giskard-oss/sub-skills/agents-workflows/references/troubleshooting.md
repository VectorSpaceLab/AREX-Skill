# agents-workflows troubleshooting

## Purpose

Use this file when `giskard.agents` workflows, tools, templates, structured
outputs, middleware, LiteLLM, or embeddings fail. Provider-specific SDK,
credential, alias, and model support issues belong in
[llm-providers](../../llm-providers/SKILL.md). Eval-scenario failures belong in
[checks-evals](../../checks-evals/SKILL.md).

## Quick triage

1. Run the deterministic smoke script if the installed package itself is in
   doubt:

   ```bash
   python sub-skills/agents-workflows/scripts/run_agents_smoke.py
   ```

2. If the smoke script passes but a live completion fails, route to
   [llm-providers](../../llm-providers/SKILL.md) and check provider install,
   credentials, model string, and operation support.
3. If the failure happens before any provider call, inspect tools, templates,
   structured-output validation, workflow error policy, or rate limiter state
   below.

## Missing LiteLLM

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError: LiteLLMGenerator requires the optional 'litellm' dependency` | The optional LiteLLM extra is not installed. | Install `pip install "giskard-agents[litellm]"` or `pip install "giskard[litellm]"`, then retry the import. |
| `AttributeError` or failed import for `LiteLLMGenerator` through the wrong namespace | LiteLLM generator is lazily exposed from `giskard.agents.generators`, not configured through the root `Generator` alias. | Use `from giskard.agents.generators import LiteLLMGenerator`. |
| LiteLLM import works but live call fails | Provider/model/credential issue inside LiteLLM or provider setup. | Keep workflow code unchanged. Diagnose provider credentials, SDK, and model support in [llm-providers](../../llm-providers/SKILL.md). |

## Provider config belongs outside workflows/tools

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Workflow code imports `openai`, `anthropic`, `google`, or `litellm` directly in a tool or prompt helper | Provider translation leaked into workflow/tool layer. | Move provider calls into a `BaseGenerator` subclass or use `agents.Generator`/`LiteLLMGenerator`; configure providers in [llm-providers](../../llm-providers/SKILL.md). |
| Tool function calls a provider API and sometimes times out/rate-limits independently of the generator | Tool is doing model work instead of deterministic business logic or external retrieval. | If the tool truly needs external I/O, keep it explicit and separately rate-limited; otherwise make the generator call the only model boundary. |
| Live `Generator(model="...")` call fails with auth, missing SDK, unsupported operation, or provider-specific bad request | Provider setup/model support is wrong, not the `ChatWorkflow` API. | Check provider alias, environment variables such as `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`, Azure settings, and supported operations in [llm-providers](../../llm-providers/SKILL.md). |

## Tool schema and coercion failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError: Tool ... parameter ... must have a type annotation` | `@tool` requires type hints for all parameters. | Add annotations, including defaults where appropriate. Annotate `RunContext` parameters as `agents.RunContext` so they are injected and omitted from the schema. |
| Tool description or parameter descriptions are empty/unhelpful | Missing or too-thin docstring. | Add a concise docstring. Use NumPy- or Google-style parameter sections for schema descriptions. |
| Pydantic validation errors inside `Tool.run` | Raw tool-call arguments do not match type hints; nested models/lists cannot be coerced. | Print or inspect `tool.parameters_schema`, validate a direct `await tool.run({...})` fixture, and fix argument names/types. Extra keys are ignored by the generated Pydantic model. |
| Tool returns JSON with strings for datetimes/UUIDs or nested models | Expected behavior: `Tool.run` serializes through Pydantic/JSON-safe adapters and always returns `str`. | Parse the returned string if the caller needs a Python object. Do not JSON-encode tool results again in workflow code. |
| `ERROR: ...` appears as a tool result | Default `@tool` catch converted an exception into a serializable `Error`. | Fix the underlying function or use `@tool(catch=None)` when the workflow should fail and be handled by `ChatWorkflow.on_error`. |
| Direct `my_tool(...)` behaves differently from `await my_tool.run(...)` | Direct call bypasses `Tool.run` coercion, catching, context injection, and serialization. | Use direct calls for ordinary Python behavior and `Tool.run` for workflow/tool-call behavior. Test both only when both modes matter. |
| `Unknown tool call 'name' ... Registered tools: <none>` | The generator returned a tool call whose name was not registered on the workflow. | Add `.with_tools(the_tool)` before `.run()`, verify the tool name, or fix the generator/provider tool serialization. |

## Template namespace and path errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `TemplateNotFound` for a name such as `judge.j2` | Default prompt path does not contain that file or was set relative to a different current directory. | Use `agents.set_default_prompts_path(...)` with the intended prompt directory, or pass a workflow-specific `PromptsManager`. Use paths controlled by the current project, not the generated skill directory unless you bundle prompts there. |
| `TemplateNotFound` for `namespace::judge.j2` | Namespace was not registered or was misspelled. | Register with `agents.add_prompts_path(path, namespace="namespace")`. Template names use `namespace::template_name`. |
| `ValueError: Namespace ... already exists` | The namespace is already registered to a different path. | Reuse the existing namespace/path, remove it with `remove_prompts_path`, or choose a distinct namespace. |
| Undefined variable error during render | Templates use `StrictUndefined`; `.with_inputs(...)` is missing a variable. | Add all variables with `.with_inputs(...)` or pass them to `PromptsManager.render_template(...)`. |
| `Template contains message blocks but rendered output is not empty` | A multi-message template has non-whitespace text outside `{% message role %}` blocks. | Move all rendered content into message blocks or remove the blocks and let the whole template become one user message. |
| Literal user text like `{{ 1 + 1 }}` unexpectedly renders | The workflow used `as_template=True` on untrusted/user-controlled content. | Keep user content as literal `.chat(text)` and pass variables through trusted developer-authored templates. Use the `fence` filter around untrusted content in templates. |

## Model refusal and workflow errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `WorkflowError: Step processing failed` | Default `ErrorPolicy.RAISE` wraps generator, tool, template, or parsing errors. | Inspect `err.exception` and `err.last_step` on the caught `WorkflowError`. For diagnostics, rerun with `.on_error(ErrorPolicy.RETURN)` to get a failed `Chat`. |
| `chat.failed` is `True` and `chat.error` is populated | Error policy returned a failed chat instead of raising. | Read `chat.error.message`, inspect messages up to `chat.last`, then fix the underlying tool/template/provider issue. |
| `run_many` or `run_batch` returns fewer chats than requested | `ErrorPolicy.SKIP` filtered failed chats. | Use `ErrorPolicy.RETURN` when the caller needs a result object for each input, including failures. |
| `.run()` with `ErrorPolicy.SKIP` returns a failed chat instead of skipping | This is expected for a single run. | Use `run_many`/`run_batch` for skip semantics, or check `chat.failed` after `.run()`. |
| `ModelRefusalError` inside `WorkflowError.exception` | Provider returned `finish_reason="refusal"` or an assistant refusal field during strict structured-output validation. | Treat as a model/content policy refusal, not a JSON parsing bug. Adjust the task/prompt if appropriate; provider policy troubleshooting belongs in [llm-providers](../../llm-providers/SKILL.md). |
| `Provider returned an empty choices list` | Generator/provider response had no choices. | For a custom generator, return a valid `CompletionResponse` with at least one `Choice`. For live providers, inspect provider response and route to provider troubleshooting. |

## Structured output parsing retries

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Strict `.with_output(Model)` fails with a Pydantic `ValidationError` | Assistant content is not valid JSON for the model schema. | Include clearer schema instructions in the prompt; in file templates include `{{ _instr_output }}`. Increase `num_retries` if occasional invalid JSON is expected. |
| Generator is called more than once for one workflow | Strict output parsing retries invalid responses. | Expected total attempts are `1 + num_retries` when validation fails. Set `num_retries=0` for a single attempt. |
| `.with_output(..., strict=False)` returns successfully but `chat.output` later raises | Non-strict mode skips validation and retries during generation; parsing still happens when `chat.output` is accessed. | Use `strict=True` for production typed outputs, or handle parse failures explicitly after raw content is returned. |
| Tool-calling workflow appears not to parse until after tools | Assistant messages containing tool calls are not parsed as final structured output; parsing happens when the generator returns a non-tool assistant content. | Ensure the final provider response after tool results is JSON matching the model. |
| Provider rejects the response-format schema name | Some backends constrain schema names. | `LiteLLMGenerator` normalizes Pydantic response-format names. For other providers, check [llm-providers](../../llm-providers/SKILL.md) for response-format support. |

## Rate limiter behavior

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Sequential calls wait about `60 / rpm` seconds | `MinIntervalRateLimiter.from_rpm(rpm)` enforces a minimum interval between request starts. | This is expected. Increase `rpm` only if allowed by the provider quota. |
| Parallel calls still start one at a time | Shared limiter plus `min_interval` spaces starts even when `max_concurrent` allows concurrent in-flight calls. | Use an appropriate RPM and `max_concurrent`; do not create separate limiters if the quota is global. |
| `ValueError: RPM must be greater than 0` | Invalid limiter construction. | Pass a positive integer to `from_rpm`. |
| `Rate limiter with id ... already registered` | Another limiter with the same id but different fields exists. | Reuse the original limiter id/config, choose a new id, or deliberately set `GISKARD_DISABLE_DUPLICATE_RATE_LIMITERS_WARNINGS=1` only if duplicate-id ambiguity is acceptable. |
| Rate limiting seems ineffective across generators | Each generator has a different limiter instance/id. | Share the same `MinIntervalRateLimiter` instance or call `.with_rate_limiter("existing-id")` after the limiter is registered. |
| Retried calls wait longer than expected | Retry backoff wraps the rate limiter, so each retry attempt also passes through throttling. | Account for both `RetryPolicy` backoff and provider RPM limits. Reduce retries or adjust backoff only if safe. |

## Embedding wrapper failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `EmbeddingModel.embed(...)` fails with provider auth or unsupported embedding errors | `EmbeddingModel` calls `giskard.llm.aembedding`; the selected provider/model must support embeddings. | Configure an embedding-capable provider in [llm-providers](../../llm-providers/SKILL.md) or choose a different model. |
| Embedding calls arrive in multiple provider batches | Local batching split the input by `max_batch_size` or `max_total_chars`. | Tune method arguments or `GISKARD_AGENTS_DEFAULT_MAX_BATCH_SIZE` / `GISKARD_AGENTS_DEFAULT_MAX_TOTAL_CHARS`. |
| An over-long single text appears truncated | `batched_embeddings` truncates a single text to the total-character limit to avoid impossible provider requests. | Increase `max_total_chars` if the provider allows it, or chunk text upstream before embedding. |
