# Evaluation Workflows

ADK has two complementary test/eval paths:

- `adk test` replays event-session JSON fixtures under agent `tests/` directories and compares normalized `Event` output.
- `adk eval` and `google.adk.evaluation.AgentEvaluator` run metric-based evaluations over EvalSet data.

Use `adk test` when the assertion is exact event flow, tool-call visibility, HITL function responses, random-mocked behavior, or workflow node routing. Use EvalSet evaluation when the assertion is a score over final text, tool trajectory, safety, rubrics, or multi-turn task success.

## `adk test` Event Replay

`adk test FOLDER` discovers files matching `tests/*.json` below each agent directory. An agent directory is recognized when it contains `agent.py`, `__init__.py`, or `root_agent.yaml`.

Typical commands:

```bash
adk test path/to/agents_dir
adk test path/to/agents_dir -- -k hello_world -q
adk test path/to/agents_dir --rebuild
```

Important behavior:

- `adk test` runs a pytest-based runner with `ADK_TEST_FOLDER` set to the folder being tested.
- The runner loads each agent through ADK's agent loader, sets workflow/node concurrency to deterministic sequential mode, seeds `random`, and normalizes event IDs, invocation IDs, timestamps, model metadata, usage metadata, and empty actions.
- Fixture `mocks` can supply values such as `random.randint` and `random.random` so generated tool results remain stable.
- The first user event supplies the initial prompt; later user events with function responses drive multi-turn, HITL, and tool-confirmation replay.
- The `--rebuild` mode reruns the agent live and rewrites discovered JSON fixtures; do this only when the intended behavior changed.

Minimal event-replay fixture shape:

```json
{
  "events": [
    {
      "author": "user",
      "content": {"role": "user", "parts": [{"text": "Roll a 6-sided die"}]},
      "id": "e-1",
      "invocationId": "i-1",
      "nodeInfo": {"path": ""}
    },
    {
      "author": "agent_name",
      "content": {"role": "model", "parts": [{"functionCall": {"id": "fc-1", "name": "roll_die", "args": {"sides": 6}}}]},
      "id": "e-2",
      "invocationId": "i-1",
      "nodeInfo": {"path": "agent_name@1"}
    }
  ],
  "mocks": {"random.randint": [6]}
}
```

Validation checklist for event fixtures:

- Include at least one user event with `content.parts[0].text`.
- Preserve `functionCall.id` and matching `functionResponse.id` pairs; the runner remaps IDs for deterministic comparison.
- Use `nodeInfo.path` to assert workflow node/branch routing; `author` can be the enclosing workflow while the node identity lives in the path.
- Keep expected model/tool events minimal but complete enough to prove the behavior; volatile fields are normalized, but semantic content and tool arguments are compared.
- Prefer `-- -k NAME -q` to focus a failing fixture before rebuilding all tests.

## EvalSet JSON For `adk eval` And `AgentEvaluator`

The current EvalSet schema is a JSON object with `eval_set_id`, optional `name`/`description`, and `eval_cases`. Each `EvalCase` must provide exactly one of `conversation` or `conversation_scenario`.

Core model names:

- `EvalSet`: `eval_set_id`, `name`, `description`, `eval_cases`, `creation_timestamp`.
- `EvalCase`: `eval_id`, `conversation`, `conversation_scenario`, `session_input`, `rubrics`, `final_session_state`.
- `Invocation`: `invocation_id`, `user_content`, `final_response`, `intermediate_data`, `rubrics`, `app_details`.
- `IntermediateData`: `tool_uses`, `tool_responses`, `intermediate_responses`.
- `InvocationEvents`: `invocation_events` for deriving tool calls/responses from event-like records.
- `SessionInput`: `app_name`, `user_id`, `state`.

Minimal EvalSet for one static turn:

```json
{
  "eval_set_id": "smoke",
  "name": "smoke",
  "eval_cases": [
    {
      "eval_id": "roll_die_tool_call",
      "conversation": [
        {
          "user_content": {"role": "user", "parts": [{"text": "Roll a 6-sided die"}]},
          "final_response": {"role": "model", "parts": [{"text": "You rolled a 6-sided die."}]},
          "intermediate_data": {
            "tool_uses": [{"name": "roll_die", "args": {"sides": 6}}],
            "tool_responses": [],
            "intermediate_responses": []
          }
        }
      ]
    }
  ]
}
```

