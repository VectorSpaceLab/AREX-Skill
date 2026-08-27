---
name: stanza
description: "Use Stanza for neural NLP pipelines, CoreNLP client workflows,
  CoNLL-U documents, training data, and demos."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Stanza Repo Skill

Use this skill when a task involves the `stanza` Python NLP package from the Stanford NLP Group: neural NLP pipelines, model resources, CoNLL-U documents, Java Stanford CoreNLP access, Stanza model training/data preparation, or demo/visualization adaptation.

## First checks

- Install/use a normal Python package environment with `stanza` importable.
- Minimal import smoke:

```python
import stanza
from stanza import Pipeline, MultilingualPipeline, Document
from stanza.utils.conll import CoNLL
print(stanza.__version__)
```

- Run `scripts/check_environment.py --help` for a no-download diagnostic helper.
- Read `references/repo-provenance.md` before deciding whether this skill is current for a checkout.
- Read `references/troubleshooting.md` when install/import, resource, optional dependency, CoreNLP, or training setup fails.

## Route by task

| Task intent | Read |
| --- | --- |
| Build or debug `stanza.Pipeline`, `MultilingualPipeline`, processor lists, model packages, model caches, downloads, offline mode, GPU/CPU selection, batching, or streaming | `sub-skills/pipelines-and-resources/SKILL.md` |
| Parse, write, validate, or manipulate Stanza `Document`, `Sentence`, `Token`, `Word`, NER/coref fields, serialized docs, or CoNLL-U | `sub-skills/documents-and-conllu/SKILL.md` |
| Use Java Stanford CoreNLP through Stanza: `CoreNLPClient`, server lifecycle, external server mode, properties, output formats, Semgrex/TokensRegex/Tregex/Ssurgeon/Tsurgeon, protobuf | `sub-skills/corenlp-client/SKILL.md` |
| Plan custom model training, evaluation, data conversion, pretrains, charlms, training wrappers, UD/NER/constituency/coref data roots, or safe training command construction | `sub-skills/training-and-data-prep/SKILL.md` |
| Adapt demos, notebooks, dependency/NER visualization, Streamlit/browser visualizers, or produce static HTML from existing annotations | `sub-skills/visualization-and-demos/SKILL.md` |

## Package entry points to remember

- `stanza.download(lang=..., processors=..., package=..., model_dir=..., proxies=...)` stages model resources.
- `stanza.Pipeline(lang='en', processors='tokenize,pos,lemma,depparse', download_method=...)` builds the neural pipeline.
- `stanza.MultilingualPipeline(...)` detects language and routes batches to per-language pipelines.
- `stanza.Document` and `stanza.utils.conll.CoNLL` handle document objects and CoNLL-U conversion.
- `stanza.server.CoreNLPClient` talks to a Java Stanford CoreNLP server.
- `python -m stanza.models.<module>` and `python -m stanza.utils.training.run_<task>` expose training/evaluation helpers.

## Safety and boundaries

- Model downloads, CoreNLP distribution downloads, word-vector downloads, notebook execution, Java server startup, W&B logging, and full model training are side-effectful. Make them explicit and obtain task approval before running them.
- Do not assume GPU is required. Stanza supports CPU for functional workflows; CUDA is optional acceleration unless a user specifically asks for GPU validation.
- Do not use this runtime skill as a link farm back to a source checkout. The references and scripts here are self-contained for Stanza 1.14.0 behavior.

## References

- `references/package-overview.md` summarizes package surfaces, dependencies, and extras.
- `references/troubleshooting.md` covers cross-cutting failures and routes to sub-skill troubleshooting.
- `references/repo-provenance.md` records the source snapshot and evidence paths.
- `references/repo-routing-metadata.json` provides structured router metadata for managed import tooling.
