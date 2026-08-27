# Import and export formats

doccano selects import and export formats by project type. The exact supported set depends on the annotation shape.

## Import formats by project type

| Project type | Supported import formats | Notes |
| --- | --- | --- |
| `DocumentClassification` | TextFile, TextLine, CSV, fastText, JSON, JSONL, Excel | CSV and Excel accept configurable delimiter and column options. fastText expects labels with the `__label__` prefix. |
| `SequenceLabeling` | TextFile, TextLine, JSONL, CoNLL, JSONL(Relation) | JSONL can also include relation extraction data when the relation workflow is enabled. |
| `Seq2seq` | TextFile, TextLine, CSV, JSON, JSONL, Excel | Text-to-text rows use the configured data and label columns. |
| `IntentDetectionAndSlotFilling` | TextFile, TextLine, JSONL | Supports categories and spans in the same example payload. |
| `ImageClassification` | ImageFile | The file-based import uses image assets rather than plain text. |
| `BoundingBox` | ImageFile | Bounding box examples are file-backed and use region data. |
| `Segmentation` | ImageFile | Segmentation examples are file-backed and use polygon/point region data. |
| `ImageCaptioning` | ImageFile | Captioning is file-backed with text labels. |
| `Speech2text` | AudioFile | Audio imports use file-backed examples and transcript labels. |

## Export formats by project type

| Project type | Supported export formats | Notes |
| --- | --- | --- |
| `DocumentClassification` | CSV, fastText, JSON, JSONL | Export format controls how category labels and comments are serialized. |
| `SequenceLabeling` | JSONL | Use the relation-aware shape when the project enables relations. |
| `Seq2seq` | CSV, JSON, JSONL | Text labels are renamed to the project's export column. |
| `IntentDetectionAndSlotFilling` | JSONL | Exports both category and span collections. |
| `ImageClassification` | JSONL | Exports filename-backed examples and categories. |
| `BoundingBox` | JSONL | Exports bounding-box dictionaries and comments. |
| `Segmentation` | JSONL | Exports segmentation region dictionaries and comments. |
| `ImageCaptioning` | JSONL | Exports filename-backed examples and text labels. |
| `Speech2text` | JSONL | Exports filename-backed examples and text labels. |

## Validation and configuration knobs

- `ENABLE_FILE_TYPE_CHECK` enables MIME-based validation during upload.
- `MAX_UPLOAD_SIZE` limits upload size.
- `IMPORT_BATCH_SIZE` controls the import batch size.
- CSV and Excel import paths need the right delimiter and column names.
- CoNLL import requires tab-separated token/tag pairs and a valid tag scheme.
- JSON and JSONL must parse cleanly before the import task can create examples and labels.

## Read alongside

- `../../references/cli-reference.md` when the task is part of a startup or service check.
- `../../references/troubleshooting.md` for common parser and validation failures.
