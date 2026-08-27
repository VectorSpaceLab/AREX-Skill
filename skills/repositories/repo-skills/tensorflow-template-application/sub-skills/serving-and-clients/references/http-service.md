# Legacy HTTP Wrapper

## Purpose

This page documents the old Django-based cancer prediction wrapper. It is a
legacy pattern, not the primary serving path for this repo.

## What it does

The wrapper loads a checkpoint-backed TensorFlow graph at import time and then
serves predictions through a Django view.

The important characteristics are:

- It is tied to the cancer example.
- It expects a checkpoint directory and a matching `.meta` file.
- It does not expose a general-purpose REST contract.
- It is brittle if the checkpoint is missing or the graph collections do not
  match the code's expectations.

## Route surface

- `POST /cancer_predict/predict/` is the useful prediction route.
- The index route returns a short message telling the caller to POST to the
  prediction endpoint.

The README mentions an online-training route, but the code surface in this repo
is centered on prediction. Treat any training mention as historical context
unless a future update adds the route back.

## Request shape

The request body is JSON. The view loads the JSON payload and feeds it into the
checkpointed session using the names stored in the graph collections.

The bundled example payload shows fields like:

- `key`
- `features`

The exact field mapping comes from the checkpointed graph collections, so the
wrapper is only safe when that graph is already present and matches the code.

## Why this is reference-only

- The wrapper exits during import if the checkpoint is not present.
- It depends on a relative checkpoint path.
- It assumes a specific graph collection layout.
- It is not a clean replacement for TensorFlow Serving or the Python gRPC
  helpers.

## Common failure modes

- `No model found, exit now` at startup: the checkpoint directory or `.meta`
  file is missing.
- JSON body shape mismatch: the JSON fields do not match the expected graph
  inputs.
- Import-time failure after a refactor: the service initializes before any
  request can be handled.

## When to mention it

Use this page when the user asks about the old HTTP cancer example, a
checkpoint-backed Flask/Django wrapper, or why the wrapper is not a good target
for a fresh serving workflow.
