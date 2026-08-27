# Stanza Repository Provenance

- Schema: `disco.repo-provenance.v1`

## Source baseline

- Upstream project: Stanford NLP Group Stanza, `https://github.com/stanfordnlp/stanza`
- Package distribution and import package: `stanza`
- Package version in source: `1.14.0`
- Source commit: `1f4bfdd2bff400969444cf9f290d402448c9d6d5`
- Source branch at construction: `main`
- License: Apache License 2.0
- Construction state: the generated `skills/` tree is production output and is not part of the upstream package API.

## Evidence paths used

The skill was derived from these source-relative surfaces:

- `README.md`
- `setup.py`
- `stanza/__init__.py`
- `stanza/_version.py`
- `stanza/pipeline/core.py`
- `stanza/resources/common.py`
- `stanza/models/common/doc.py`
- `stanza/utils/conll.py`
- `stanza/server/client.py`
- `stanza/utils/training/run_*.py`
- `demo/`
- `stanza/tests/`

These paths are provenance evidence, not runtime links. The operating skill is self-contained under this skill directory.

## Included scope

- neural `Pipeline` and `MultilingualPipeline` construction, processor selection, devices, model packages, and resource/cache behavior;
- `Document`, `Sentence`, `Token`, and `Word` manipulation plus CoNLL-U conversion;
- the Python `CoreNLPClient`, server lifecycle, request properties, pattern engines, and protobuf-facing workflows;
- model training/evaluation command construction and corpus preparation;
- bundled demo and visualization adaptation;
- installation, optional dependencies, environment checks, and troubleshooting.

## Excluded scope

- model weights, language resource archives, training corpora, word vectors, and Stanford CoreNLP distributions;
- Java server processes, downloaded jars, cache contents, generated checkpoints, and experiment logs;
- private construction environments and review reports under `skills/tests/`;
- guarantees for APIs introduced after the source commit above.

## Runtime baseline and boundaries

The skill targets Stanza 1.14.0 and Python 3.9 or newer. The package metadata requires PyTorch and the base Python dependencies summarized in `package-overview.md`. CUDA is optional for ordinary inference and is not treated as a baseline requirement. Live neural pipelines require separately downloaded language resources. Live CoreNLP annotation additionally requires Java and a compatible Stanford CoreNLP distribution. The root environment checker performs no downloads and starts no servers.

## Refresh triggers

Refresh this skill when any of the following change:

- the package version, public exports, or signatures for pipelines, documents, downloads, CoNLL-U, or `CoreNLPClient`;
- the resources manifest, package naming, cache layout, model URL behavior, or `DownloadMethod` semantics;
- document fields or CoNLL-U serialization rules;
- CoreNLP server/protobuf compatibility or pattern-engine APIs;
- training entry points, corpus layouts, dependency extras, or visualization helpers.
