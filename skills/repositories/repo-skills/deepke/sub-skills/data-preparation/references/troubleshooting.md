# DeepKE data-preparation troubleshooting

Use this reference when a conversion or auto-labeling step succeeds but DeepKE training still fails, or when a bundled helper exits nonzero.

## Empty train/dev/test splits

Symptoms:

- A generated split file exists but has zero rows or zero sentence blocks.
- Training fails immediately with an index, sampler, or empty dataset error.

Likely causes and fixes:

- The corpus is too small for `0.8/0.1/0.1`. Use more examples or choose rates that allocate at least one example to every split you need.
- All input text lines were blank after stripping whitespace. Inspect the source text before splitting.
- A source directory contained no `.txt` files. Pass the correct `--source-dir` or use `--source-file`.
- For smoke checks, it is acceptable to create tiny artificial splits; for model training, use representative data.

## Bad NER offsets

Symptoms:

- Converter reports an offset mismatch.
- BIO output labels the wrong characters.
- Doccano export spans look shifted after preprocessing.

Likely causes and fixes:

- Offsets were computed before stripping prefixes, relation suffixes, HTML, or normalization. Recompute offsets on the exact `sentence` or `text` field used for training.
- Offsets are byte positions instead of Python character positions. Re-export or convert them to character offsets.
- `end_offset` is inclusive in a custom source, but DeepKE/doccano-style conversion expects exclusive. Add one to inclusive end positions.
- The same entity surface appears multiple times and the source only gives `word` without offsets. Prefer offset-based JSON for repeated mentions.

## Overlapping or nested entities

Symptoms:

- Converter exits with an overlap error.
- Long entities are partly overwritten by shorter entities.

DeepKE's basic BIO text representation has one label per token/character. It cannot faithfully encode overlapping spans such as `University of California` and `California` as separate entities in the same positions. Pick one label per position, split the sentence, or use a model/data path that explicitly supports nested entities.

## Unknown or inconsistent labels

Symptoms:

- Training errors mention a missing label or an unexpected tag.
- Evaluation produces zero scores for a label that appears in raw annotations.

Likely causes and fixes:

- Label spelling differs between data and config, such as `PER` vs `Person` or `Cause-Effect` vs `Cause_Effect`.
- Weak-supervision dictionaries introduce labels not present in the supervised config.
- RE distant-supervision triples use relation names that were not added to the downstream relation vocabulary.
- The none label is `None` in prepared data but the target workflow expects `NA`, `no_relation`, or another sentinel.

## Tokenization and dictionary problems

Symptoms:

- Weak NER output misses obvious entities.
- A shorter dictionary entry hides a longer one.
- English multi-word entities are split incorrectly.

Checks:

- Add aliases and casing variants to the dictionary, or run the helper with appropriate case sensitivity.
- Put complete multi-word expressions in the dictionary; the bundled helper performs longest-match span labeling.
- Inspect punctuation around entities. `Washington,` and `Washington` may tokenize differently in downstream loaders.
- Remember that weak supervision is noisy. Review a sample of output before using it as gold data.

## Malformed JSON or JSONL

Symptoms:

- `json2txt`, `json2csv`, or `ds_label_data.py` exits with a JSON parse error.
- Only the first line is read, or line numbers appear in the error.

Fixes:

- Use `--json-lines` for one JSON object per line.
- Use a JSON array (`[...]`) when not using JSONL.
- Remove comments and trailing commas; standard JSON does not allow them.
- Ensure nested values intended for CSV are valid JSON-serializable values.

## Malformed CSV

Symptoms:

- Dictionary rows are skipped.
- Triple rows have shifted columns.
- CSV conversion produces columns with unexpected names.

Fixes:

- Quote fields that contain commas, newlines, or quotes.
- Use headers `entity,label` for NER dictionaries and `head,tail,rel` for RE triples when possible.
- Check encoding; use UTF-8 unless your environment requires another encoding.
- Inspect the first row because JSON/XLSX conversion treats keys or the first spreadsheet row as column names.

## XLSX conversion problems

Symptoms:

- The converter reports missing workbook XML or an empty header row.
- CSV output has blank columns.

Fixes:

- Save the spreadsheet as a normal `.xlsx`, not legacy `.xls`.
- Put headers in the first row of the first sheet.
- Avoid merged header cells for data files.
- If formulas are present, save cached values or export to CSV from the spreadsheet application first.

## DOCX conversion problems

Symptoms:

- `docx2txt` cannot find any sentence paragraphs.
- Labels are assigned to the wrong sentence.

Fixes:

- Use `Sentence:<text>` for each sentence paragraph.
- Put entity paragraphs after the sentence they annotate, using `LABEL:entity1,entity2`.
- Avoid tables, text boxes, comments, and tracked-change-only text for data content; the bundled parser reads normal document paragraphs.
- Prefer JSON with offsets when sentence text or entity strings contain many repeated phrases.

## RE distant-supervision mismatch

Symptoms:

- Most labeled records receive `None`.
- A relation appears reversed.

Likely causes and fixes:

- The triple table is directed and source candidate pairs are reversed. Either generate candidate pairs in the correct direction or rerun with bidirectional matching only if the relation semantics allow it.
- English casing differs between source and triples. Use default English case-insensitive matching or normalize both files.
- Entity aliases differ, such as `U.S.` vs `United States`. Add aliases to the triple table or normalize source pairs before labeling.
- Head/tail offsets point to a different mention than the `head`/`tail` strings. Validate with strict offsets on a sample.
