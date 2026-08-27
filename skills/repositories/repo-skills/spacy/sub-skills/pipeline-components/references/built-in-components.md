# Built-in components

Validated against spaCy 3.8.15 on the installed CPU environment.

Evidence provenance: `spacy/pipeline/factories.py`, `spacy/tests/pipeline/test_pipe_factories.py`, `spacy/tests/test_factory_registrations.py`, `spacy/language.py`, and `website/docs/usage/processing-pipelines.mdx`.

These are the primary built-in factories covered by this sub-skill. The active metadata below reflects the installed 3.8.15 English registry; language subclasses can override some defaults, so treat `nlp.get_factory_meta(name)` as authoritative for the active `Language` subclass.

| Name | Kind | Assigns / requires | Key defaults to remember | Notes |
| --- | --- | --- | --- | --- |
| `sentencizer` | rule-based | assigns `token.is_sent_start`, `doc.sents` | `overwrite=False`, `punct_chars=None` | Sentence segmentation without the parser. |
| `entity_ruler` | rule-based | assigns `doc.ents`, `token.ent_type`, `token.ent_iob` | `validate=False`, `overwrite_ents=False`, `ent_id_sep="||"` | Pattern-driven entity component; pattern details belong to `documents-and-visualization`. |
| `span_ruler` | rule-based | assigns `doc.spans` | `spans_key="ruler"`, `overwrite=True`, `annotate_ents=False` | Span-group ruler; pattern details belong elsewhere. |
| `attribute_ruler` | rule-based | no default assign/require metadata | `validate=False` | Token-attribute overrides and rule-based exceptions. |
| `lemmatizer` | hybrid / language-specific | assigns `token.lemma` | active blank English resolves to `mode="rule"` | Language defaults vary; use the active factory meta. |
| `trainable_lemmatizer` | trainable | assigns `token.lemma` | `backoff="orth"`, `min_tree_freq=3`, `top_k=1` | Edit-tree lemmatizer. |
| `tok2vec` | trainable | assigns `doc.tensor` | model config only | Shared token-to-vector embeddings for listeners. |
| `tagger` | trainable | assigns `token.tag` | `overwrite=False`, `neg_prefix="!"` | Part-of-speech tagger. |
| `morphologizer` | trainable | assigns `token.morph`, `token.pos` | `overwrite=True`, `extend=False` | Morphology and coarse POS. |
| `parser` | trainable | assigns `token.dep`, `token.head`, `token.is_sent_start`, `doc.sents` | `learn_tokens=False`, `min_action_freq=30` | Dependency parser. |
| `senter` | trainable | assigns `token.is_sent_start` | `overwrite=False` | Sentence recognizer without dependency parsing. |
| `ner` | trainable | assigns `doc.ents`, `token.ent_iob`, `token.ent_type` | `update_with_oracle_cut_size=100` | Named entity recognizer. |
| `textcat` | trainable | assigns `doc.cats` | `threshold=0.0` | Exactly one label per doc. |
| `textcat_multilabel` | trainable | assigns `doc.cats` | `threshold=0.5` | Zero, one, or many labels per doc. |
| `spancat` | trainable | assigns `doc.spans` | `spans_key="sc"`, `threshold=0.5`, `max_positive=None` | Span categorizer. |
| `entity_linker` | trainable | assigns `token.ent_kb_id`; requires `doc.ents`, `doc.sents`, `token.ent_iob`, `token.ent_type` | `use_gold_ents=True`, `candidates_batch_size=1`, `threshold=None` | Add after something that sets entities and sentence boundaries. |
| `doc_cleaner` | utility | no default assign/require metadata | `silent=True`, `attrs={"tensor": None, "_.trf_data": None}` | Removes heavy doc attributes. |
| `token_splitter` | utility | no default assign/require metadata | `min_length=25`, `split_length=10` | Retokenizes. Put it early when token boundaries matter. |

## Order hints

- `tok2vec` often comes before trainable listeners that use shared token vectors.
- `sentencizer`, `senter`, and `parser` all affect sentence boundaries, but they do so in different ways.
- `entity_linker` should only come after sentence boundaries and entities exist.
- `token_splitter` retokenizes the document, so it can change all downstream offsets.

## Secondary factories present in this install

The installed registry also exposes secondary factories and helpers such as `spancat_singlelabel`, `span_finder`, `beam_ner`, `beam_parser`, `future_entity_ruler`, `nn_labeller`, `merge_entities`, `merge_noun_chunks`, and `merge_subtokens`. They are valid factory names in spaCy 3.8.15, but they are not the primary surface for this sub-skill.

## Handoff to other sub-skills

- For ruler/matcher behavior details, use `documents-and-visualization`.
- For config assembly and custom registration, use `component-factories-and-registry.md` and `pipeline-assembly-and-analysis.md`.
- For symptom-to-fix mapping, use `troubleshooting.md`.
