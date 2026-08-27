# Service and Integration Patterns

## When to read

Read this when integrating LTP output into APIs, data pipelines, or downstream formats. For direct model calls, use `workflows.md` first.

## Service wrapper pattern

A safe service wrapper separates model startup, request validation, inference, and output normalization:

```python
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
from ltp import LTP

class Request(BaseModel):
    sentences: List[str]
    tasks: List[str] = ["cws", "pos", "ner"]

app = FastAPI()
ltp = LTP("LTP/small")

@app.post("/api")
def predict(req: Request):
    output = ltp.pipeline(req.sentences, tasks=req.tasks)
    return {task: getattr(output, task) for task in req.tasks}
```

Add `fastapi`/`uvicorn` separately. Do not bundle server startup into library import code; load the model at process startup or via a controlled lazy singleton.

## Dependency and security notes

- Validate task names before passing them to `pipeline`.
- Do not expose arbitrary model ids or local paths to untrusted callers.
- Keep Hugging Face tokens in environment/secret stores, not request payloads.
- Set request size and timeout limits for long documents.
- If CUDA is enabled, warm up the model and handle out-of-memory recovery by returning an explicit error or falling back to CPU only if the application accepts it.

## CoNLL-U-like export

The repository example pattern turns `cws`, `pos`, `dep`, and `sdpg` into rows. Use the bundled converter for a source-independent workflow:

```bash
python scripts/convert_ltp_output_to_conllu.py --input ltp_output.json --output ltp_output.conllu
```

The converter expects already-saved JSON output and avoids model loading. This makes it useful in tests or pipelines where inference happens elsewhere.

## Offset handling

LTP entity and SRL spans are word-index based after segmentation. If a downstream API needs character offsets:

1. Keep the original sentence text.
2. Reconstruct word offsets from `cws` by scanning left to right.
3. Map entity or argument word spans onto the word-offset table.
4. Preserve punctuation tokens because dependency and semantic graph indices include them.

## Batch and document pipelines

- Use `StnSplit` before feeding documents into `pipeline`.
- Store a mapping from sentence index to document id and sentence offset.
- Run `pipeline` over batches of sentences, then join results back by the mapping.
- For long-running services, explicitly log model id/path, task list, CPU/GPU state, and package versions at startup.

## Testing integration code

Prefer fixture tests that do not load a model:

- Test JSON-to-CoNLL-U conversion using saved or synthetic LTP-shaped output.
- Test service request validation with mocked output objects.
- Keep one optional end-to-end model test behind an explicit marker or environment variable such as `RUN_LTP_MODEL_TEST=1`.
