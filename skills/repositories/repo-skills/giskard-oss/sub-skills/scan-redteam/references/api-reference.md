# Scan API Reference

## Purpose

Read this when a task needs exact `giskard.scan` entry points, parameters,
registry behavior, or knowledge-base semantics. Details here were verified from
installed package inspection and source-backed public API tests; examples are
self-contained and do not require the original repository checkout.

## Import Surface

```python
from giskard.scan import (
    DEFAULT_TARGET_MODE,
    Document,
    KnowledgeBase,
    PromptInjectionScenarioGenerator,
    HuggingFaceDatasetScenarioGenerator,
    generate_suite,
    list_scan_items,
    quality_scan,
    third_party_scan,
    vulnerability_scan,
)
```

`DEFAULT_TARGET_MODE == "multiturn"`. The shared target modes are
`"multiturn"` and `"singleturn"`; single-turn mode skips generators or attacks
that are inherently multi-turn and caps other turn budgets to one.

## Native Scan Entry Points

All three suite-generation entry points are `async` and should be awaited or run
inside an event loop.

| API | Verified signature | Returns | Key behavior |
| --- | --- | --- | --- |
| `generate_suite` | `generate_suite(description: str, languages: list[str], generators: Sequence[ScenarioGenerator | type[ScenarioGenerator]], max_scenarios=None, seed=42, target_mode="multiturn", knowledge_base=None) -> Suite` | `giskard.checks.Suite` | Runs the supplied generator classes/instances concurrently, distributes `max_scenarios` across generators with a seeded NumPy RNG, and wraps the generated scenarios in `Suite(name="Scenarios")`. Generation parallelism is always on; execution parallelism is controlled later by `Suite.run`. |
| `vulnerability_scan` | `vulnerability_scan(target, description: str, languages: list[str], *, max_scenarios=None, seed=42, group_by="threat-type", parallel=True, max_concurrency=None, return_exception=False, target_mode="multiturn", commercial_use=False) -> SuiteResult` | `giskard.checks.SuiteResult` | Builds from `vulnerability_suite_generator_registry`, runs the suite against `target`, prints a report grouped by `group_by`, and returns the result. `commercial_use=True` filters out generators whose datasets do not permit commercial use. |
| `quality_scan` | `quality_scan(target, description: str, languages: list[str], *, knowledge_base=None, max_scenarios=None, seed=42, group_by="component", parallel=True, max_concurrency=None, return_exception=False, target_mode="multiturn") -> SuiteResult` | `giskard.checks.SuiteResult` | Builds from `quality_suite_generator_registry`, normalizes `knowledge_base`, runs the suite, attempts to generate a quality recommendation, prints a report grouped by `group_by`, and returns a copied result with `recommendation`. |

Shared options:

- `max_scenarios`: total upper bound distributed across generators. `None`
  lets each generator use its default; `0` can produce an empty suite.
- `seed`: reproducibility seed for scenario generation and budget allocation.
- `group_by`: annotation key used by the printed report; pass `None` for an
  ungrouped report.
- `parallel`: scan helpers pass this to `Suite.run`; it controls target
  execution, not suite generation. Default is `True` on scans.
- `max_concurrency`: cap for parallel target execution. `None` means no explicit
  cap from Giskard; provider limits or target limits become the real cap.
- `return_exception`: when `True`, scenario input-generation failures are
  recorded as errored results where supported by suite execution; when `False`,
  failures propagate.
- `target_mode`: `"multiturn"` by default. Use `"singleturn"` for targets that
  cannot preserve conversation state.
- `commercial_use`: vulnerability-only. Use `True` when the scan output will be
  used in a commercial context and non-commercial datasets must be excluded.

For how to interpret `SuiteResult`, grouped reports, pass/fail/error/skip, and
checks, read [checks-evals](../../checks-evals/SKILL.md).

## Knowledge Base APIs

| API | Verified signature | Behavior and caveats |
| --- | --- | --- |
| `Document` | `Document(*, content: str, embeddings: list[float] | None = None, tags: list[str] | None = None)` | Stores one text chunk plus optional precomputed embedding and caller tags. |
| `KnowledgeBase` | `KnowledgeBase(*, embedding_model=None, documents: tuple[Document, ...])` | Frozen collection of non-empty documents used by quality generators. Documents are a tuple; do not plan to append after creation. |
| `KnowledgeBase.from_texts` | `KnowledgeBase.from_texts(texts: list[str]) -> KnowledgeBase` | Wraps each raw text as a `Document`. It does not compute embeddings at construction time. Whitespace-only documents are dropped; all-empty input raises `ValueError`. |

Quality scans accept `knowledge_base` as either an existing `KnowledgeBase`, a
`list[str]`, or `None`. Pass a list of text chunks, not a bare string. Empty or
missing input emits a runtime warning and knowledge-base scenarios are skipped.

