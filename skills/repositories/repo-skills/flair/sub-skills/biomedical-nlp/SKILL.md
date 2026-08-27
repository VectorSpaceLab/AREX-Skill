---
name: biomedical-nlp
description: "Routes pip-installed Flair HunFlair/HunFlair2 biomedical NER,
  entity mention linking/normalization, dictionaries, abbreviation fallback, and
  biomedical corpus offset workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# biomedical-nlp

Use this sub-skill when a task is specifically about biomedical NLP in Flair:
HunFlair or HunFlair2 named entity recognition (NER), biomedical entity mention
linking / normalization (NEN), biomedical dictionaries, abbreviation behavior,
biomedical corpus offsets, nested entity caveats, or custom biomedical NER and
linking label layers.

## Route here for

- Loading or planning `Classifier.load("hunflair2")`, legacy `Classifier.load("hunflair")`, or entity-specific HunFlair NER models.
- Separating NER mention layers such as `ner` from linking layers such as `link`, `gene-link`, `disease-link`, or `species-link`.
- Loading, building, or applying `EntityMentionLinker.load(...)`, `EntityMentionLinker.build(...)`, and `EntityMentionLinker.predict(...)`.
- Choosing built-in biomedical dictionaries for genes, species, diseases, and chemicals, or creating a small custom dictionary.
- Handling optional SciSpaCy biomedical tokenization / sentence splitting and optional pyab3p abbreviation resolution.
- Loading, converting, or debugging biomedical NER corpora where offsets, tokenization, nested entities, and canonical entity-type mappings matter.

## Route elsewhere for

- Generic `Sentence`, `Token`, `Span`, labels, serialization, sentence splitting, and visualization tasks: use the tagging-and-annotations sub-skill.
- Generic corpus formats, `ColumnCorpus`, `JsonlCorpus`, trainer knobs, checkpoints, TARS, or multi-GPU training: use the training-and-datasets sub-skill.
- Transformer embedding choice, context windows, ONNX/provider acceleration, or embedding cache/device optimization: use the embeddings-and-optimization sub-skill.

## Operating assumptions

- Use the public, pip-installed `flair` package. Do not depend on a local development tree.
- CPU is the verified baseline. Set `FLAIR_DEVICE=cpu` before importing Flair when the user wants deterministic CPU behavior.
- Pretrained HunFlair/HunFlair2 NER models, linker models, and downloaded biomedical dictionaries may fetch public model or data files if they are not already cached. Ask or make the download explicit before using them in constrained environments.
- CUDA, ONNX/provider runtimes, SciSpaCy, pyab3p, and large model downloads are optional and unverified unless the active environment has been separately checked.
- Keep NER and linking annotations in separate label layers. Do not overwrite a user's NER layer with normalization identifiers.
- HunFlair2 NER can tag cell lines, but the built-in `EntityMentionLinker` shortcuts cover gene, disease, chemical, and species linking. Cell-line normalization needs a custom dictionary/linker.

## Quick decisions

1. **Need biomedical tagging only?** Use HunFlair2 NER first; inspect spans on the `ner` layer. See [HunFlair workflows](references/hunflair-workflows.md).
2. **Need normalized ontology identifiers?** Run one or more type-specific `EntityMentionLinker` instances after NER. Store links in `link` or a type-specific output layer. See [entity linking](references/entity-linking.md).
3. **Need an offline/no-download check?** Use an in-memory exact-match linker and a tiny dictionary, or run the bundled [smoke script](scripts/biomedical_smoke.py).
4. **Need biomedical corpora or custom NER?** Use this sub-skill for corpus names, offsets, nested entity cautions, and entity-type mappings; use the training-and-datasets sub-skill for trainer configuration.

## Safety checklist before acting

- Confirm whether model or dictionary downloads are allowed. If not, use cached local models or exact-string-match custom dictionaries.
- If SciSpaCy is requested, treat it as optional: `SciSpacyTokenizer` and `SciSpacySentenceSplitter` require matching SciSpaCy and `en_core_sci_sm` installations. Fall back to standard Flair tokenizers/splitters when not verified.
- If abbreviation resolution is requested, treat pyab3p as optional: prebuilt linkers may switch to `-no-ab3p` variants when pyab3p is missing, while custom `build()` calls should pass `BioSynEntityPreprocessor()` to avoid requiring pyab3p.
- For legacy HunFlair v1 or custom NER layers, inspect `sentence.annotation_layers` and pass `entity_label_types` explicitly to the linker.
- For offset-sensitive corpora, choose tokenization before conversion and expect nested/overlapping entities to be filtered when writing one BIO layer.

## References

- [HunFlair workflows](references/hunflair-workflows.md): NER, tokenization, longer texts, biomedical corpora, offsets, nested entity caveats, and custom biomedical NER planning.
- [Entity linking](references/entity-linking.md): `EntityMentionLinker.load/build/predict`, dictionaries, exact-match no-download linking, label-layer separation, cell-line linker gap, and abbreviation behavior.
- [Troubleshooting](references/troubleshooting.md): optional dependency failures, cache/download issues, label-layer mismatches, dictionary problems, and corpus offset pitfalls.
- [Smoke script](scripts/biomedical_smoke.py): a no-download dry run by default, plus an optional local in-memory linking smoke when Flair is installed.
