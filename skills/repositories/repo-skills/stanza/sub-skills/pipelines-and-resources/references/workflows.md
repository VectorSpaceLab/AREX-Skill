# Workflows

Use these workflows when you need a concrete, low-risk way to inspect or run Stanza pipelines.

## 1. Inspect first, run later

Start with cache and API inspection:

```bash
python scripts/pipeline_smoke.py --help
python scripts/pipeline_smoke.py --no-pipeline
python -m stanza.resources.list_installed --help
```

Then review:
- installed model rows
- resource dir path
- torch/CUDA status
- whether a smoke pipeline can run without downloads

## 2. Offline single-language smoke

When you already know the cache contains the needed models:

```bash
python scripts/pipeline_smoke.py --lang en --processors tokenize --text "Barack Obama was born in Hawaii."
```

What this checks:
- `stanza` import and version
- local resource dir
- `torch` and CUDA availability
- no-download `Pipeline` construction
- a tiny text pass if the model is already present

If you only want CPU behavior, keep the script on its default CPU device or pass `--device cpu`.

## 3. Explicit download workflow

When the user says downloads are allowed, stage them explicitly:

```bash
python scripts/pipeline_smoke.py --allow-download --lang en --processors tokenize,pos --package default
```

If your network needs a proxy, pass one before allowing downloads.

## 4. Multilingual workflow

For mixed-language text, configure language-specific pipelines and let the language ID step route each document:

```python
from collections import defaultdict
import stanza

lang_configs = {
    "en": {"processors": "tokenize,pos,lemma,depparse"},
    "fr": {"processors": "tokenize,pos,lemma,depparse"},
}
pipe = stanza.MultilingualPipeline(lang_configs=lang_configs)
```

Good habits:
- use `restrict=True` if the language set is closed
- keep `default_processors` small so missing processors are obvious
- remember that the internal language-id pipeline is built on `multilingual`

## 5. Batch and stream

For a fixed list of strings or `Document` objects, use the batch helpers:

```python
pipe = stanza.Pipeline("en", processors="tokenize,pos", download_method=stanza.DownloadMethod.NONE)
processed = pipe.process_many(["This is a test.", "Another one."])
```

For an iterator or large stream:

```python
for doc in pipe.stream(text_iter, batch_size=50):
    ...
```

Rules of thumb:
- `process_many` always returns a list and preserves order
- `stream` is best for iterators and large batches
- `bulk_process` is useful when you already have a batch container

## 6. Device selection

- Use CPU by default for smoke runs.
- Use `device='cuda'` or `device='cuda:0'` only when the environment has a visible GPU.
- If you are unsure, inspect `torch.cuda.is_available()` first.

## 7. Custom or unknown language setups

If you are working with a custom language or a locally staged model:

- set `allow_unknown_language=True`
- provide explicit `*_model_path` kwargs
- keep `download_method=DownloadMethod.NONE` until the local files are verified

## 8. When the pipeline complains about prerequisites

If a processor raises `PipelineRequirementsException`, fix the order or the inputs rather than forcing downloads.

Examples:
- depparse without its required upstream tags
- lemmatization without the expected POS information
- a pretagged configuration that does not match the provided data

## Verification basis

These workflows were distilled from Stanza 1.14.0 source, tests, demos, and installed-package inspection. Check the root provenance file before treating them as current for a different checkout or package version.
