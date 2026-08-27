---
name: spacy
description: "Use spaCy for install checks, document processing, pipeline
  components, training and CLI workflows, and project workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# spaCy

Use this repo skill when the task is about the public `spacy` package, its document model, pipeline assembly, training CLI, or `spacy project` workflows.

## Start here

1. Read [references/package-overview.md](references/package-overview.md) to map the task to the right sub-skill.
2. Read [references/troubleshooting.md](references/troubleshooting.md) if the task may be an install/import/model/backend issue.
3. Read [references/repo-provenance.md](references/repo-provenance.md) when checking whether this skill still matches the checkout that produced it.
4. Run [scripts/spacy_smoke_matrix.py](scripts/spacy_smoke_matrix.py) for a fast cross-cutting health check of the installed package.

## Install and minimal smoke

For a normal runtime install:

```bash
python -m pip install -U spacy
python -m spacy info --silent
python scripts/spacy_smoke_matrix.py
```

If you are intentionally working from a local spaCy source checkout, use editable install only for that local development context:

```bash
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install --no-build-isolation --editable .
```

Optional extras that are only needed for specific workflows are routed to `install-and-inspect`:

- `lookups`
- `transformers`
- `cuda*`
- `apple`
- `ja`, `ko`, `th`

## Route map

- [sub-skills/install-and-inspect/SKILL.md](sub-skills/install-and-inspect/SKILL.md): install/import/version/blank-pipeline/CLI-help and optional backend probes.
- [sub-skills/documents-and-visualization/SKILL.md](sub-skills/documents-and-visualization/SKILL.md): Doc/Token/Span/DocBin, tokenization, matchers/rulers, scoring, and displaCy.
- [sub-skills/pipeline-components/SKILL.md](sub-skills/pipeline-components/SKILL.md): `Language.component`, `Language.factory`, `add_pipe`, registry, and pipe analysis.
- [sub-skills/training-and-cli/SKILL.md](sub-skills/training-and-cli/SKILL.md): config generation, data conversion, debug, train, evaluate, package, and validate.
- [sub-skills/project-workflows/SKILL.md](sub-skills/project-workflows/SKILL.md): `spacy project` clone/assets/run/document/remotes/DVC workflows.

## Good first questions

- "How do I install or verify spaCy in this environment?" -> `install-and-inspect`
- "How do I work with Doc, Span, Token, or matchers?" -> `documents-and-visualization`
- "How do I register a custom component or factory?" -> `pipeline-components`
- "How do I generate configs or run training?" -> `training-and-cli`
- "How do I use a spaCy project template?" -> `project-workflows`

## Evidence and scope

This generated skill is based on spaCy's packaging metadata, public docs, source code, installed-package inspection, and behavior-backed tests from the repository snapshot recorded in `references/repo-provenance.md`.
