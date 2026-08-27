# Demos and Serving Troubleshooting

## Purpose

Use this when a Gradio or FastAPI demo fails to start, binds the wrong port, or returns the wrong payload.

## Missing optional dependencies

**Symptoms**

- `ModuleNotFoundError` for `gradio`, `fastapi`, `uvicorn`, `python-multipart`, or `requests`.
- Import succeeds for the core package, but the server/client helper fails.

**Recovery**

1. Install the dependency set for the route you need.
2. Re-run the bundled environment check.
3. Use the lazy-loading skeleton instead of the original import-time demo when you need a safer starting point.

## Import-time model downloads

**Symptoms**

- The original demo script hangs during import.
- Starting the UI or server tries to download a model immediately.

**Likely cause**: the repo demo code loads the model at module import time.

**Recovery**

1. Switch to the generated lazy-loading skeleton.
2. Keep the model id configurable.
3. Only download weights after the service is ready to run.

## `share=True` or accidental public exposure

**Symptoms**

- The demo creates a public share link.
- The user did not intend to expose the server outside the local machine.

**Recovery**

1. Keep sharing disabled by default.
2. Prefer a local host and explicit port.
3. Turn on sharing only when the user asks for it.

## Port binding failures

**Symptoms**

- `OSError: [Errno 98] Address already in use`
- The server exits immediately.

**Recovery**

1. Pick another port.
2. Check for a stale process.
3. Restart the server with the explicit host/port you planned.

## Wrong request fields or 422 responses

**Symptoms**

- The client gets `422 Unprocessable Entity`.
- The image or prompt payload does not reach the server.

**Likely cause**: the client form field names do not match the server endpoint.

**Recovery**

1. Re-check the endpoint contract in the reference.
2. Confirm the file/question/seed/top_p/temperature or prompt/guidance field names.
3. Re-run the bundled client after fixing the field names.

## Streaming response parsing issues

**Symptoms**

- The client saves garbled bytes or only part of the image stream.
- Multiple images are hard to split from the response body.

**Likely cause**: the response is streamed, but the client treats it like a single finished image.

**Recovery**

1. Prefer a simple client that prints or saves the raw response for debugging.
2. Add explicit parsing only after you confirm the server's streaming format.
3. Keep the client configurable so you can change the output handling without editing the server.

## CUDA and model-size problems

**Symptoms**

- The demo loads but runs out of memory.
- The model runs too slowly on CPU.

**Recovery**

1. Use a smaller model id when available.
2. Lower concurrency and batch size.
3. Switch to the core workflow sub-skill to reduce the model-side memory footprint before serving again.
