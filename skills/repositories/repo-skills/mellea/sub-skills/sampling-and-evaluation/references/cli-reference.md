# `m eval` reference

This route owns the evaluation meaning of the command. General CLI discovery,
installation, backend setup, and service lifecycle belong to
`serving-and-cli`.

## Command

```text
m eval run TEST_FILES... [OPTIONS]
```

`TEST_FILES` is one or more JSON/JSONL paths. The runner loads each path with
`TestBasedEval.from_json_file()`. The source implementation documents JSON
objects and arrays; use JSON for the portable, assertion-backed format even
when a surrounding benchmark tool uses JSONL naming.

## Options and defaults

| Option | Default | Meaning |
|---|---:|---|
| `--backend`, `-b` | `ollama` | Candidate-generation backend |
| `--model` | backend default | Candidate model identifier or known model-id name |
| `--max-gen-tokens` | `256` | Candidate output token cap |
| `--judge-backend`, `-jb` | same as `--backend` | Judge backend |
| `--judge-model` | backend default | Judge model identifier |
| `--max-judge-tokens` | `256` | Judge output token cap |
| `--output-path`, `-o` | `eval_results` | Output path prefix |
| `--output-format` | `json` | `json` or `jsonl` |
| `--continue-on-error` | `True` | Skip failed test cases instead of aborting |

The CLI does not expose a `threshold`, seed, or strategy option. If a benchmark
needs those, pass model options in a Python runner or post-process the saved
results; do not imply that an unexposed option changed native CLI behavior.

Use `m eval run --help` before invoking a versioned environment. Help is a
safe parser check and does not create a backend session.

## Input contract

Each test object requires:

- `source`: origin label;
- `name`: human-readable test name;
- `instructions`: judge guidelines;
- `id`: test identifier;
- `examples`: non-empty list.

Each example has `input` message objects, optional `targets` message objects,
and optional `input_id`. A message has `role` and `content`. During loading,
the last user message becomes the candidate input. Assistant target messages
become reference strings; examples without a user message are skipped.

The bundled `validate_eval_config.py` validates a small preflight config, not
the dataset contents. Dataset validation remains the responsibility of
`TestBasedEval.from_json_file()` and should be run before an expensive model
run.

## Result schema

For `--output-format json`, the runner writes an object like:

```json
{
  "summary": {
    "total_tests": 1,
    "total_inputs": 2,
    "passed_inputs": 1,
    "failed_inputs": 1,
    "overall_pass_rate": 0.5
  },
  "results": [
    {
      "test_id": "email-001",
      "source": "email",
      "name": "professional-email",
      "instructions": "...",
      "input_results": [
        {
          "input": "Write a short email.",
          "model_output": "...",
          "passed": true,
          "score": 1,
          "justification": "..."
        }
      ],
      "expected_targets": [["reference"]],
      "passed": 1,
      "total_count": 2,
      "pass_rate": 0.5
    }
  ]
}
```

`jsonl` writes one per-test result per line, without the JSON summary wrapper.
The output path receives the selected extension when it does not already end
with it. Treat judge text and model output as potentially sensitive benchmark
data.

## Judge parsing

The runner first scans for the first decodable JSON object containing a
`score` key. Its `justification` is used only when it is a string; otherwise
raw judge output is retained. If no such object is found, it searches for a
text pattern equivalent to `score: 1`. A missing score returns `(None, raw)` and
is marked failed. The native pass rule is exactly `score == 1`; other numeric
scores may be serialized but do not pass.

A parser-level assertion can be run without any backend:

```python
from cli.eval.runner import parse_judge_output

score, reason = parse_judge_output('{"score": 1, "justification": "ok"}')
assert score == 1
assert reason == "ok"

score, reason = parse_judge_output("no score")
assert score is None
assert reason == "no score"
```

## Cost and failure policy

One input consumes one candidate call and one judge call in the native runner,
plus any backend/provider retry outside the runner. `continue_on_error=True`
keeps later tests running but can reduce the denominator represented in
`results`; record load/execute errors separately. Keep generator and judge
model identities, token caps, and output-format choices alongside pass rates.
