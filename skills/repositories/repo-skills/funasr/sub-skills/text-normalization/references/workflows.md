# Text-normalization workflows

This reference separates the self-contained punctuation helper from the optional FunTextProcessing ITN/TN stack. Use it to choose the smallest safe tool for a user's text-processing request.

## Decision table

| User need | Use | Why |
|---|---|---|
| Fix spaces around punctuation or quotes after a normalizer/detokenizer changed them | Bundled punctuation helper | Pure Python, no model download, no Pynini, no grammar cache |
| Preserve Unicode punctuation spacing from the original text | Bundled punctuation helper with `--unicode-punct` | Handles punctuation classes beyond ASCII |
| Convert spoken ASR output into written forms, numbers, dates, units, or abbreviations | Optional ITN stack | Requires finite-state grammars and language-specific rules |
| Convert written forms into spoken text for TTS-style preprocessing | Optional TN stack | Requires finite-state grammars and language-specific rules |
| Run ASR, choose a speech model, write subtitles, serve an API, train, export, or use vLLM | A sibling FunASR sub-skill | Those workflows have different dependencies and failure modes |

## Lightweight punctuation helper

Use [`../scripts/post_process_punct.py`](../scripts/post_process_punct.py) when the candidate text already contains the correct characters but punctuation has drifted relative to the original input. The shell commands below assume the current directory is this `text-normalization` sub-skill directory.

Single text pair:

```bash
python scripts/post_process_punct.py align \
  --input "test' example" \
  --normalized "test 'example"
```

Unicode punctuation:

```bash
python scripts/post_process_punct.py align \
  --input "你好，世界！" \
  --normalized "你好 ， 世界 ！" \
  --unicode-punct
```

Line-aligned files:

```bash
python scripts/post_process_punct.py align \
  --input-file original.txt \
  --normalized-file normalized.txt \
  --output-file cleaned.txt
```

Simple cleanup of already-final text is also available:

```bash
python scripts/post_process_punct.py simple --text ' “ hello ”  , world ! '
```

What the helper can and cannot do:

- It can move spaces before or after punctuation marks to match the original input.
- It can collapse repeated spaces after processing.
- It can normalize common curly quote characters in `simple` mode.
- It cannot infer a missing number/date/unit conversion. Use full ITN/TN for semantic text normalization.
- It cannot reliably repair punctuation counts that do not match between original and candidate text; inspect those cases manually.

## Optional full ITN path

Use inverse text normalization when the user starts from spoken-form ASR text and wants written-form text. Examples include numbers, dates, units, money, telephone numbers, and language-specific written conventions.

Typical optional API shape:

```python
from fun_text_processing.inverse_text_normalization.inverse_normalize import InverseNormalizer

normalizer = InverseNormalizer(lang="en", cache_dir="./itn-cache")
written = normalizer.inverse_normalize("twelve kilograms", verbose=False)
print(written)
```

Language choices exposed by the ITN command-line parser include:

- `en`, `id`, `ja`, `de`, `es`, `pt`, `ru`, `fr`, `vi`, `ko`, `zh`, `tl`

ITN stack expectations:

- `pynini` must import successfully.
- Language-specific grammar modules must be present in the installed package.
- The cache directory must be writable if a cache is used.
- For Japanese, optional number flags control standalone numbers and zero-to-nine conversion.

## Optional full TN path

Use text normalization when the user starts from written text and wants spoken-form text, often before TTS or a normalization benchmark.

Typical optional API shape:

```python
from fun_text_processing.text_normalization.normalize import Normalizer

normalizer = Normalizer(input_case="cased", lang="en", cache_dir="./tn-cache")
spoken = normalizer.normalize("12 kg", punct_pre_process=True, punct_post_process=True)
print(spoken)
```

Language choices exposed by the TN command-line parser include:

- `en`, `de`, `es`, `zh`

TN stack expectations:

- `pynini`, `regex`, `joblib`, and `tqdm` are imported by the full path.
- Optional Moses detokenization support is used for `punct_post_process`; without the NLP helper, punctuation post-processing in the full TN path is skipped.
- `input_case` must be either `cased` or `lower_cased`.
- Use `punct_pre_process` for bracket spacing before normalization and `punct_post_process` only when optional detokenization support is ready.

## Cache and overwrite rules

- Use a user-writable cache directory outside read-only package locations.
- Use separate cache directories for distinct languages or experiments when reproducibility matters.
- Use overwrite only when stale or incompatible grammar files are suspected.
- Set the cache directory to `None` only when the runtime should avoid persistent grammar caches.

## Dependency probe

Before promising full ITN/TN, run:

```bash
python scripts/post_process_punct.py check-full-stack
```

Use `--strict` when the caller wants a non-zero exit status if required full-stack packages are missing.
