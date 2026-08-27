# API Reference

## Purpose

Use this when you need exact constructor signatures, defaults, or output-file names for scispaCy's candidate-generation and entity-linking stack.

## Verified signatures

| API | Verified signature | Notes |
| --- | --- | --- |
| `LinkerPaths.from_directory` | `LinkerPaths.from_directory(directory: Union[str, pathlib.Path]) -> Self` | Resolves the four on-disk linker artifacts |
| `CandidateGenerator` | `CandidateGenerator(ann_index=None, tfidf_vectorizer=None, ann_concept_aliases_list=None, kb=None, verbose=False, ef_search=200, name=None)` | Default name is `umls` |
| `create_tfidf_ann_index` | `create_tfidf_ann_index(out_path: Optional[str], kb=None, *, ef_search: int = 200) -> Tuple[List[str], TfidfVectorizer, FloatIndex]` | Builds or reloads the ANN index |
| `EntityLinker` | `EntityLinker(nlp=None, name='scispacy_linker', candidate_generator=None, resolve_abbreviations=True, k=30, threshold=0.7, no_definition_threshold=0.95, filter_for_definitions=True, max_entities_per_mention=5, linker_name=None)` | Factory name: `scispacy_linker` |
| `EntityLinker.from_kb` | `EntityLinker.from_kb(kb, *, ann_index_out_dir=None, candidate_generator_kwargs=None, **entity_linker_kwargs)` | Builds a linker directly from a KB |
| `KnowledgeBase` | `KnowledgeBase(file_path=None)` | Accepts JSON, JSONL, or an iterable of `Entity` objects |
| `UmlsKnowledgeBase` | `UmlsKnowledgeBase(file_path=DEFAULT_UMLS_PATH, types_file_path=DEFAULT_UMLS_TYPES_PATH)` | Default UMLS KB plus semantic type tree |
| `Mesh` / `GeneOntology` / `HumanPhenotypeOntology` / `RxNorm` | one-argument path loaders | Built-in KB subclasses |
| `Entity` | `Entity(concept_id, canonical_name, aliases, types=[], definition=None)` | Named tuple for KB records |
| `construct_umls_tree_from_tsv` | `construct_umls_tree_from_tsv(filepath: str) -> UmlsSemanticTypeTree` | Builds the UMLS type tree |
| `read_umls_concepts` | `read_umls_concepts(meta_path, concept_details, source=None, lang='ENG', non_suppressed=True)` | Reads `MRCONSO.RRF` |
| `read_umls_types` | `read_umls_types(meta_path, concept_details)` | Reads `MRSTY.RRF` |
| `read_umls_definitions` | `read_umls_definitions(meta_path, concept_details)` | Reads `MRDEF.RRF` |

## Important runtime shapes

| Object | Shape |
| --- | --- |
| `Span._.kb_ents` | `List[Tuple[str, float]]` of `(concept_id, score)` pairs |
| `KnowledgeBase.cui_to_entity` | `Dict[str, Entity]` |
| `KnowledgeBase.alias_to_cuis` | `Dict[str, Set[str]]` |
| `CandidateGenerator(...)` result | `List[List[MentionCandidate]]` |
| `MentionCandidate` | `NamedTuple(concept_id, aliases, similarities)` |

## Linker output artifacts

When `create_tfidf_ann_index(out_path, kb)` is given an output directory, it writes:

- `nmslib_index.bin`
- `tfidf_vectorizer.joblib`
- `tfidf_vectors_sparse.npz`
- `concept_aliases.json`

`LinkerPaths.from_directory(...)` resolves those files back into a `LinkerPaths` object.

## Defaults worth remembering

- `EntityLinker.resolve_abbreviations=True` by default.
- `EntityLinker.k=30` by default.
- `EntityLinker.threshold=0.7` by default.
- `EntityLinker.no_definition_threshold=0.95` by default.
- `EntityLinker.filter_for_definitions=True` by default.
- `EntityLinker.max_entities_per_mention=5` by default.
- `CandidateGenerator` defaults to the `umls` KB family when `name` is not overridden.

## Notes from the source and tests

- `create_tfidf_ann_index` uses a char-3gram `TfidfVectorizer` with `min_df=10`; tiny custom KBs may need more repeated aliases to produce a useful vocabulary.
- The linker tests use a small local UMLS fixture and verify that abbreviation-aware linking works only after the abbreviation detector is already present.
- `scispacy.umls_linking.UmlsEntityLinker` is a backward-compatibility alias for `EntityLinker`.
