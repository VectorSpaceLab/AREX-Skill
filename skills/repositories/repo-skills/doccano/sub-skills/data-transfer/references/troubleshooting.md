# Data-transfer troubleshooting

## Parser and file-shape failures

- **JSON or JSONL parse error**: validate the payload before upload. JSONL must contain one object per line.
- **CSV parse error**: confirm the delimiter, headers, and column names. Empty cells and out-of-order columns can change how the parser behaves.
- **CoNLL parse error**: each non-empty line must contain exactly two tab-separated columns.
- **Text file import looks wrong**: make sure you selected the correct format between plain text, line-based text, and structured text formats.
- **Relation extraction import looks wrong**: confirm the project has relation support enabled and the JSONL rows contain the expected relation fields.

## Encoding and file-type failures

- **Unexpected MIME rejection**: disable `ENABLE_FILE_TYPE_CHECK` for a trusted upload path or upload the exact file type the project expects.
- **File too large**: increase `MAX_UPLOAD_SIZE` or split the file into smaller chunks.
- **Encoding looks corrupted**: retry with UTF-8 or an explicitly selected encoding if auto-detection guessed wrong.
- **Excel import fails**: confirm the workbook format is supported and that the expected sheet contents are simple enough for the parser.

## Task-specific shape failures

- **Sequence labeling mismatch**: confirm whether the project expects spans only or spans plus relations.
- **Seq2seq mismatch**: check the data and label column names in the source file.
- **Intent detection mismatch**: confirm the file contains both the category list and any slot spans the project needs.
- **Image/audio import mismatch**: use the file-backed formats and confirm the uploaded asset path or binary file is valid.

## Export surprises

- **Collaborative export contains more labels than expected**: collaborative projects export all visible labels for the chosen confirmation mode.
- **Per-user export is missing labels**: non-collaborative projects export one file per member and use only that member's annotations.
- **Relation export looks flat**: check whether the project enabled relations before assuming the exported JSONL will include relation dictionaries.

## Recovery steps

1. Recheck the project type.
2. Recheck the file format and format options.
3. Validate the file outside doccano with a tiny fixture.
4. Re-run the import or export with the corrected settings.
