# Inference Workflows

## Purpose

Read this when you need to generate couplets from a checkpoint, run the HTTP
service wrapper, or smoke-test route behavior without editing the legacy source
server.

## Requirements

- A checkpoint directory produced with the same vocabulary and model shape.
- A vocabulary file whose first entries are `<s>` and `</s>`.
- The verified TensorFlow/Flask runtime dependency set.

## Offline prediction

Use `scripts/infer_couplet.py` for one-off generation. It loads the checkpoint,
applies the same input-length and ranking logic as the service wrapper, and
prints JSON.

Example:

```bash
python sub-skills/inference/scripts/infer_couplet.py \
  --vocab-file <vocabs.txt> \
  --model-dir <checkpoint-dir> \
  "天朗气清"
```

The script converts the raw input string into space-separated characters before
calling `Model.infer`.

## HTTP service

Use `scripts/serve_couplet.py` to start the Flask-compatible service with
explicit paths.

Example:

```bash
python sub-skills/inference/scripts/serve_couplet.py \
  --vocab-file <vocabs.txt> \
  --model-dir <checkpoint-dir> \
  --host 0.0.0.0 \
  --port 5000
```

Run with `--dry-run` first to validate paths and route setup without starting a
listener.

## Safe route smoke

Use `scripts/serve_smoke.py` when you need a fast end-to-end route check. The
smoke can create a tiny checkpoint internally, build the Flask app, and use a
Flask test client to request both routes without opening a network socket.

The smoke validates service mechanics only. It does not prove model quality.

## Operational notes

- The service route `/chat/couplet/<in_str>` returns only the top output.
- The route `/v0.2/couplet/<in_str>` returns the ranked list and scores.
- The bundled service wrapper accepts an optional censor-word file; if omitted,
  the censor penalty is skipped.
- Do not import the legacy service module directly during tests because it
  starts the WSGI server at module import time.
