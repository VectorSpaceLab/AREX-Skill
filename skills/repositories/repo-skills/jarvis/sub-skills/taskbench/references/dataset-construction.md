# TaskBench dataset construction

TaskBench constructs benchmark examples by building a tool graph, sampling subgraphs, prompting an OpenAI-compatible model to Back-Instruct user requests and invoking graphs, and formatting the generated raw data. Treat model-backed construction as a credentialed network workflow and keep all generated files in explicit output directories.

## Construction stages

1. **Tool library**: create `tool_desc.json` with a top-level `nodes` list.
2. **Tool graph**: create `graph_desc.json` from the tool library or edit it manually.
3. **Graph sampling**: sample single-tool, chain, or DAG subgraphs.
4. **Back-Instruct generation**: call an OpenAI-compatible endpoint to synthesize user requests, task steps, and invoking graphs.
5. **Formatting**: convert `data_raw.json` into evaluator-style `data.json` and `user_requests.json`.
6. **Validation**: validate tool, graph, data, user-request, and prediction fixtures before inference or evaluation.

## Choose resource or temporal construction

Use `resource` when tools have resource-type I/O:

```json
{"id": "Text-to-Speech", "input-type": ["text"], "output-type": ["audio"]}
```

Use `temporal` when APIs have request parameters:

```json
{"id": "send_sms", "parameters": [{"name": "phone_number", "type": "string"}]}
```

Daily Life APIs are temporal. Selecting resource for Daily Life APIs is not a recoverable runtime choice; route to temporal and explain the assertion.

## Safe graph generation

Prefer the bundled graph helper because native graph generation chooses its output by string replacement on the input filename.

Resource graph:

```bash
python SUB_SKILL_DIR/scripts/taskbench_graph_tools.py generate-graph \
  --input TOOL_DESC_JSON \
  --output GRAPH_DESC_JSON \
  --dependency-type resource
```

Temporal graph:

```bash
python SUB_SKILL_DIR/scripts/taskbench_graph_tools.py generate-graph \
  --input TOOL_DESC_JSON \
  --output GRAPH_DESC_JSON \
  --dependency-type temporal
```

Review generated links manually before using the graph for dataset construction. Resource graph generation only checks type intersections; it does not know whether a tool chain is semantically useful.

## Safe graph sampling

```bash
python SUB_SKILL_DIR/scripts/taskbench_graph_tools.py sample-graph \
  --input GRAPH_DESC_JSON \
  --output SAMPLE_GRAPH_JSON \
  --method dag \
  --num-nodes 4 \
  --seed 7
```

Supported sample methods:

- `single`: one tool/API node.
- `chain`: a path-like sample using predecessor/successor expansion.
- `dag`: a directed acyclic-style sample using existing graph edges where possible.

Use small samples for smoke tests. A sampled graph is a fixture for validating schemas and prompts, not a replacement for benchmark-scale sampling.

## Safe graph visualization

```bash
python SUB_SKILL_DIR/scripts/taskbench_graph_tools.py visualize \
  --input GRAPH_DESC_JSON \
  --output GRAPH_IMAGE_OR_PDF \
  --title "TaskBench graph"
```

The helper uses headless matplotlib and writes only the explicit output path. This avoids native visualization behavior that opens an interactive display and saves beside the graph file.

## Back-Instruct generation with native data engine

Only run this after the user provides an endpoint and API key or compatible token. Keep counts small until the endpoint and schema are proven.

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
  --dependency_type temporal \
  --save_figure false \
  --check true \
  --api_addr HOST \
  --api_port PORT \
  --api_key "$API_KEY"
```

Native data engine behavior:

- If `--data_dir` is omitted, it writes a timestamped `result_*` directory in the current working directory. Always pass `--data_dir`.
- If `--data_dir` already exists, native code ignores separately provided `--graph_desc` and `--tool_desc` and resumes from files inside that directory.
- It writes `data_raw.json`, `statistics.json`, `data_engine.log`, copied graph/tool descriptions, and optional `task_graphs/` figures.
- `--play true` samples one graph and prints the generated result, but still calls the endpoint.
- `--use_async true` changes concurrency behavior; keep `--multiworker` conservative until rate limits are known.

## Formatting generated data

After `data_engine.py` creates `data_raw.json`, format the generated directory:

```bash
python taskbench/format_data.py \
  --data_dir OUTPUT_DATA_DIR \
  --dependency_type temporal
```

Formatter behavior:

- Reads `OUTPUT_DATA_DIR/data_raw.json`.
- Writes `data.json`, `user_requests.json`, and `data_error.json` with truncating writes.
- Converts generated invoking graph nodes into `task_nodes` and generated steps into `task_steps`.
- For resource data, converts references to prior tool outputs into `<node-j>` arguments.

Use a temporary or intentionally generated output directory because formatting overwrites those files.

## Validate constructed fixtures

Validate immediately after graph generation, after formatting, and before evaluation:

```bash
python SUB_SKILL_DIR/scripts/validate_taskbench_fixture.py \
  --tool-desc OUTPUT_DATA_DIR/tool_desc.json \
  --graph-desc OUTPUT_DATA_DIR/graph_desc.json \
  --data-jsonl OUTPUT_DATA_DIR/data.json \
  --user-requests-jsonl OUTPUT_DATA_DIR/user_requests.json \
  --dependency-type auto
```

With predictions:

```bash
python SUB_SKILL_DIR/scripts/validate_taskbench_fixture.py \
  --tool-desc OUTPUT_DATA_DIR/tool_desc.json \
  --graph-desc OUTPUT_DATA_DIR/graph_desc.json \
  --data-jsonl OUTPUT_DATA_DIR/data.json \
  --user-requests-jsonl OUTPUT_DATA_DIR/user_requests.json \
  --predictions-jsonl OUTPUT_DATA_DIR/predictions/MODEL_NAME.json \
  --dependency-type auto \
  --strict
```

The validator accepts both normalized evaluator rows and legacy released-data rows, but it warns when legacy rows need conversion before native evaluation.

## Native script import map

| Source behavior | Runtime recommendation |
| --- | --- |
| Graph generation | Use bundled `taskbench_graph_tools.py generate-graph` for explicit output. |
| Graph sampling | Use bundled `sample-graph` for deterministic fixtures; native sampler remains useful as source behavior evidence. |
| Graph visualization | Use bundled `visualize` for headless output. |
| Inference | Use native inference only with explicit endpoint/API prerequisites and validation. |
| Evaluation | Use native evaluation or bundled batch wrapper after validating predictions. |
| Data engine | Use native data engine only for authorized Back-Instruct generation. |
| Format data | Use native formatter in generated/temp directories; it writes truncating outputs. |

## Tiny fixture workflow

A safe local fixture can avoid network calls entirely:

1. Write a two-tool `tool_desc.json` in a temporary directory.
2. Generate `graph_desc.json` with the bundled graph helper.
3. Sample a one- or two-node graph with the bundled graph helper.
4. Handwrite one normalized `data.json` line, one `user_requests.json` line, and one prediction line.
5. Run the bundled validator.
6. Run native evaluation only if the TaskBench environment has the required metric dependencies and the fixture uses normalized evaluator fields.
