---
name: inference
description: "Routes checkpoint inference, candidate ranking, and Flask API
  serving for the couplet model."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# inference

Use this sub-skill when the user wants to load a trained checkpoint, generate
couplet candidates, inspect ranked scores, or expose the model through the
Flask-compatible HTTP API.

## Includes

- Loading `Model` in inference mode from a checkpoint directory.
- Generating ranked candidate lower lines for an input upper line.
- Applying the legacy length, repetition, and censor-word ranking heuristics.
- Serving the `/chat/couplet/<in_str>` and `/v0.2/couplet/<in_str>` routes.
- Running a test-client smoke that does not start a long-running listener.

## Excludes

- Training a model or continuing a checkpoint.
- BLEU evaluation and dataset batching.
- General web-app deployment not tied to this model.

If the user needs to create or continue the checkpoint first, route to
`../training/SKILL.md`.

## Read these files

- `../../references/dependencies.md` if TensorFlow, Flask, or gevent is missing.
- `../../references/model-overview.md` for how `Model.infer` relates to the
  training graph.
- `../../references/troubleshooting.md` for shared import, backend, and
  checkpoint failures.
- `references/workflows.md` for offline generation and service startup.
- `references/http-api.md` for route behavior and response shapes.
- `references/troubleshooting.md` for inference-specific failures.
- `scripts/infer_couplet.py` for one-off predictions from a checkpoint.
- `scripts/serve_couplet.py` for the parameterized Flask service wrapper.
- `scripts/serve_smoke.py` for a safe route smoke using a tiny checkpoint.

## Typical questions this route answers

- How do I generate a couplet from a trained checkpoint?
- What does the `/v0.2/couplet/<in_str>` route return?
- How can I run the server without editing hard-coded paths?
- Why does the service return the same fixed error message?
- How do I verify the serving path without leaving a listener running?

## Working pattern

1. Verify the environment with the root `scripts/check_env.py`.
2. Confirm that the checkpoint directory and vocab file match.
3. Use `scripts/infer_couplet.py` for one-off generation.
4. Use `scripts/serve_smoke.py` before starting a persistent service.
5. Start `scripts/serve_couplet.py` only when the model and paths are ready.

## High-value reminders

- The raw input string is split into characters before `Model.infer` is called.
- Empty input or input longer than the service limit returns `您的输入太长了`.
- The service wrapper sorts candidates after applying the legacy scoring
  heuristics.
- The legacy source server has import-time side effects; use the bundled
  wrappers for testing and serving.
