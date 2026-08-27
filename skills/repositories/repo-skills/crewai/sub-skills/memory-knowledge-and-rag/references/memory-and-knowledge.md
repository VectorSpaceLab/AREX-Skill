# Memory and Knowledge

CrewAI has two retrieval surfaces that often work together but serve different purposes:

- `Memory` stores and recalls learned facts over time. It can run standalone, attach to a `Crew`, attach to an `Agent`, or be used inside a `Flow`.
- `Knowledge` indexes explicit sources such as strings, text files, PDFs, CSV, Excel, JSON, or Docling-converted documents for retrieval during agent work.

## Memory Quick Reference

```python
from crewai import Memory

memory = Memory(
    llm="gpt-5.4-mini",
    storage="lancedb",
    recency_weight=0.3,
    semantic_weight=0.5,
    importance_weight=0.2,
)

record = memory.remember(
    "Use PostgreSQL for the customer analytics warehouse.",
    scope="/project/analytics/decisions",
    categories=["database", "decision"],
    importance=0.8,
)

matches = memory.recall(
    "Which warehouse database did we choose?",
    scope="/project/analytics",
    limit=5,
    depth="shallow",
)
```

Important `Memory` constructor fields:

| Field | Default or behavior | Use when |
| --- | --- | --- |
| `llm` | Model string default is `gpt-5.4-mini`; lazy-initialized for analysis | Scope/category/importance inference or deep recall needs model reasoning. |
| `storage` | `"lancedb"` by default; `"qdrant-edge"` selects edge Qdrant; any other string is treated as a LanceDB path | Choose a local persistent store or inject a custom backend. |
| `embedder` | `None` builds the default OpenAI embedder; dict provider specs are supported; callables are accepted | Keep the same embedder for an existing collection unless you reset/rebuild. |
| `root_scope` | `None`; crews with `memory=True` set `/crew/<crew-name>` automatically | Isolate one crew or application namespace. |
| `read_only` | `False` | Build read-only views or restored memories where writes are disabled. |
| scoring weights | semantic `0.5`, recency `0.3`, importance `0.2`, half-life `30` days | Bias recall toward recent facts, long-lived important facts, or semantic similarity. |

Important methods:

| Method | Notes |
| --- | --- |
| `remember(content, scope=None, categories=None, metadata=None, importance=None, source=None, private=False)` | Synchronous save. If scope/categories/importance are omitted, the LLM analysis layer can infer them. |
| `remember_many(contents, ...)` | Background save. A later `recall()` drains pending writes before searching. |
| `recall(query, scope=None, categories=None, limit=10, depth="deep", source=None, include_private=False)` | `"shallow"` is direct vector search; `"deep"` uses LLM-guided query/scoping. |
| `extract_memories(content)` | Splits raw task output or notes into atomic memory statements. |
| `forget(...)` / `update(...)` | Delete or update selected records. |
| `scope(path)` | Returns a `MemoryScope`, a subtree-restricted read/write view. |
| `slice(scopes=[...], categories=None, read_only=True)` | Returns a `MemorySlice`, a multi-scope recall view. |
| `list_scopes()`, `list_records()`, `info()`, `tree()`, `list_categories()` | Inspect stored memory organization. |
| `reset(scope=None)` | Deletes within a scope, respecting `root_scope` when set. |
| `reset_all()` | Deletes the entire backing memory store, ignoring `root_scope`. |

## Memory in Crews, Agents, and Flows

Use `memory=True` for default crew memory:

```python
from crewai import Agent, Crew, Memory, Process, Task

researcher = Agent(role="Researcher", goal="Find facts", backstory="Careful analyst")
writer = Agent(role="Writer", goal="Write reports", backstory="Concise writer")

task = Task(
    description="Summarize the policy decision.",
    expected_output="One paragraph with the remembered decision.",
    agent=writer,
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[task],
    process=Process.sequential,
    memory=True,
)
```

Crew behavior:

- `memory=True` creates a `Memory` instance and automatically sets a crew root scope like `/crew/<sanitized-crew-name>`.
- If the crew has an `embedder`, CrewAI builds and passes that embedder into default memory.
- If a crew has `chat_llm` or an agent LLM, default memory reuses one of those for analysis where possible.
- Agents use their own `agent.memory` when set; otherwise they use the crew memory when crew memory is enabled.
- Crew execution drains pending background memory saves near shutdown so task output saves are not lost.

Agent-level private memory:

```python
memory = Memory()
researcher = Agent(
    role="Researcher",
    goal="Find private facts",
    backstory="Keeps raw findings isolated.",
    memory=memory.scope("/agent/researcher"),
)
```

Flow memory has helper methods such as `self.remember(...)`, `self.recall(...)`, and `self.extract_memories(...)` available inside flow methods when memory is configured for the flow.

## Scopes and Slices

Scopes are hierarchical paths such as `/`, `/project/alpha`, `/agent/researcher`, or `/customer/acme`. Use shallow, concern-oriented paths: `/project/alpha/decisions` is easier to recall than deeply nested data-type paths.

