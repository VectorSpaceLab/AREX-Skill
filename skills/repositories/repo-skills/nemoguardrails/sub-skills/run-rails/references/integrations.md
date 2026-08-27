# Integrations

## Framework selection

Enable the LangChain framework with either of these:

```bash
export NEMOGUARDRAILS_LLM_FRAMEWORK=langchain
```

```python
from nemoguardrails import set_default_framework
set_default_framework("langchain")
```

`RunnableRails` lives in `nemoguardrails.integrations.langchain.runnable_rails`; it is not imported from `nemoguardrails.integrations.langchain` itself.

## RunnableRails

`RunnableRails` wraps a `RailsConfig` around an LLM or an existing runnable.

Typical constructor shape:

```python
RunnableRails(
    config,
    llm=None,
    tools=None,
    passthrough=True,
    runnable=None,
    input_key="input",
    output_key="output",
    verbose=False,
    input_blocked_message="I cannot process this request.",
    output_blocked_message="I cannot provide this response.",
)
```

Use it when you want to:

- wrap an LLM or an entire LCEL chain,
- preserve tool-call metadata,
- stream directly through guardrails,
- or wrap a specific graph node in LangGraph.

### Common shapes

- `RunnableRails(config) | some_chain`
- `RunnableRails(config, runnable=some_chain)`
- `prompt | (guardrails | llm)`
- `guardrails | rag_chain`

### Supported methods

`RunnableRails` implements the runnable surface you expect from LangChain:

- `invoke` / `ainvoke`
- `stream` / `astream`
- `batch` / `abatch`
- `transform` / `atransform`

### Input and output handling

- Strings, message lists, prompt values, and dict inputs are accepted.
- Dict chains default to `input` and `output`, but those keys can be customized.
- The output shape follows the wrapped target: `AIMessage`/`AIMessageChunk` when wrapping an LLM, or a plain string/dict when wrapping a chain.

## Tool calling

Tool calling with `RunnableRails` requires `passthrough=True`.

Recommended pattern:

```python
from langchain_openai import ChatOpenAI
from nemoguardrails.integrations.langchain.runnable_rails import RunnableRails

model = ChatOpenAI(...).bind_tools(tools)
guardrails = RunnableRails(config, passthrough=True)
guarded_model = guardrails | model
```

Rules to remember:

- bind tools on the model, not on the guardrails wrapper,
- keep `passthrough=True` for tool-call flows,
- and expect `tool_calls` metadata to survive the round trip.

If you bind tools at the wrong layer, the wrapper can raise a `RunnableBinding`-style error.

## LangGraph and agent middleware

Choose the integration point based on where you want the safety check to run:

| Integration | Best for | Caveat |
| --- | --- | --- |
| `RunnableRails` | Wrapping a chain or a LangGraph node | Direct streaming works best outside a graph; graph execution can buffer chunks. |
| `GuardrailsMiddleware` | LangChain `create_agent` loops | Checks message content before and after every model call, but does not inspect tool-call arguments. |

`GuardrailsMiddleware` lives in `nemoguardrails.integrations.langchain.middleware`. It is the right choice when you want automatic `before_model` / `after_model` hooks on every agent iteration.

### Tool-call caveats for middleware

- Tool-call arguments are not inspected because the middleware checks message `content`.
- Tool results arrive as tool messages and can influence later calls without being rechecked as input.
- If intermediate tool-call messages cause false positives, disable output rails or narrow the output rail policy.

## Using a chain inside guardrails

You can register a runnable or chain as an action and invoke it from Colang:

```python
rails.register_action(sample_chain, "sample_action")
```

Then call it from a flow with `execute sample_action`.

This pattern is useful when the chain belongs inside the guardrails config rather than around it.

## Troubleshooting hints

- `passthrough=False` is safer for prompt rewriting but is often the wrong choice for tool-calling agents.
- If streaming appears to collapse into large chunks inside a LangGraph node, test the same chain through direct `RunnableRails` streaming first.
- If a tool-bound model fails, move the tool binding to the wrapped model or wrap the whole agent instead of the bound sub-node.
