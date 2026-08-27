# TaskBench CLI reference

This reference summarizes the TaskBench command surfaces that matter at runtime. Commands below assume a user-provided checkout with a `taskbench/` directory and a Python environment where the TaskBench requirements are installed. Keep all output directories explicit when creating fixtures or running evaluations.

## Dependency-type selection

| Data or tool shape | Required dependency type | Why |
| --- | --- | --- |
| HuggingFace Tools domain | `resource` | Tool records have `input-type` and `output-type`; edges represent resource flow. |
| Multimedia Tools domain | `resource` | Tool records have `input-type` and `output-type`; edges represent resource flow. |
| Daily Life APIs domain | `temporal` | Tool records have request `parameters`; edges represent API order. |
| Custom tool library with `input-type`/`output-type` | `resource` | Graph links can be inferred by matching output resources to input resources. |
| Custom tool library with `parameters` only | `temporal` | No resource matching is available; links are temporal invocation order. |

If the data directory is Daily Life APIs or the first tool has `parameters` but no `input-type`, route to `temporal`. Native inference asserts when Daily Life APIs is paired with `resource`.

## OpenAI-compatible inference

Native inference posts to `/v1/chat/completions` on the host and port provided by `--api_addr` and `--api_port`. It appends prediction JSONL to a directory inside the data directory.

Safe shape:

```bash
python taskbench/inference.py \
  --llm MODEL_NAME \
  --data_dir DATA_DIR \
  --temperature 0.2 \
  --top_p 0.1 \
  --api_addr HOST \
  --api_port PORT \
  --api_key "$API_KEY" \
  --multiworker 1 \
  --use_demos 0 \
  --reformat true \
  --reformat_by self \
  --dependency_type resource \
  --tag true \
  --log_first_detail true
```

Important options:

- `--data_dir`: directory containing `tool_desc.json`, `user_requests.json`, and usually `data.json`.
- `--llm`: model field sent to the OpenAI-compatible server and output JSONL basename.
- `--api_addr`, `--api_port`, `--api_key`: endpoint prerequisites; no endpoint is started by TaskBench itself.
- `--multiworker`: concurrent async requests. Start with `1` for smoke runs; raise only after endpoint stability is known.
- `--use_demos`: number of built-in few-shot examples to include. Valid small values are `0` to `3`.
- `--reformat`: if true, malformed model JSON is sent through a second formatting request before the line is written.
- `--reformat_by`: `self` keeps the same model; another model name routes formatting to that model.
- `--tag`: when true, the prediction directory name records demo and reformat settings.
- `--dependency_type`: `resource` or `temporal` according to the mapping above.

Prediction directory naming:

- Base directory is `DATA_DIR/predictions`.
- With `--tag true`, `_use_demos_N` is appended when demos are used.
- With `--tag true --reformat true`, `_reformat_by_NAME` is appended.
- The prediction file is `MODEL_NAME.json`; the log is `MODEL_NAME.log`.

## Evaluation

Native evaluation reads labels from `DATA_DIR/data.json` and predictions from `DATA_DIR/PREDICTION_DIR/MODEL_NAME.json`. It writes metrics under a metrics directory inside `DATA_DIR` unless `--save_dir` is provided.

Safe shape:

```bash
python taskbench/evaluate.py \
  --data_dir DATA_DIR \
  --prediction_dir PREDICTION_DIR \
  --llm MODEL_NAME \
  --splits all \
  --n_tools all \
  --mode add \
  --dependency_type temporal \
  -m all
```

Important options:

- `--prediction_dir`: directory name relative to `DATA_DIR`, not a free-standing output path for native evaluation.
- `--save_dir`: optional metrics directory name under `DATA_DIR`. If omitted, native code replaces `predictions` with `metrics` in `--prediction_dir`.
- `--splits`: repeatable; `all` expands to `overall`, `single`, `chain`, and `dag`.
- `--n_tools`: repeatable; `all` expands to `overall` and tool counts `1` through `10`.
- `--mode add`: evaluate split groups plus tool-count groups separately. `mul` evaluates every split/count pair.
- `--metric` or `-m`: repeatable. `all` expands to node F1, edit distance, link F1, argument F1, Rouge, and BERTScore when `--prompting cot`.
- `--alignment`: optional alignment subset name. Non-human values are looked up in `alignment_ids.json`.
- `--prompting`: if not `cot`, native `all` skips Rouge and BERTScore.

Use the bundled [batch wrapper](../scripts/batch_evaluate.sh) when evaluating every model JSON in a prediction directory.

## Graph generation and sampling

Native graph generation and visualization use implicit output paths. Prefer the bundled [graph tools](../scripts/taskbench_graph_tools.py), which require explicit outputs:

```bash
python SUB_SKILL_DIR/scripts/taskbench_graph_tools.py generate-graph \
  --input TOOL_DESC_JSON \
  --output GRAPH_DESC_JSON \
  --dependency-type resource

python SUB_SKILL_DIR/scripts/taskbench_graph_tools.py sample-graph \
  --input GRAPH_DESC_JSON \
  --output SAMPLE_GRAPH_JSON \
  --method chain \
  --num-nodes 3 \
  --seed 0

python SUB_SKILL_DIR/scripts/taskbench_graph_tools.py visualize \
  --input SAMPLE_GRAPH_JSON \
  --output SAMPLE_GRAPH_PNG
```

Native evidence behavior to remember:

- Native `generate_graph.py` infers resource links by intersecting output resource types with target input resource types; temporal links are complete directed links between every pair of tools.
- Native `graph_sampler.py` supports `single`, `chain`, and `dag`; when `--save_figure` is true it writes a hard-coded figure name in the current working directory.
- Native `visualize_graph.py` reads `DATA_DIR/graph_desc.json`, calls an interactive show operation, and saves beside the graph file. Use the bundled helper for headless automation.

## Back-Instruct data construction

Back-Instruct generation is a credentialed inference workflow. Do not run it without explicit endpoint authorization and bounded output paths.

Safe shape for a tiny generation run:

```bash
python taskbench/data_engine.py \
  --graph_desc GRAPH_DESC_JSON \
  --tool_desc TOOL_DESC_JSON \
  --data_dir OUTPUT_DATA_DIR \
  --number_of_samples 5 \
  --multiworker 1 \
  --llm MODEL_NAME \
  --temperature 1.0 \
  --top_p 1.0 \
  --dependency_type resource \
  --save_figure false \
  --check true \
  --api_addr HOST \
  --api_port PORT \
  --api_key "$API_KEY"
```

Then format the raw generation in the same output directory:

```bash
python taskbench/format_data.py \
  --data_dir OUTPUT_DATA_DIR \
  --dependency_type resource
```

`format_data.py` overwrites `data.json`, `user_requests.json`, and `data_error.json` in the output directory, so use a temporary or intentionally generated directory.

## Validation before evaluation

Run the bundled validator before evaluation or after any data construction step:

```bash
python SUB_SKILL_DIR/scripts/validate_taskbench_fixture.py \
  --tool-desc DATA_DIR/tool_desc.json \
  --graph-desc DATA_DIR/graph_desc.json \
  --data-jsonl DATA_DIR/data.json \
  --user-requests-jsonl DATA_DIR/user_requests.json \
  --predictions-jsonl DATA_DIR/PREDICTION_DIR/MODEL_NAME.json \
  --dependency-type auto \
  --strict
```

The validator emits a JSON summary and exits non-zero when required schemas are invalid.
