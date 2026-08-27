# LLM, RAG, and Agent Recipes

This reference collects self-contained txtai orchestration patterns. It assumes `txtai` 9.x and Python 3.10+.

## Choose the Right Primitive

| Need | Primitive | Notes |
| --- | --- | --- |
| One prompt in, generated text out | `LLM` | Best for summarization, rewriting, classification-by-prompt, chat, or custom generation. |
| Prompt must cite or use local retrieved context | `RAG` | Retrieves context with embeddings/similarity, builds a prompt, and calls a generator or QA model. |
| Model must decide which operation to call next | `Agent` | Uses tools over iterative steps; output can vary across runs. |
| Fixed, repeatable transformations | `Workflow` | Route to `../pipelines-and-workflows/SKILL.md`. |
| Build/search the vector store itself | `Embeddings` | Route to `../embeddings-search/SKILL.md`. |

## Direct `LLM`

```python
from txtai import LLM

llm = LLM("ibm-granite/granite-4.0-350m")
print(llm("Write a one sentence explanation of txtai.", maxlength=128))
```

Useful call parameters:

- `maxlength`: maximum output token length sent to the backend.
- `stream=True`: returns a stream/generator of text chunks when the backend supports streaming.
- `stop=[...]`: stop strings passed through generation.
- `defaultrole="auto"`: wraps plain strings as chat user messages for chat models; use `"prompt"` for raw prompts.
- `stripthink`: defaults to `True` for non-streaming and strips common thinking tags.

Chat-style input:

```python
messages = [
    {"role": "system", "content": "You are concise."},
    {"role": "user", "content": "Explain RAG in txtai."},
]
print(llm(messages, maxlength=256))
```

Batch input:

```python
answers = llm(["Define embeddings", "Define agentic RAG"], maxlength=64)
```

## Minimal RAG with In-Memory Content

```python
from txtai import Embeddings, RAG

embeddings = Embeddings(content=True)
embeddings.index([
    ("rag", "RAG combines retrieval with generation."),
    ("agent", "Agents can call Python functions, web search, embeddings indexes and skills."),
])

template = """
Use only the context to answer.
Question: {question}
Context: {context}
"""

rag = RAG(
    embeddings,
    "ibm-granite/granite-4.0-350m",
    template=template,
    system="Answer only from supplied context.",
    context=2,
    output="flatten",
)
print(rag("What can agents call?", maxlength=128))
```

RAG constructor fields to set deliberately:

- `similarity`: `Embeddings`, `Similarity`, callable batch searcher, or other compatible similarity source.
- `path`: model path, existing `LLM`, `Questions`, or custom pipeline.
- `context`: number of retrieved matches to include; defaults to 3.
- `minscore`: minimum score for a retrieved match to enter prompt context.
- `mintokens`: minimum token/text length for retrieved context rows.
- `template`: Python format string; must include `{question}` and `{context}` for normal RAG.
- `system`: optional system prompt, also formatted with `{question}` and `{context}`.
- `separator`: string joining retrieved context segments.
- `output`: `default`, `flatten`, or `reference`.

## RAG with Explicit Inputs

String input returns a single answer when the model returns one answer:

```python
answer = rag("Summarize the knowledge base", maxlength=512)
```

Batch string input returns a list:

```python
answers = rag(["What is RAG?", "What is an agent?"], maxlength=256)
```

Tuple/dict input separates search query from final question:

```python
queue = [{
    "name": "case-1",
    "query": "agent tools embeddings web search",
    "question": "Which tools can the agent use?",
    "snippet": False,
}]
answers = rag(queue, maxlength=256)
```

Use tuple/dict input when the retrieval query should be terse and the generated question should be user-friendly.

## RAG over a Provided Text List

If no embeddings database is available, pass `texts=` and use a similarity-compatible source.

```python
from txtai.pipeline import Similarity
from txtai import RAG

similarity = Similarity("sentence-transformers/all-MiniLM-L6-v2")
texts = ["txtai supports semantic search", "txtai supports RAG and agents"]
rag = RAG(similarity, "ibm-granite/granite-4.0-350m", output="flatten")
print(rag("What generation patterns exist?", texts=texts, maxlength=128))
```

This still may download the similarity and generation models. For safe config-only validation, use `scripts/rag_config_template.py`.

## RAG via YAML/Application

```yaml
path: ./knowledge-index
embeddings:
  path: sentence-transformers/all-MiniLM-L6-v2
  content: true

rag:
  path: ibm-granite/granite-4.0-350m
  output: flatten
  context: 3
  minscore: 0.05
  template: |
    Answer using only the context below.
    Question: {question}
    Context: {context}
```

```python
from txtai import Application

app = Application("app.yml")
rag_pipeline = app.pipelines["rag"]
print(rag_pipeline("What does the index contain?"))
```

When `rag.similarity` is omitted, the Application initializes the RAG pipeline and later attaches the configured embeddings index as the similarity source.

## Python Function Tools

Direct function with annotations and docstring:

