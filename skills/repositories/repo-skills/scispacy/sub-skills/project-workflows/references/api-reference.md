# API Reference

## Purpose

Use this when you need the registered readers, evaluation helpers, or data parsers that power scispaCy's project workflows.

## Verified signatures

| API | Verified signature | Notes |
| --- | --- | --- |
| `replace_tokenizer_callback` | `replace_tokenizer_callback() -> Callable[[Language], Language]` | spaCy callback registry entry named `replace_tokenizer` |
| `parser_tagger_data` | `parser_tagger_data(path, mixin_data_path, mixin_data_percent, gold_preproc, max_length=0, limit=0, augmenter=None, seed=0)` | spaCy reader registry entry named `parser_tagger_data` |
| `med_mentions_reader` | `med_mentions_reader(directory_path: str, split: str) -> Callable[[Language], Iterator[Example]]` | spaCy reader registry entry named `med_mentions_reader` |
| `specialized_ner_reader` | `specialized_ner_reader(file_path: str)` | spaCy reader registry entry named `specialized_ner_reader` |
| `read_full_med_mentions` | `read_full_med_mentions(directory_path, label_mapping=None, span_only=False, spacy_format=True, use_umls_ids=False)` | Returns `(train, dev, test)` lists |
| `read_ner_from_tsv` | `read_ner_from_tsv(filename: str) -> List[Tuple[str, Dict[str, List[Tuple[int, int, str]]]]]` | BIO TSV parser |
| `med_mentions_example_iterator` | `med_mentions_example_iterator(filename: str) -> Iterator[MedMentionExample]` | Yields parsed MedMentions examples |
| `process_example` | `process_example(lines: List[str]) -> MedMentionExample` | Parses one MedMentions abstract |
| `remove_overlapping_entities` | `remove_overlapping_entities(sorted_spacy_format_entities)` | Removes overlaps greedily |
| `select_subset_of_overlapping_chain` | `select_subset_of_overlapping_chain(chain)` | Chooses the longest non-overlapping spans |
| `evaluate_ner` | `evaluate_ner(nlp: Language, eval_data, dump_path: Optional[str] = None, verbose: bool = False) -> PerClassScorer` | Runs model evaluation and returns metrics |
| `PerClassScorer` | `PerClassScorer()` | Span-level scorer with typed and untyped metrics |

## Registry names to remember

| Registry | Name |
| --- | --- |
| spaCy callback | `replace_tokenizer` |
| spaCy reader | `parser_tagger_data` |
| spaCy reader | `med_mentions_reader` |
| spaCy reader | `specialized_ner_reader` |

## Notes from the source

- `parser_tagger_data` can mix a main corpus with optional mixin data and a sampling percent.
- `med_mentions_reader` and `specialized_ner_reader` both return spaCy `Example` streams.
- `PerClassScorer.get_metric(reset=False)` returns per-label precision/recall/F1 plus overall metrics.
- `evaluate_ner` writes metrics to disk when `dump_path` is supplied.
- `read_full_med_mentions` expects the canonical MedMentions directory layout with corpus and PMID split files.
