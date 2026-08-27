# Native Scan Workflows

## Purpose

Use this guide to plan and execute native `giskard.scan` workflows without
reopening repository docs. It distinguishes safe inspection from live red-team
execution, and it shows where provider configuration, target design, and result
interpretation are owned by sibling sub-skills.

## Safe Preflight Before Any Scan

1. Verify that the installed package exposes the expected scan APIs without
   running a scan:

   ```bash
   python scripts/inspect_scan_api.py
   ```

   The helper imports `giskard.scan`, lists built-in generator names, creates a
   tiny `KnowledgeBase`, and reports optional scanner availability. It does not
   call providers, download datasets, or invoke a target.

2. Decide whether the target is single-turn or multi-turn:
   - Use `target_mode="singleturn"` if each call is independent and no chat
     history is available. Multi-turn-only generators/attacks will skip.
   - Use `target_mode="multiturn"` (the default) when the target can preserve
     conversation state across scenario turns.

3. Decide whether the target is safe under concurrency:
   - If the target has shared mutable state, session caches, local file writes,
     or non-thread-safe wrappers, start with `parallel=False`.
   - If the target is stateless or explicitly concurrency-safe, use
     `parallel=True` with a bounded `max_concurrency` that matches provider and
     application limits.

4. Confirm provider prerequisites before live generation or judging. Many native
   scan generators use `LLMGenerator`, `LLMJudge`, `Conformity`, embeddings, or
   quality recommendations, so they need a configured Giskard default generator
   and provider credentials. Provider setup belongs in
   [llm-providers](../../llm-providers/SKILL.md).

5. Confirm the result contract. Scan helpers return `SuiteResult` from
   `giskard.checks`; result grouping, pass/fail/error/skip semantics, trace
   inspection, and export belong in [checks-evals](../../checks-evals/SKILL.md).

## Target Design Checklist

A scan target may be a callable accepted by `giskard.checks.Suite.run` or a
Giskard target/workflow object. For robust scan execution:

- Keep target inputs and outputs serializable and easy to inspect in traces.
- For a RAG agent, preserve retrieved context in trace metadata when possible;
  this helps groundedness and troubleshooting even when the scan itself builds
  scenarios from a separate `KnowledgeBase`.
- Separate per-conversation state from global process state. Scenario execution
  can be parallel, and third-party adapters may call the target from worker
  threads.
- If wrapping an agent workflow, follow [agents-workflows](../../agents-workflows/SKILL.md)
  for async workflow, tool, and state handling.

Minimal async target shape:

```python
async def target(inputs: str) -> str:
    return await call_my_agent(inputs)
```

For stateful targets, prefer a wrapper that creates fresh conversation/session
state per scenario or run `parallel=False` until thread/session safety is proven.

## Vulnerability Scan Workflow

Use `vulnerability_scan` for red-team scenario generation across harmful content,
prompt injection, jailbreak-style attacks, and Hugging Face-backed attack
datasets.

```python
import asyncio
from giskard.scan import vulnerability_scan

async def target(inputs: str) -> str:
    return await call_my_agent(inputs)

async def main() -> None:
    result = await vulnerability_scan(
        target=target,
        description="Customer-support assistant that answers order questions.",
        languages=["en"],
        max_scenarios=8,
        seed=42,
        group_by="threat-type",
        parallel=False,              # switch to True only after target safety review
        max_concurrency=None,
        return_exception=True,
        target_mode="singleturn",
        commercial_use=True,         # excludes non-commercial dataset generators
    )
    print(result.passed, result.pass_rate)

asyncio.run(main())
```

Important choices:

- `commercial_use=False` includes all registered vulnerability generators,
  including generators backed by datasets marked non-commercial. Use
  `commercial_use=True` when commercial-use restrictions matter.
- `target_mode="singleturn"` removes multi-turn-only attacks such as Crescendo
  and GOAT from generated suites. This is better than pretending a stateless
  endpoint can preserve conversation history.
- `return_exception=True` is useful during exploratory scans because one failed
  generated input can be recorded as an error while other scenarios continue.
  Use `False` when any generation/execution error should stop the scan.

## Quality Scan Workflow for RAG Targets

Use `quality_scan` for document-grounded hallucination, sycophancy,
split-question, multi-topic, and out-of-scope quality scenarios.

