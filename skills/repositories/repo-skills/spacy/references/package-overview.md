# spaCy Package Overview

## Purpose

Read this when you need a quick map of the spaCy package surface and which sub-skill owns which workflow.

## Public package shape

Verified from the installed package and source docs:

- Import name: `spacy`
- Distribution name: `spacy`
- Top-level helpers: `spacy.load`, `spacy.blank`, `spacy.prefer_gpu`, `spacy.require_gpu`, `spacy.info`, `spacy.explain`
- Core classes: `Language`, `Vocab`, `Example`
- Core object model: `Doc`, `Token`, `Span`, `DocBin`
- Main subpackages: `cli`, `language`, `tokens`, `matcher`, `pipeline`, `training`, `displacy`, `lang`, `kb`, `ml`

## Route map

| Workflow family | Owning sub-skill |
| --- | --- |
| Install/import/version/blank pipeline/CLI entry-point/model-package/backend probes | `sub-skills/install-and-inspect/` |
| Doc/Token/Span/DocBin/tokenization/matching/displacy | `sub-skills/documents-and-visualization/` |
| `Language.component`, `Language.factory`, `add_pipe`, registry, pipe analysis | `sub-skills/pipeline-components/` |
| `init config`, `debug config/data`, `convert`, `train`, `evaluate`, `package`, `validate` | `sub-skills/training-and-cli/` |
| `spacy project` clone/assets/run/document/remotes/DVC | `sub-skills/project-workflows/` |

## How the package fits together

- `spacy.blank()` creates a language object with tokenizer/language data but no pretrained weights.
- `spacy.load()` loads an installed model package or saved pipeline directory.
- `Language` owns the vocabulary, tokenizer, and pipeline order.
- `Doc`/`Token`/`Span` represent processed text and annotations.
- `Matcher`/`EntityRuler`/`SpanRuler` provide rule-based extraction.
- `training` and `cli` coordinate config-driven model building and data conversion.
- `project` workflows compose repeatable command graphs around configs, assets, and outputs.

## Read this together with

- `references/troubleshooting.md` for cross-cutting install/import/model/backend problems.
- `sub-skills/*/references/` for workflow-specific details.
- `references/repo-provenance.md` when checking whether the skill still matches the checkout that produced it.