```python
from datetime import datetime
from txtai import Agent

def today(iso: bool = True) -> str:
    """
    Gets the current date.

    Args:
        iso: return ISO formatted time when true

    Returns:
        current date string
    """
    return datetime.today().isoformat() if iso else str(datetime.today())

agent = Agent(model="Qwen/Qwen3-4B-Instruct-2507", tools=[today], max_steps=3)
```

Explicit dictionary when docs or annotations are not enough:

```python
def lookup(query):
    return {"query": query, "answer": "example"}

tool = {
    "name": "lookup",
    "description": "Looks up a short answer in the local catalog",
    "inputs": {"query": {"type": "string", "description": "search query"}},
    "output": "any",
    "target": lookup,
}
agent = Agent(model="Qwen/Qwen3-4B-Instruct-2507", tools=[tool], max_steps=3)
```

Tool names should be short, lowercase, and unique. Descriptions should say when to use the tool and what it returns.

## Embeddings-Backed Agent Tools

Use a live `Embeddings` instance:

```python
from txtai import Agent, Embeddings

embeddings = Embeddings(content=True)
embeddings.index([("doc1", "Agents can search embeddings indexes as tools.")])

kb = {
    "name": "knowledgebase",
    "description": "Searches local txtai orchestration notes",
    "target": embeddings,
}
agent = Agent(model="Qwen/Qwen3-4B-Instruct-2507", tools=[kb], max_steps=5)
```

Use a saved index path:

```python
kb = {
    "name": "knowledgebase",
    "description": "Searches the saved local knowledge base",
    "path": "./knowledge-index",
}
agent = Agent(model="Qwen/Qwen3-4B-Instruct-2507", tools=[kb], max_steps=5)
```

The built-in embeddings tool calls `embeddings.search(query, 5)` and describes results as dict rows with `id`, `text`, and `score`. Ensure the embeddings index was built with `content=True` or the tool will not have useful `text` context.

## Built-In and Web Tools

```python
agent = Agent(
    model="Qwen/Qwen3-4B-Instruct-2507",
    tools=["websearch", "webview", "read"],
    max_steps=5,
)
```

Common shortcuts:

- `websearch`: searches the web; requires network and provider availability.
- `webview`: alias for `read`; extracts web page text.
- `read`: reads files or URLs and extracts text where possible.
- `defaults`: loads the default local toolkit (`bash`, `edit`, `glob`, `grep`, `python`, `question`, `read`, `todowrite`, `websearch`, `write`). Use only in trusted sandboxes.
- `http://.../mcp`: imports a Model Context Protocol tool collection.
- `*.md`: loads a `skill.md` file as a tool.

## Agent Teams

```python
from txtai import Agent, LLM

llm = LLM("Qwen/Qwen3-4B-Instruct-2507")

searcher = Agent(model=llm, tools=["websearch"], max_steps=3)
writer = Agent(model=llm, tools=[], max_steps=2)

team = Agent(
    model=llm,
    tools=[
        {"name": "searcher", "description": "Finds fresh web evidence", "target": searcher},
        {"name": "writer", "description": "Writes concise final summaries", "target": writer},
    ],
    max_steps=8,
)
```

Guidelines:

- Give sub-agents narrow toolsets.
- Use a shared `LLM` instance to avoid repeated backend setup.
- Increase `maxlength` on the supervisor call when sub-agent outputs are long.
- Use `memory=` only when conversation history should affect later calls.

## Agent Prompt Template and Memory

```python
agent = Agent(
    model="Qwen/Qwen3-4B-Instruct-2507",
    tools=["websearch"],
    memory=5,
    template="""
{{ text }}

{% if memory %}
Relevant prior conversation:
{{ memory }}
{% endif %}

Respond with citations when web tools are used.
""",
)

agent("Find current txtai release notes", session="research")
agent("Summarize them", session="research")
agent("Start over", session="research", reset=True)
```

Agent templates are Jinja templates and must include `{{ text }}` and `{{ memory }}` placeholders when replacing the default template.

## Instructions Files and Skill Files

```python
agent = Agent(
    model="Qwen/Qwen3-4B-Instruct-2507",
    instructions="agents.md",
    tools=["./skills/example/SKILL.md"],
    max_steps=5,
)
```

`instructions` may be a direct string or a path to an `agents.md` file. Tool strings ending in `.md` load skill-style Markdown with YAML frontmatter containing `name` and `description`.

## Code-Agent Mode

```python
agent = Agent(
    model="Qwen/Qwen3-4B-Instruct-2507",
    tools=["python"],
    method="code",
    max_steps=3,
)
```

`method="tool"` is the default. `method="code"` switches to a smolagents code agent that generates and executes Python. Use code-agent mode only with trusted prompts and sandboxed execution.

## API/YAML Agent Section

```yaml
llm:
  path: hf-internal-testing/tiny-random-LlamaForCausalLM

agent:
  support:
    max_steps: 3
    tools:
      - name: ticket_lookup
        description: Looks up support tickets
        target: mypackage.tools.ticket_lookup
```

`Application` resolves `target` strings through configured pipelines, workflows, or importable callables. When serving this through txtai API, route endpoint and deployment details to `../api-and-deployment/SKILL.md`.
