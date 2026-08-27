# Evaluation workflows

This reference explains how to prepare, run, and inspect `sam eval` without contacting live services during preflight.

## Command surface

```bash
sam eval <PATH> [-v]
```

- `<PATH>` must point to an existing suite configuration file.
- The CLI resolves the path before handing it to the evaluation runner.
- `-v` / `--verbose` enables richer logs.
- The live loader is JSON-based, so a file that only looks like YAML will still fail unless it is valid JSON syntax.

## Choose a mode

`sam eval` supports two mutually exclusive suite shapes:

- **Local evaluation**
  - Use when the agents run on the local machine.
  - Include `agents`, `broker`, `llm_models`, and `test_cases`.
  - Do not include `remote`.
- **Remote evaluation**
  - Use when the target SAM instance is already running elsewhere and exposes a REST gateway.
  - Include `broker`, `remote`, and `test_cases`.
  - Do not include `agents` or `llm_models`.

In both modes, provide `results_dir_name`. The current loader treats it as required even though some older prose describes a default.

## Local evaluation prerequisites

Before a local run, make sure the following are available:

- A local SAM project or app that can be started on the machine running the evaluation.
- The `sam-rest-gateway` package installed in the same environment that runs the evaluation command.
- Broker credentials in the environment or in `_VAR` references inside the suite config.
- Any LLM service credentials required by the models you name in `llm_models`.
- A generated evaluation-backend config if the runner needs to create one.

Local runs are the right choice when you want to compare model choices, iterate on prompts, or inspect messages and summaries from a local agent mesh.

## Remote evaluation prerequisites

Before a remote run, make sure the following are available:

- A reachable REST gateway URL in `remote`.
- A namespace value for the remote task stream.
- Broker credentials for the event broker used by the remote mesh.
- An auth token if the remote gateway is protected.
- Any LLM service credentials required by the evaluation settings.

Remote runs are the right choice when the target agents already exist in another environment and you only want to drive test cases against that endpoint.

## Execution flow

A live `sam eval` run follows this sequence:

1. Load the suite config.
2. Resolve relative paths from the suite file directory.
3. Validate mode boundaries and required fields.
4. Create or replace `results/<results_dir_name>/` under the current working directory.
5. Start local services or prepare the remote subscriber path.
6. Submit each test case for each run.
7. Collect messages and summarize each run.
8. Score the results.
9. Write `results.json`, `stats.json`, and `report.html`.

The runner removes any existing results directory with the same name before writing new output. Use a unique `results_dir_name` if you need to preserve an older run.

## Result tree

Local runs write one directory per model name. Remote runs write a single `remote/` directory.

```text
results/<results_dir_name>/
├── report.html
├── stats.json
├── <model_name>/
│   ├── full_messages.json
│   ├── results.json
│   ├── task_mappings.json
│   └── <test_case_id>/
│       └── run_<n>/
│           ├── messages.json
│           ├── summary.json
│           └── test_case_info.json
└── remote/
    ├── full_messages.json
    ├── results.json
    └── ...
```

### What the main files mean

- `report.html`: human-readable HTML report.
- `stats.json`: overall execution time and score statistics.
- `full_messages.json`: the full message stream captured for a model or remote run.
- `results.json`: aggregated scoring for each test case.
- `messages.json`: the per-run message capture used to build summaries.
- `summary.json`: extracted run summary with final response, tool calls, artifacts, and timing.
- `test_case_info.json`: the original test case path for the run.
- `task_mappings.json`: task-id-to-result-path mapping used during collection and post-processing.

## When to use the offline validator

Use `scripts/validate_eval_inputs.py` before live evaluation when you want to:

- Check that suite and test case files parse.
- List the test cases included in a suite.
- Verify that local file references exist.
- See which environment variables a suite references.
- Catch mixed local/remote configs before the live run starts.

The validator never submits tasks or contacts a live broker or gateway.
