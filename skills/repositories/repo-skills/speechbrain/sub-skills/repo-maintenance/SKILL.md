---
name: repo-maintenance
description: "Guides SpeechBrain repository maintenance, focused tests, recipe
  consistency metadata, docs/performance generation, linting, and contribution
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SpeechBrain repository maintenance

Use this sub-skill when modifying the SpeechBrain repository, adding or updating recipes/templates, changing public APIs used by HyperPyYAML, running focused tests, generating docs, or updating performance tables.

## Route map

| Task | Read |
| --- | --- |
| Choose focused tests for a code, recipe, docs, or API change. | `references/testing.md` |
| Add/update recipe CSV rows, debug flags, result/HF links, mandatory files, or recipe metadata. | `references/recipe-consistency.md` |
| Build docs, update generated performance tables, or maintain docs links. | `references/docs-and-performance.md` |
| Diagnose maintainer CI, lint, recipe, docs, or URL/HF check failures. | `references/troubleshooting.md` |

## Default maintainer stance

- Prefer focused tests first; do not run all recipe/HF/network checks by default.
- If a Python API signature changes, search HyperPyYAML usages and recipes, not just direct Python imports.
- If a recipe changes, update the corresponding `tests/recipes/*.csv` row and ensure `test_debug_flags` still work.
- If a public workflow changes, update docs/tutorial references and tests together.
- Treat source repo scripts as maintainer tools, not runtime dependencies for the generated repo skill.

## Common focused commands

```bash
pytest tests/consistency
pytest tests/unittests/test_core.py -q
pytest tests/unittests/test_audio_io.py -q
pytest --doctest-modules speechbrain
```

Use broader wrappers such as recipe tests, URL checks, and Hugging Face checks only when their side effects and runtime are acceptable.
