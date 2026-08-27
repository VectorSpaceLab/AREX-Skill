# Customization Recipes

## Settings Scope and Test Isolation

Use `Settings` for process-wide defaults and constructor arguments for local overrides.

```python
from contextlib import contextmanager
from llama_index.core import Settings
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM
from llama_index.core.node_parser import SentenceSplitter

@contextmanager
def isolated_settings(**overrides):
    snapshot = {
        "llm": Settings._llm,
        "embed_model": Settings._embed_model,
        "callback_manager": Settings._callback_manager,
        "node_parser": Settings._node_parser,
        "transformations": Settings._transformations,
        "prompt_helper": Settings._prompt_helper,
        "chat_prompt_helper": Settings._chat_prompt_helper,
    }
    try:
        for name, value in overrides.items():
            setattr(Settings, name, value)
        yield
    finally:
        Settings._llm = snapshot["llm"]
        Settings._embed_model = snapshot["embed_model"]
        Settings._callback_manager = snapshot["callback_manager"]
        Settings._node_parser = snapshot["node_parser"]
        Settings._transformations = snapshot["transformations"]
        Settings._prompt_helper = snapshot["prompt_helper"]
        Settings._chat_prompt_helper = snapshot["chat_prompt_helper"]

with isolated_settings(
    llm=MockLLM(max_tokens=64),
    embed_model=MockEmbedding(embed_dim=8),
    node_parser=SentenceSplitter(chunk_size=256, chunk_overlap=20),
):
    # Build indexes or query engines here.
    pass
```

Prefer explicit local overrides when only one component should change:

```python
query_engine = index.as_query_engine(llm=custom_llm, similarity_top_k=3)
```

Use `Settings.chunk_size` and `Settings.chunk_overlap` only when the configured `node_parser` exposes those attributes. If a custom parser does not, set parser-specific fields directly.

## Prompt Templates and Prompt Inspection

Core prompt imports:

```python
from llama_index.core.prompts import PromptTemplate, ChatPromptTemplate
from llama_index.core.base.llms.types import ChatMessage, MessageRole
```

Completion-style template:

```python
qa_prompt = PromptTemplate(
    "Context:\n{context_str}\n\nQuestion: {query_str}\nAnswer with citations."
)
formatted = qa_prompt.format(context_str="...", query_str="...")
```

Chat template:

```python
chat_prompt = ChatPromptTemplate([
    ChatMessage(role=MessageRole.SYSTEM, content="You answer with JSON only."),
    ChatMessage(role=MessageRole.USER, content="Context: {context_str}\nQuestion: {query_str}"),
])
messages = chat_prompt.format_messages(context_str="...", query_str="...")
```

Prompt objects support:

- `partial_format(**kwargs)` to freeze common variables.
- `template_var_mappings={"question": "query_str"}` when a component expects a different variable name.
- `function_mappings={"timestamp": lambda **kw: ...}` for computed template variables.
- `output_parser=...` to append parser format instructions during `format()`.

Many query components expose prompt mixin APIs. Inspect first, then update the exact prompt key:

```python
prompts = query_engine.get_prompts()
for key, prompt in prompts.items():
    print(key, prompt.get_template())

query_engine.update_prompts({"response_synthesizer:text_qa_template": qa_prompt})
```

Prompt keys are component-specific. If a key fails, re-run `get_prompts()` after constructing the exact retriever/query engine/response synthesizer and use one of the returned keys.

## Pydantic Output Parser

Use `PydanticOutputParser` when the LLM returns JSON text that must validate into a Pydantic model.

```python
from llama_index.core.bridge.pydantic import BaseModel, Field
from llama_index.core.output_parsers import PydanticOutputParser
from llama_index.core.prompts import PromptTemplate

class AnswerWithEvidence(BaseModel):
    answer: str = Field(description="Concise answer")
    evidence: list[str] = Field(description="Quoted source snippets")
    confidence: float = Field(ge=0, le=1)

parser = PydanticOutputParser(output_cls=AnswerWithEvidence)
prompt = PromptTemplate(
    "Use the context to answer.\nContext: {context_str}\nQuestion: {query_str}",
    output_parser=parser,
)
formatted_prompt = prompt.format(context_str="...", query_str="...")
parsed = parser.parse('{"answer":"...","evidence":["..."],"confidence":0.8}')
```

