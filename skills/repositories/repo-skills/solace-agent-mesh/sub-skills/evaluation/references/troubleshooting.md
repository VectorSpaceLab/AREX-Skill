# Evaluation troubleshooting

Use this guide when a suite parses but fails to run, or when the results do not match the expected behavior.

## Fast triage order

1. Run the offline validator.
2. Check the suite mode boundary.
3. Check local file references.
4. Check broker, gateway, and namespace settings.
5. Check scorer settings and expected outputs.

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `sam eval` says the path does not exist | The suite path is wrong or not a file | Point the command to an existing config file, not a directory. |
| JSON parse errors | The suite or test case is malformed, or a YAML-style file was passed to the live loader | Rewrite the file as valid JSON for live execution, or use the offline validator to catch the syntax issue first. |
| Suite validation says local and remote settings are mixed | The config contains both `remote` and local-only keys | Remove one mode and keep the required fields for the other. |
| Local run fails because the gateway plugin is missing | `sam-rest-gateway` is not installed | Install the gateway plugin in the same environment that runs the evaluation. |
| Local run fails while creating backend config | The project does not have the expected evaluation-backend scaffolding | Run the project bootstrap flow first, then retry the evaluation. |
| Remote run fails with 401 or 403 | Missing or wrong auth token | Check `EVAL_AUTH_TOKEN` and whether the remote gateway requires it. |
| Remote run fails with 404 or connection errors | Wrong `EVAL_REMOTE_URL`, wrong namespace, or the gateway is down | Confirm the base URL, namespace, and reachability before retrying. |
| Broker connection fails | Broker credentials or host values are missing | Check the `_VAR` references and the actual environment variables they point to. |
| A run times out | `wait_time` is too short, the agent is slow, or worker contention is too high | Increase the per-test `wait_time`, reduce `workers`, or simplify the test case. |
| Tool-match scores look wrong | Expected tool names do not match the names captured in the summary | Compare `expected_tools` against the actual `tool_calls[*].tool_name` values. |
| Response-match scores look low | ROUGE is sensitive to wording and synonym changes | Tighten the expected response, or rely more on tool match or LLM judging. |
| LLM scores are missing | `llm_evaluator` is disabled or its env values are incomplete | Enable it explicitly and provide `LLM_SERVICE_PLANNING_MODEL_NAME`, `LLM_SERVICE_ENDPOINT`, and `LLM_SERVICE_API_KEY`. |
| File artifact lookups fail | The artifact path is relative to the test case file, not the suite file | Recompute the path from the test case directory and confirm the file exists. |
| Output folders appear overwritten | The runner clears `results/<results_dir_name>/` before each run | Use a new `results_dir_name` when you need to keep an older run. |

## Mode confusion

### Local mode mistakes

Local evaluation needs:

- `agents`
- `broker`
- `llm_models`
- `test_cases`
- `results_dir_name`

Do not include `remote` in the same file.

If local mode fails before any tasks are sent, the issue is usually one of these:

- Missing `sam-rest-gateway`
- Missing or incomplete broker credentials
- Bad model environment values
- Broken relative paths for agents or test cases

### Remote mode mistakes

Remote evaluation needs:

- `broker`
- `remote`
- `test_cases`
- `results_dir_name`

Do not include local-only keys in the same file.

If remote mode fails before the first test case completes, the issue is usually one of these:

- Wrong remote base URL
- Wrong namespace
- Missing auth token for a protected gateway
- Broker credentials that do not match the target environment

## Missing file checks

Before a live run, verify these paths locally:

- suite file path
- each suite-relative agent file
- each suite-relative test case file
- each file artifact path relative to its test case file

The bundled validator can flag these without contacting live services.

## Malformed JSON or YAML

The live loader is JSON-oriented. If a file is meant for live evaluation, keep it valid JSON.

When you want a lighter preflight path:

- Use the offline validator to inspect the file.
- Fix any syntax issues it reports.
- Convert the file to JSON before invoking `sam eval`.

## Scorer mismatch fixes

### Tool match

If the score is lower than expected:

- Check that the tool name in `expected_tools` matches the real tool name exactly.
- Make sure the tool was actually invoked in the run summary.
- Remember that an empty expected tool list scores as `1.0`.

### Response match

If the score is lower than expected:

- Compare against the actual `final_message` in `summary.json`.
- Avoid relying on paraphrases or synonym-heavy answers.
- Narrow the expected response to the stable part of the reply.

### LLM evaluator

If the judge output is missing or inconsistent:

- Confirm that the model name, endpoint, and API key are set.
- Make the `criterion` concrete and specific.
- Check that the prompt and expected response describe the same outcome.

## When the helper script is enough

Use `scripts/validate_eval_inputs.py` when you only need to:

- Inventory a suite or test case set.
- Confirm that file paths exist.
- Review `_VAR` references.
- Catch local-vs-remote mistakes early.

Use the live `sam eval` command only after those checks pass.
