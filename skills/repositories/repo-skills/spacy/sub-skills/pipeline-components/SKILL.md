---
name: pipeline-components
description: "Assemble and debug spaCy pipeline components, factories, registry
  wiring, and pipe analysis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# pipeline-components

Validated against spaCy 3.8.15 on the installed CPU environment. Optional CUDA, Apple, transformer, and language-extra behavior was not verified here.

Use this sub-skill when the task is about `Language.component`, `Language.factory`, `nlp.add_pipe`, component order, registry lookup, source-vs-factory config wiring, or `nlp.analyze_pipes`.

## Read first

- [references/component-factories-and-registry.md](references/component-factories-and-registry.md) for verified `Language.factory` / `Language.component` signatures and component metadata.
- [references/pipeline-assembly-and-analysis.md](references/pipeline-assembly-and-analysis.md) for pipe ordering, enable/disable/select behavior, and `analyze_pipes` usage.
- [references/built-in-components.md](references/built-in-components.md) for the built-in component catalog and what each one roughly does.
- [references/troubleshooting.md](references/troubleshooting.md) when `add_pipe` raises, config validation fails, or a source component gets mistaken for a factory.
- [scripts/inspect_factories.py](scripts/inspect_factories.py) for a safe registry and analysis smoke check.

## What this sub-skill covers

- Registering stateless components with `Language.component`.
- Registering stateful factories with `Language.factory` and default configs.
- Adding components by name, reordering them, and loading components from source pipelines.
- Reading and interpreting built-in factory metadata.
- Using `nlp.analyze_pipes()` to understand assigns/requires/retokenizes relationships.

## What to route elsewhere

- Tokenization, `Doc`/`Token`/`Span`, matchers/rulers, serialization, and displaCy: `documents-and-visualization`.
- `init config`, `debug config`, `train`, `evaluate`, `convert`, `package`, `validate`: `training-and-cli`.
- Install/import or backend concerns: `install-and-inspect`.
- `spacy project` orchestration: `project-workflows`.

## Fast use pattern

1. Check the exact component signature in the reference.
2. Decide whether the user needs a stateless component or a stateful factory.
3. Use the bundled registry inspection script to confirm the named component exists.
4. Read `pipeline-assembly-and-analysis.md` when order, disable/enable, or source-vs-factory confusion appears.

## Evidence basis

This sub-skill is grounded in the installed `Language` signatures, built-in factory source, pipeline tests, and public docs for component registration and pipeline processing.
