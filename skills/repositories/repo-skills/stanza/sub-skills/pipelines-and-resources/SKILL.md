---
name: pipelines-and-resources
description: "Operate Stanza pipelines, multilingual routing, resource
  downloads, caches, and safe smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---
# pipelines-and-resources

Use this sub-skill for Stanza pipeline and resource tasks that need concrete commands without reopening source.

## Handles
- `stanza.Pipeline` and `stanza.MultilingualPipeline`
- `stanza.download`, `DownloadMethod`, and local resource/cache inspection
- processor, package, and device selection
- string, list, and `Document` inputs
- batching, `process_many`, and `stream`
- avoiding accidental downloads in offline or restricted runs

## Route elsewhere
- Field-level `Document` or CoNLL-U work: `documents-and-conllu`
- Java Stanford CoreNLP client work: `corenlp-client`
- Training, datasets, and model fitting: `training-and-data-prep`
- Demo UI or notebook adaptation: `visualization-and-demos`

## Use these references
- `references/api-reference.md`
- `references/resources-and-cache.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- `scripts/pipeline_smoke.py`

The details are distilled from Stanza 1.14.0 source, tests, demos, and installed-package inspection; use the root provenance file when checking staleness.