```python
import asyncio
from giskard.scan import KnowledgeBase, quality_scan

async def rag_target(inputs: str) -> str:
    return await call_my_rag_agent(inputs)

kb = KnowledgeBase.from_texts([
    "Returns are accepted within 30 days with a receipt.",
    "Premium support is available from Monday to Friday.",
])

async def main() -> None:
    result = await quality_scan(
        target=rag_target,
        description="RAG assistant for customer policy questions.",
        languages=["en"],
        knowledge_base=kb,
        max_scenarios=6,
        seed=7,
        group_by="component",
        parallel=False,
        return_exception=True,
        target_mode="multiturn",
    )
    print(result.recommendation or "No recommendation generated")

asyncio.run(main())
```

Knowledge-base guidance:

- Use several semantically distinct, non-empty text chunks. Empty strings are
  discarded by `KnowledgeBase.from_texts`; all-empty input raises `ValueError`.
- `quality_scan(knowledge_base=None)` or an empty raw list emits a runtime
  warning and the knowledge-base generators return no scenarios.
- Creating the `KnowledgeBase` does not compute embeddings. Retrieval inside
  quality generators computes missing embeddings lazily, so a live embedding
  provider or a controlled embedding model is required unless documents already
  carry valid embeddings.
- `MultiTopicScenarioGenerator` needs at least two documents. `SplitQuestions`
  and `MultiTopic` are multi-turn and skip under `target_mode="singleturn"`.

## Generate a Suite Without Running the Target

Use `generate_suite` when the task is to build or inspect a `Suite` first, then
run it later with explicit `Suite.run` controls.

```python
import asyncio
from giskard.scan import PromptInjectionScenarioGenerator, generate_suite

async def main() -> None:
    suite = await generate_suite(
        description="Support chatbot for account help.",
        languages=["en"],
        generators=[PromptInjectionScenarioGenerator()],
        max_scenarios=3,
        seed=123,
        target_mode="singleturn",
    )
    print(suite.name, len(suite.scenarios))

asyncio.run(main())
```

This only generates or loads scenarios. Running `suite.run(target=...)` is the
step that invokes the target. Some generators also invoke LLMs during suite
generation, so a generated-suite step can still need provider credentials even
before target execution.

## Customize Generator Registries

Use custom registries for repeatable scan profiles, but keep registry mutation
scoped to a test, notebook, or process setup block because registries are mutable
module-level objects.

```python
from giskard.scan import (
    PromptInjectionScenarioGenerator,
    SuiteGeneratorRegistry,
    vulnerability_suite_generator_registry,
)

registry = SuiteGeneratorRegistry()
registry.register(PromptInjectionScenarioGenerator())
print([type(g).__name__ for g in registry.generators()])

# The default vulnerability registry can be inspected, but avoid mutating it in
# reusable library code unless every caller expects that process-wide change.
print([type(g).__name__ for g in vulnerability_suite_generator_registry.generators()])
```

If a task needs a custom `ScenarioGenerator`, implement the generator contract in
[the API reference](api-reference.md), then pass instances or classes to
`generate_suite`. Do not register duplicate equivalent generator instances; the
registry raises `ValueError`.

## Prompt-Injection and Dataset Workflows

- `PromptInjectionScenarioGenerator()` loads a bundled prompt-injection JSONL
  dataset and tags scenarios with prompt-injection/OWASP metadata. Loading is
  local, but the scenarios contain LLM-backed interactions and checks when run.
- `HuggingFaceDatasetScenarioGenerator(repo_id=..., repo_allow_commercial_use=...)`
  reads dataset metadata and downloads matching language files from Hugging Face
  Hub. It skips requested languages that are not present and returns no
  scenarios for recognized Hub outage conditions.
- For commercial contexts, prefer `vulnerability_scan(..., commercial_use=True)`
  or explicitly choose dataset generators whose `repo_allow_commercial_use` is
  true. The flag filters generator selection; it does not legal-review your use
  of downstream scan outputs.

## Result Interpretation Handoff

After a scan returns:

- Use `result.group_by("threat-type")`, `result.group_by("component")`, or the
  grouping key used by your scan to summarize failures.
- Treat skipped results as operational signals, not passes. Skips can mean
  single-turn filtering, missing optional extras, unsupported item names,
  missing detector credentials, network/HF unavailability, or an intentionally
  empty generator set.
- For detailed result navigation, check status counts, traces, check messages,
  and export options in [checks-evals](../../checks-evals/SKILL.md).