Legacy JSON list format is still accepted and migrated internally. It is a list of cases with `name`, `data`, and optional `initial_session`. Each `data` row uses `query`, `reference`, `expected_tool_use`, and `expected_intermediate_agent_responses`. Use this only when updating older fixtures; prefer the EvalSet object for new work.

Legacy row example:

```json
[
  {
    "name": "roll_17_sided_dice_twice",
    "data": [
      {
        "query": "Roll a 17 sided dice twice for me",
        "expected_tool_use": [
          {"tool_name": "roll_die", "tool_input": {"sides": 17}},
          {"tool_name": "roll_die", "tool_input": {"sides": 17}}
        ],
        "expected_intermediate_agent_responses": [],
        "reference": "I rolled a 17-sided die twice."
      }
    ],
    "initial_session": {"state": {}, "app_name": "hello_world", "user_id": "user"}
  }
]
```

## Evaluation Config And Metrics

`test_config.json` or `--config_file_path` supplies an `EvalConfig`. If absent, ADK defaults to:

```json
{
  "criteria": {
    "tool_trajectory_avg_score": 1.0,
    "response_match_score": 0.8
  }
}
```

Metric/config objects to know:

- `EvalConfig.criteria`: metric name to threshold or criterion object.
- `BaseCriterion`: `threshold`, `include_intermediate_responses_in_final`.
- `ToolTrajectoryCriterion`: `threshold`, `match_type` with `EXACT`, `IN_ORDER`, or `ANY_ORDER`.
- `LlmAsAJudgeCriterion` and rubric criteria: include `judge_model_options` with `judge_model`, optional generation config, and `num_samples`.
- `CustomMetricConfig`: `code_config.name`, optional `metric_info`, and description.
- `EvaluateConfig.parallelism` and `InferenceConfig.parallelism`: defaults are `4`; lower them for quota-sensitive model/tool runs.
- `InferenceConfig.use_live` and `live_timeout_seconds`: needed only for live/bidirectional models.

Prebuilt metric names include:

- `tool_trajectory_avg_score`
- `response_evaluation_score`
- `response_match_score`
- `safety_v1`
- `final_response_match_v2`
- `rubric_based_final_response_quality_v1`
- `hallucinations_v1`
- `rubric_based_tool_use_quality_v1`
- `per_turn_user_simulator_quality_v1`
- `multi_turn_task_success_v1`
- `multi_turn_trajectory_quality_v1`
- `multi_turn_tool_use_quality_v1`
- `rubric_based_multi_turn_trajectory_quality_v1`

Legacy validation rules are strict for default metrics:

- `tool_trajectory_avg_score` needs `query` and `expected_tool_use` in old-format rows.
- `response_match_score` needs `query` and `reference` in old-format rows.
- Unsupported legacy criterion keys raise an invalid-criteria error.

## CLI `adk eval`

Command shape:

```bash
adk eval path/to/agent/__init__.py path/to/evalset.json --config_file_path path/to/test_config.json --print_detailed_results
adk eval path/to/agent/__init__.py path/to/evalset.json:case_a,case_b
adk eval path/to/agent/__init__.py eval_set_id:case_a --eval_storage_uri gs://bucket
```

Behavior and assumptions:

- `AGENT_MODULE_FILE_PATH` points to an `__init__.py` whose module exposes `agent.root_agent`.
- Eval inputs may be file paths or EvalSet IDs; do not mix file paths and IDs in one invocation.
- File-path EvalSets are loaded into an in-memory manager for that run.
- EvalSet IDs are read from local storage under the agent parent directory unless `--eval_storage_uri` is supplied.
- `--eval_storage_uri` currently supports `gs://bucket` and requires GCP dependencies plus `GOOGLE_CLOUD_PROJECT`.
- `--print_detailed_results` prints per-invocation prompt, expected/actual response, expected/actual tool calls, scores, thresholds, and rubric rationale when available.

Failure boundary:

- Missing eval dependencies are reported as: install `google-adk[eval]`.
- GCS eval managers require GCP optional dependencies; base installs may not include them.
- Judge-model metrics require model credentials and quota; deterministic metrics can still validate schema and tool trajectory without external judge calls.

