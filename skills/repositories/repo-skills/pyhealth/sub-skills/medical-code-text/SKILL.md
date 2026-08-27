---
name: medical-code-text
description: "Guides PyHealth medical-code ontology lookup and mapping plus NLP,
  text, vision, audio, EEG, signal, and multimodal processing with explicit
  optional-resource gates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Medical code, text, and multimodal workflows

Use this route for ICD/CCS/ATC/NDC/RxNorm/UMLS lookup or mapping, clinical text
and NLP, text/image/audio/signal processors, or multimodal embeddings.

## Workflow

1. Identify the code vocabulary or modality and whether local mapping/model
   assets already exist. Read [code maps](references/code-maps.md) or
   [NLP/multimodal](references/nlp-and-text.md).
2. Run `scripts/optional_dependency_probe.py` without downloading anything.
   Install `[nlp]` for NLP extras and `[graph]` for graph paths only when needed.
3. Use `InnerMap.load(vocabulary)` for ontology lookup or
   `CrossMap.load(source_vocabulary, target_vocabulary)` for cross-system maps;
   validate code-system names and cache/network policy first.
4. Distinguish local tokenization/processor checks from pretrained model weight
   acquisition. Route model orchestration to [models-training](../models-training/SKILL.md)
   and generic processor/data schemas to [data-pipelines](../data-pipelines/SKILL.md).
5. For a full multimodal experiment, record each modality's processor output,
   time/mask semantics, encoder, alignment, missing-modality policy, and device.

The bundled medcode smoke performs only explicit local/API checks; it does not
fetch mappings, corpora, credentials, or model weights. Read [troubleshooting](references/troubleshooting.md)
and [long-tail](references/long-tail.md) for gated capabilities.