Validation failures usually mean one of these is wrong:

- The prompt does not include parser format instructions.
- The provider returned prose around JSON that cannot be extracted.
- The Pydantic model has fields or constraints the model did not satisfy.
- The selected LLM has weak JSON-following behavior for the requested schema.

## Pydantic Programs

Use `LLMTextCompletionProgram.from_defaults` when you want a callable object that formats a prompt, calls an LLM, and returns a Pydantic model.

```python
from llama_index.core.program import LLMTextCompletionProgram

program = LLMTextCompletionProgram.from_defaults(
    output_cls=AnswerWithEvidence,
    prompt_template_str=(
        "Return JSON for the answer.\n"
        "Context: {context_str}\nQuestion: {query_str}"
    ),
    llm=llm,
)
result = program(context_str="...", query_str="...")
```

For deterministic tests, use a mock or fake LLM that emits valid JSON matching the schema. `MockLLM` is useful for no-provider smoke checks, but a custom fake may be needed to return schema-specific JSON.

## Structured LLM and Response Synthesizer Outputs

For LLMs that support structured prediction through the LlamaIndex LLM interface, wrap the model:

```python
structured_llm = llm.as_structured_llm(AnswerWithEvidence)
response = structured_llm.complete("Return an answer with evidence")
```

For query response synthesis, pass `output_cls` into the response synthesizer factory or the query-engine construction path that forwards synthesizer arguments:

```python
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.response_synthesizers import ResponseMode

synthesizer = get_response_synthesizer(
    llm=llm,
    response_mode=ResponseMode.COMPACT,
    output_cls=AnswerWithEvidence,
)
```

`structured_answer_filtering=True` is available on refine/compact refine synthesizers and asks the LLM to filter answers in a structured way. It requires an LLM path that can follow the structured-answer contract; if results are empty or invalid, test without filtering first, then reintroduce it with simpler prompts.

## Callbacks and Token Counting

Attach callbacks before constructing the component whose events you need to observe.

```python
from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler

counter = TokenCountingHandler(tokenizer=lambda text: text.split())
Settings.callback_manager = CallbackManager([counter])

# Build/query components here, then inspect counts.
print(counter.total_llm_token_count)
```

`CallbackManager` can also trace explicit events:

```python
from llama_index.core.callbacks import CallbackManager, CBEventType

manager = CallbackManager([])
with manager.as_trace("custom-check"):
    with manager.event(CBEventType.QUERY, payload={"query": "hello"}):
        pass
```

If a handler does not fire, make sure the target component received the same callback manager directly or was built after `Settings.callback_manager` was set.

## Instrumentation Basics

LlamaIndex also has an instrumentation dispatcher and event/span handlers for observability integrations. Use callbacks for local token/event debugging and instrumentation when you need dispatcher-level event or span handling.

Typical approach:

1. Identify whether the integration expects callbacks or instrumentation handlers.
2. Register handlers before executing the indexed/query/agent operation.
3. Trigger a minimal local operation.
4. Verify handler state, emitted event types, or span records.

Provider-backed observability packages belong to integrations setup; keep no-provider tests on `CallbackManager`, `TokenCountingHandler`, `LlamaDebugHandler`, and simple instrumentation handlers.

## Evaluation Signals

Evaluator outputs use `EvaluationResult` with fields such as `query`, `contexts`, `response`, `passing`, `score`, `feedback`, `invalid_result`, and `invalid_reason`.

```python
from llama_index.core.evaluation import EvaluationResult

result = EvaluationResult(
    query="What is indexed?",
    contexts=["A doc chunk"],
    response="A doc chunk is indexed.",
    passing=True,
    score=1.0,
    feedback="Grounded in context.",
)
```

LLM-backed evaluators require the same LLM/provider setup as other model calls. For unit tests, assert result shape and custom evaluator logic without calling external APIs; reserve provider-backed scoring for integration tests.