## `adk eval_set` Management

Commands exposed by the CLI include:

```bash
adk eval_set create path/to/agent/__init__.py smoke
adk eval_set add_eval_case path/to/agent/__init__.py smoke --scenarios_file scenarios.json --session_input_file session_input.json
adk eval_set generate_eval_cases path/to/agent/__init__.py smoke --user_simulation_config_file generation_config.json
```

Use cases:

- `create` creates an empty EvalSet for an app.
- `add_eval_case` reads serialized `ConversationScenarios` and `SessionInput`, hashes each scenario into a stable eval id, and skips duplicates.
- `generate_eval_cases` uses Vertex AI Eval SDK scenario generation and may create the EvalSet if missing; treat this as credential/cloud-dependent.

## Programmatic `AgentEvaluator`

Use `AgentEvaluator` for Python tests or focused local scripts:

```python
from google.adk.evaluation.agent_evaluator import AgentEvaluator

await AgentEvaluator.evaluate(
    agent_module="my_agent_package",
    eval_dataset_file_path_or_dir="path/to/eval_files",
    num_runs=2,
    agent_name=None,
    initial_session_file=None,
    print_detailed_results=True,
)
```

Key details:

- `eval_dataset_file_path_or_dir` can be a single file or a directory recursively scanned for `.test.json` files.
- `find_config_for_test_file()` looks for `test_config.json` in the same folder as the test file.
- The agent module must expose `agent.root_agent`, `root_agent`, or `get_agent_async` through the expected module convention.
- `agent_name` selects a sub-agent via `root_agent.find_agent(agent_name)`.
- `num_runs` defaults to repeated runs to average stochastic behavior; increase for confidence, decrease for speed/quota.
- `migrate_eval_data_to_new_schema(old, new)` converts old list-format data into an EvalSet JSON file.

## Assertion Strategy

Design evals so failures point to one behavioral question.

- For tool-call observability, assert `intermediate_data.tool_uses` in EvalSet data or `functionCall` parts in event replay JSON.
- For multi-turn state, include `session_input.state` and/or expected `final_session_state`; also summarize actual session events to confirm the state delta landed.
- For sub-agent/workflow routing, inspect `author`, `intermediate_responses`, and `nodeInfo.path`; do not rely only on final text.
- For final responses, use deterministic `response_match_score` when text is stable and rubric/LLM-as-judge metrics only when wording can vary.
- For flaky models, use lower parallelism, `num_runs`, rubrics with explicit thresholds, and deterministic tool mocks where possible.

## Converting An Interaction Into A Fixture

For a user request like “convert this sample interaction into an `adk test` JSON and debug why expected tool calls are not observed”:

1. Capture or write the first user event with `author: "user"`, `content.role: "user"`, and a text part.
2. Add expected model events for each relevant function call: `content.role: "model"`, `functionCall.name`, `functionCall.args`, and a stable `id`.
3. Add tool response/user events when the next agent turn depends on a function result or HITL response.
4. Add final model text if the response is deterministic enough to assert.
5. Put mocked random values under `mocks` when tool output is random.
6. Run `adk test AGENTS_DIR -- -k TEST_STEM -q` and compare actual events with `scripts/summarize_adk_events.py` if the assertion is noisy.
7. If the call is missing, confirm the agent actually declares the tool, the model received the tool declaration, and the expected event uses the exact function name/args shape.

## Native Verification Candidate Selection

Safe local candidates for this sub-skill:

```bash
adk test --help
adk eval --help
adk eval_set --help
# In an ADK source checkout, run the focused evaluation unit-test target.
# In an ADK source checkout, run selected integration tests that exercise EvalSet and JSON test-file behavior.
```

Selection rules:

- Prefer `adk --help` and command-specific `--help` for CLI surface checks; they avoid model/network side effects.
- Prefer focused evaluation unit coverage for schema, metrics, managers, and evaluator utilities.
- Use selected integration tests only when the agent fixture behavior is relevant and the environment has required dependencies.
- Skip or isolate tests that require real model credentials, cloud storage, web servers, live API, or optional extras not present in the base install.