```python
memory = Memory()

project = memory.scope("/project/alpha")
project.remember("GraphQL is the external API style.", scope="/api")

matches = project.recall("API style")
# Searches under /project/alpha by default.

team_view = memory.slice(
    scopes=["/project/alpha", "/company/policies"],
    read_only=True,
)
policy_matches = team_view.recall("security approval")
```

`MemoryScope` operations treat scopes as relative to the view root. `MemorySlice` recall merges results from all included scopes and re-ranks by score. A read-only slice makes `remember(...)` a no-op; set `read_only=False` only when writes to selected scopes are expected and callers can pass an explicit `scope`.

## Knowledge Quick Reference

CrewAI knowledge sources are attached to agents or crews through `knowledge_sources` or by constructing `Knowledge` directly.

```python
from crewai import Agent, Crew, Process, Task
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource

policy_source = StringKnowledgeSource(
    content="All vendor contracts require security review before signing."
)
handbook_source = TextFileKnowledgeSource(file_paths=["handbook.txt"])

agent = Agent(
    role="Policy Specialist",
    goal="Answer policy questions",
    backstory="Uses indexed policy sources.",
    knowledge_sources=[policy_source],
)

task = Task(
    description="Answer: {question}",
    expected_output="Policy-backed answer.",
    agent=agent,
)

crew = Crew(
    agents=[agent],
    tasks=[task],
    process=Process.sequential,
    knowledge_sources=[handbook_source],
)
```

Initialization behavior:

- Crew-level `knowledge_sources` become a `Knowledge(collection_name="crew", sources=..., embedder=crew.embedder)` object during crew validation.
- Agent-level `knowledge_sources` are initialized during kickoff through `agent.set_knowledge(crew_embedder=crew.embedder)`. If an agent has no embedder and the crew has one, the agent falls back to the crew embedder.
- Agent and crew knowledge use separate collection names. Crew knowledge uses `knowledge_crew`; agent knowledge uses the agent role as the collection suffix.
- `Knowledge.query(query: list[str], results_limit=5, score_threshold=0.6)` searches the collection. Crew convenience methods default to a lower threshold (`0.35`) and limit (`3`).
- `Knowledge.add_sources()` assigns storage to each source, chunks source content, and saves documents into the vector collection.

## Knowledge Source Classes

| Source | Import | Input notes | Dependency notes |
| --- | --- | --- | --- |
| String | `crewai.knowledge.source.string_knowledge_source.StringKnowledgeSource` | `content="..."` | No file dependency; still needs a configured embedder at indexing time. |
| Text file | `TextFileKnowledgeSource` | `file_paths=["name.txt"]` | String paths are resolved under the project `knowledge/` directory. `Path` objects are used directly. |
| PDF | `PDFKnowledgeSource` | `file_paths=["file.pdf"]` | Requires `pdfplumber`. |
| CSV | `CSVKnowledgeSource` | `file_paths=["data.csv"]` | Reads rows into text. |
| Excel | `ExcelKnowledgeSource` | `file_paths=["sheet.xlsx"]` | Requires `pandas` and Excel engine dependencies. |
| JSON | `JSONKnowledgeSource` | `file_paths=["data.json"]` | Converts dict/list structures into readable text. |
| Docling | `CrewDoclingSource` | `file_paths=[local paths or approved HTTP(S) URLs]` | Requires `docling`; supports formats allowed by Docling such as MD, PDF, DOCX, HTML, image, XLSX, and PPTX. HTTP(S) inputs perform retrieval. |

For local file sources, prefer placing files in a project `knowledge/` directory and passing relative file names. Use `Path` objects only when the application deliberately manages absolute or external paths.

## KnowledgeConfig and Query Tuning

`KnowledgeConfig` can tune how much knowledge context is injected and which results qualify. Use it when the default result count or score threshold is too broad or too narrow.

```python
from crewai.knowledge.knowledge_config import KnowledgeConfig

agent = Agent(
    role="Specialist",
    goal="Answer precisely",
    backstory="Uses a narrow retrieval threshold.",
    knowledge_sources=[policy_source],
    knowledge_config=KnowledgeConfig(results_limit=10, score_threshold=0.5),
)
```

Use lower thresholds when valid snippets are missing; raise thresholds when unrelated snippets are injected.

## Reset Behavior

Runtime reset choices:

```python
crew.reset_memories(command_type="memory")
crew.reset_memories(command_type="knowledge")
crew.reset_memories(command_type="agent_knowledge")
crew.reset_memories(command_type="kickoff_outputs")
crew.reset_memories(command_type="all")
```

CLI reset choices:

```bash
crewai reset-memories --memory
crewai reset-memories --knowledge
crewai reset-memories --agent-knowledge
crewai reset-memories --kickoff-outputs
crewai reset-memories --all
```

Deprecated `--long`, `--short`, and `--entities` flags are treated as unified `--memory`. `--all` resets every available crew memory system and flow memory in the current project. Use the smallest reset target that matches the problem: reset `--knowledge` for stale source collections, `--memory` for learned crew/flow facts, and `--all` only when vector dimensions or storage state are broadly inconsistent.

## Source Evidence Notes

This reference distills current CrewAI docs and source behavior for memory, knowledge, reset utilities, and tests into standalone guidance. Original repository docs, tests, and source paths are evidence only; future agents should not need to reopen them to use this sub-skill.
