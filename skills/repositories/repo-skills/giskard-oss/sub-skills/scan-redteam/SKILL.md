---
name: scan-redteam
description: "Routes giskard.scan vulnerability, quality, suite-generation,
  knowledge-base, prompt-injection, and third-party red-team scan tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Scan and Red-Team Workflows

Use this sub-skill when the task is about `giskard.scan`: vulnerability scans,
RAG quality scans, generated scan suites, scan scenario generators, prompt
injection datasets, `KnowledgeBase`, or optional third-party scanners such as
garak, deepteam, and private lidar.

## Read First

- [API reference](references/api-reference.md) for verified scan entry points,
  signatures, generator registries, `KnowledgeBase`, and item listing.
- [Workflows](references/workflows.md) for planning and running native Giskard
  scans safely, including target design, concurrency, knowledge bases, and
  default generator/provider prerequisites.
- [Third-party integrations](references/third-party-integrations.md) for
  `third_party_scan(tool=...)`, optional extras, supported item names, and skip
  behavior for garak, deepteam, and lidar.
- [Troubleshooting](references/troubleshooting.md) for missing credentials,
  empty knowledge bases, network/Hugging Face issues, commercial-use flags,
  target state safety, and optional scanner failures.
- [scripts/inspect_scan_api.py](scripts/inspect_scan_api.py) for a safe
  installed-package inspection helper. It imports `giskard.scan`, prints public
  versions/items, builds a tiny `KnowledgeBase`, and checks optional scanner
  availability without running scans or providers.

## Typical Triggers

- "Run or configure a `vulnerability_scan` for my chatbot."
- "Plan a RAG `quality_scan` with a knowledge base."
- "Generate a scan `Suite` from specific scenario generators."
- "List built-in scan generators or garak/deepteam probes."
- "Use prompt-injection or Hugging Face dataset scenarios."
- "Choose between native Giskard, garak, deepteam, and lidar scanning."
- "Explain why scan results are skipped, errored, or grouped unexpectedly."

## Boundary and Routing

Include here:

- `vulnerability_scan`, `quality_scan`, `generate_suite`, and
  `DEFAULT_TARGET_MODE`.
- `KnowledgeBase`, `Document`, `KnowledgeBase.from_texts`, lazy embeddings, and
  empty-knowledge-base behavior.
- `ScenarioGenerator`, `SuiteGeneratorRegistry`, built-in vulnerability and
  quality generator registries, `PromptInjectionScenarioGenerator`, and
  `HuggingFaceDatasetScenarioGenerator`.
- `list_scan_items("giskard" | "garak" | "deepteam")` and
  `third_party_scan(tool="garak" | "deepteam" | "lidar")` prerequisites.
- Scan execution controls: `max_scenarios`, `seed`, `group_by`, `parallel`,
  `max_concurrency`, `return_exception`, `target_mode`, and
  vulnerability-only `commercial_use`.

Route elsewhere:

- Suite and check-result interpretation, custom checks, JUnit export, and
  deterministic `Scenario`/`Suite` details ->
  [checks-evals](../checks-evals/SKILL.md).
- Default generator/provider keys, `provider/model` routing, provider extras,
  and live LLM errors -> [llm-providers](../llm-providers/SKILL.md).
- Designing async targets, agent workflows, tools, prompt templates, and
  stateful chat wrappers -> [agents-workflows](../agents-workflows/SKILL.md).

## Operating Rule

Do not start an expensive or live red-team scan until the user has confirmed the
provider credentials, network/commercial-use stance, target concurrency safety,
and optional scanner extras needed by the selected workflow. For no-key
inspection, run only the bundled `inspect_scan_api.py` helper.