Embeddings are lazy. They are computed only when retrieval is needed, such as
`closest_documents(...)` or `closest_documents_to_text(...)`. If any document is
missing embeddings, the knowledge base recomputes all embeddings in one batch to
avoid mixing vectors from different models. Retrieval validates shape,
finite values, and non-zero vectors. If you need deterministic/no-provider
quality generation, provide precomputed `Document(..., embeddings=[...])` or a
controlled embedding model; otherwise default embedding/provider configuration
belongs in [llm-providers](../../llm-providers/SKILL.md).

## Generator Base and Registries

| API | Behavior |
| --- | --- |
| `ScenarioGenerator` | Base class with `generate_scenario(context, max_scenarios=None, rng=None, target_mode=DEFAULT_TARGET_MODE)`. Subclasses return `giskard.checks.Scenario` objects. |
| `SuiteGeneratorRegistry` | Mutable registry with `register(...)`, `unregister(...)`, `clear()`, and `generators(commercial_use=False)`. Registers generator classes or instances; duplicate equivalent instances raise `ValueError`. |
| `vulnerability_suite_generator_registry` | Default vulnerability generator registry used by `vulnerability_scan`. |
| `quality_suite_generator_registry` | Default quality generator registry used by `quality_scan`. |
| `list_scan_items("giskard")` | Returns sorted built-in Giskard scenario generator class names from the quality and vulnerability registries. |

Public generator classes exposed by `giskard.scan` and `giskard.scan.generators`:

| Generator | Main use | Notes |
| --- | --- | --- |
| `AdversarialScenarioGenerator(max_turns=3)` | Harmful-content, bias, misinformation, unauthorized-advice rules generated by an LLM. | Requires a working default generator during scenario generation. `target_mode="singleturn"` caps generated scenario turns to one. |
| `CrescendoAttackScenarioGenerator(max_turns=10)` | Multi-turn Crescendo-style harmful-content attacks. | Multi-turn only; skipped when `target_mode="singleturn"`. |
| `GOATAttackScenarioGenerator(max_turns=10)` | Multi-turn GOAT attack strategies. | Multi-turn only; skipped when `target_mode="singleturn"`. |
| `GCGInjectionScenarioGenerator(repo_id="giskardai/harmbench-scenarios", repo_allow_commercial_use=True)` | Adds GCG adversarial suffixes to harmful prompts loaded from a Hugging Face dataset. | Requires Hugging Face Hub access unless cached; suffixes are English-tuned. |
| `PromptInjectionScenarioGenerator(tags=[], dataset_name="prompt_injection")` | Loads bundled prompt-injection scenarios. | No dataset download for loading, but generated scenarios still contain LLM-backed interactions/checks at execution time. |
| `HuggingFaceDatasetScenarioGenerator(tags=[], repo_id: str, repo_allow_commercial_use=True)` | Loads scenarios from a Hugging Face dataset repository. | Reads dataset-card configs by language and downloads matching JSONL files; outage/network errors are logged and return no scenarios for recognized hub outage cases. |
| `HallucinationScenarioGenerator(context_documents=4, max_turns=3)` | Direct document-grounded hallucination quality scenarios. | Requires a non-empty knowledge base and embeddings when retrieval starts. |
| `SycophancyScenarioGenerator(context_documents=4, max_turns=3)` | Pressure-with-false-premise quality scenarios. | Requires a non-empty knowledge base and default LLM-backed user simulation/judging. |
| `SplitQuestionsScenarioGenerator(context_documents=4, max_turns=2)` | Two-message document-grounded questions. | Multi-turn only; skipped in single-turn mode. |
| `MultiTopicScenarioGenerator(context_documents=4, max_turns=3)` | Multi-turn questions over multiple knowledge-base topics. | Needs at least two documents and is skipped in single-turn mode. |
| `OutOfScopeScenarioGenerator(context_documents=4, max_turns=3)` | Questions about plausible absent topics. | Uses default generator and embeddings for candidate generation and validation. |

## Third-Party Discovery API

| API | Verified signature | Notes |
| --- | --- | --- |
| `list_scan_items` | `list_scan_items(tool: str, *, include_inactive=False) -> list[str]` | `"giskard"` lists scenario generator names. `"garak"` lists garak probe plugin names and may include inactive probes with `include_inactive=True`. `"deepteam"` lists supported vulnerability and attack names. Optional dependencies must be installed for garak/deepteam listing. |
| `third_party_scan` | `third_party_scan(target, tool: Literal["garak", "lidar", "deepteam"], *, description: str, languages: list[str] | None = None, **kwargs) -> SuiteResult` | Dispatches to optional scanners. Public docs support garak and deepteam; `tool="lidar"` is a private Giskard integration path for environments that already have lidar installed. See [third-party integrations](third-party-integrations.md). |

Unknown tool names raise `ValueError`. Unknown keyword arguments passed through
`third_party_scan` raise `TypeError` with the selected tool name.
