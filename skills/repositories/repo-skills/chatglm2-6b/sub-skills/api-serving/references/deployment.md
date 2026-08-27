# API Deployment

## When to read

Read this before starting either FastAPI sample or exposing it to a client.

## Local launch checklist

1. Install the model/runtime dependencies and the service extras:
   `fastapi`, `uvicorn`, and `sse-starlette` for the OpenAI-compatible route.
2. Verify a model path or Hub id and run a backend preflight. The sample
   launch code loads the tokenizer/model under `__main__`, moves the model to
   CUDA, calls `.eval()`, and starts Uvicorn on port `8000` with one worker.
3. Start on localhost first. Confirm `/docs` and the endpoint list before
   sending a generation request. Keep a single model process; multiple workers
   multiply model memory.
4. Use the payload validators in `scripts/` before testing a client. For a
   tuned checkpoint, load the checkpoint through the `ptuning` route before
   embedding it in a service.

The simple service is a development-oriented POST `/` adapter. The
OpenAI-compatible service is the better fit for existing Chat Completions
clients, but its CORS policy allows every origin and it has no authentication.
Put it behind an authenticated reverse proxy or add application-level controls
before binding to a non-local interface.

## Request and resource controls

Bound `max_length`, `top_p`, and `temperature` at the application boundary.
Reject malformed role sequences and oversized histories before calling the
model. Use request timeouts and a concurrency policy appropriate for the
available GPU memory. Streaming keeps a request open while `model.stream_chat`
yields text; clients and proxies must allow long-lived SSE connections.

## Port and process hygiene

- A port-in-use error means another process owns `8000`; choose another port in
  the Uvicorn call or stop the intended old process after identifying it.
- Do not run the two sample services on the same port simultaneously.
- Avoid `--workers > 1` unless duplicated model memory and request isolation
  are intentional.
- Do not add public network exposure as a smoke test: route import and payload
  validation are safe checks; full service launch needs model weights and an
  explicit listener decision.
