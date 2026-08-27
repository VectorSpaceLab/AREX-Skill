---
name: checks-evals
description: "Build and run Giskard checks, scenarios, suites, judges,
  generators, custom checks, serialization, and JUnit export."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# checks-evals

Use this sub-skill for the `giskard.checks` package: evaluation scenarios, suites,
deterministic checks, LLM-as-judge checks, input generators, JSONPath extraction,
custom check registration, serialization, and JUnit export.

## Route here when

- Building `Scenario(...).interact(...).check(...)` flows or running `Suite.run(...)`.
- Choosing deterministic checks such as `Equals`, comparison checks,
  `StringMatching`, `RegexMatching`, `JsonValid`, `AllOf`, `AnyOf`, `Not`, or
  one-off `from_fn` / `FnCheck` checks.
- Using optional or model-backed checks such as `SemanticSimilarity`,
  `Readability`, `RegoPolicy`, `Groundedness`, `Conformity`, `Contradiction`,
  `AnswerRelevance`, `Toxicity`, or `LLMJudge`.
- Generating scenario inputs with `LLMGenerator`, `UserSimulator`, or
  `DatasetInputGenerator`.
- Debugging `Trace` / `Interaction` data and JSONPath selectors such as
  `trace.last.inputs`, `trace.last.outputs`, and `trace.last.metadata.context`.
- Defining reusable custom checks with `@Check.register("...")`,
  `JSONPathStr`, and `MISSING` defaults, then round-tripping with
  `model_validate(...)`.
- Exporting suite results as JUnit XML.

## Route elsewhere

- Provider aliases, provider SDK extras, live completion/embedding credentials,
  and `giskard.llm` client behavior: use `../llm-providers/SKILL.md`.
- Agent workflow construction, prompt templates, tools, and `Generator` internals:
  use `../agents-workflows/SKILL.md`.
- Vulnerability scans, RAG quality scans, `generate_suite`, or scan generator
  registries: use `../scan-redteam/SKILL.md`.
- Installation, split-package imports, telemetry controls, and cross-package
  runtime setup: use `../runtime-setup/SKILL.md`.

## Operating checklist

1. Import public symbols from `giskard.checks`; do not use a `giskard_checks`
   import namespace.
2. Start with deterministic checks when provider keys or a default generator are
   unavailable.
3. Bind target output deliberately: pass `outputs=` to `interact(...)`, or bind a
   target on the `Scenario`, `Suite`, or `run(...)` call.
4. Prefer `trace.last.*` JSONPath selectors for current-turn data; use explicit
   structured field paths when outputs are dictionaries or models.
5. Pass an explicit `generator=` or configure `set_default_generator(...)` before
   running LLM judges or LLM-backed input generators; configure an embedding
   model before provider-backed `SemanticSimilarity` runs.
6. Import every custom registered class before `model_validate(...)` of a
   serialized scenario, suite, test case, check, interaction spec, or input
   generator.
7. Use the bundled smoke script for a no-key installed-package sanity check.

## References and Script

- [API reference](references/api-reference.md) for public APIs, defaults,
  status fields, and result/export surfaces.
- [Workflows](references/workflows.md) for Scenario, Suite, judge, generator,
  serialization, and JUnit recipes.
- [Custom checks](references/custom-checks.md) for custom check authoring,
  JSONPath field typing, registration, and tests.
- [Troubleshooting](references/troubleshooting.md) for failure modes and
  diagnostics.
- [scripts/run_checks_smoke.py](scripts/run_checks_smoke.py) for a deterministic
  installed-package smoke that sets telemetry opt-out before import, makes no
  network/API calls, and exits nonzero if `Scenario`, `StringMatching`,
  `Equals`, or `Suite.run` behavior is broken.

Run the smoke from any current working directory with a Python environment that
has `giskard.checks` installed:

```bash
python path/to/sub-skills/checks-evals/scripts/run_checks_smoke.py
```
