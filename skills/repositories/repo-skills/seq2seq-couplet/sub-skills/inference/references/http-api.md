# HTTP API Reference

## Purpose

Read this when you need route names, response shapes, or the output-ranking
rules used by the inference service.

## Routes

| Route | Method | Response | Notes |
| --- | --- | --- | --- |
| `/chat/couplet/<in_str>` | GET | `{"output": "<top-output>"}` | Returns only the best-ranked candidate. |
| `/v0.2/couplet/<in_str>` | GET | `{"output": ["..."], "score": [0.0]}` | Returns all ranked candidates and their adjusted scores. |

The bundled service wrapper exposes the same route shapes without importing the
legacy long-running server module.

## Input handling

- The incoming `<in_str>` is treated as a raw string.
- Before `Model.infer`, the string is split into individual characters joined
  by spaces.
- Empty input or input longer than the configured maximum length returns the
  fixed message `您的输入太长了`.
- The default maximum length is 50 characters.

## Candidate ranking

The model returns beam-search candidates and raw scores. The service then
adjusts those scores with the legacy heuristics:

- penalize inputs made of the same repeated character,
- penalize candidate/input length mismatch,
- penalize outputs or inputs containing configured censor words,
- penalize repeated-character patterns that do not mirror the input,
- penalize candidates that reuse input characters too directly,
- sort candidates by the adjusted score in descending order.

## Censor words

The original service expected a censor-word file. The bundled wrapper makes
that file optional. If no censor-word file is supplied, the censor penalty is
skipped while the other ranking rules remain active.

## Validation flow

1. Run `scripts/check_env.py` from the root skill to confirm the runtime and
   bundled route definitions.
2. Run `scripts/serve_smoke.py` to exercise both routes through a Flask test
   client.
3. Only start `scripts/serve_couplet.py` as a persistent listener after the
   checkpoint and vocab paths are known to work.
