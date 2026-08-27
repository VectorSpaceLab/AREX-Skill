# EasyTool API and Module Reference

EasyTool's internal modules are ordinary Python files under the inner `easytool/` package directory. Importing them requires `OPENAI_API_KEY` to be present because module top levels set `openai.api_key = os.environ["OPENAI_API_KEY"]`. Several modules also use absolute `from util import *`, so add the inner package directory to `PYTHONPATH` before imports.

## Import pattern

```bash
cd "$REPO_ROOT/easytool"
export PYTHONPATH="$PWD/easytool${PYTHONPATH:+:$PYTHONPATH}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-sk-dummy-for-help-only}"
python - <<'PY'
from easytool import funcQA, restbench, toolbench, toolbench_retrieve
from easytool.util import build_index, get_last_processed_index
print("imports ok")
PY
```

Use a dummy key only for import/help checks. Any function that constructs `ChatOpenAI`, calls `openai.Embedding.create`, or runs task execution needs real credentials.

## Dispatcher behavior in `main.py`

The CLI parses options and then dispatches:

- `args.task == "funcqa"`: loads FuncQA instructions and `data_funcqa/test_data/<data_type>.json`; progress file `FuncQA_<data_type>_<model>_Easytool.txt`.
- `'toolbench' in args.task`: loads ToolBench instructions and generated `G2_category.json` or `G3_instruction.json`; builds an index from `--tool_root_dir`; progress file `<data_type>_<model>_Easytool.txt`.
- `args.task == "restbench"`: loads RestBench tool instructions and `data_restbench/test_data/tmdb.json`; progress file `restbench_<model>_Easytool.txt`.
- Otherwise prints `Wrong task name` and exits.

After loading data, `main.py` computes `start_index = get_last_processed_index(progress_file)`, `total_files = len(test_data)`, and `ind = start_index`, then calls the task executor selected by `data_type` and `task`.

## Verified task-execution signatures

These callable signatures were verified from source/inspection evidence:

```python
funcQA.task_execution_mh(
    data_type, start_index, total_files, retrieval_num, ind, model_name,
    dataset, Tool_dic, test_data, progress_file,
)

funcQA.task_execution_oh(
    data_type, start_index, total_files, retrieval_num, ind, model_name,
    dataset, Tool_dic, test_data, progress_file,
)

restbench.task_execution(
    Tool_dic, dic_tool, test_data, progress_file,
    start_index, total_files, retrieval_num, ind, model_name,
)

toolbench.task_execution(
    data_type, base_path, index, dataset, test_data, progress_file,
    start_index, total_files, retrieval_num, ind, model_name,
)

toolbench_retrieve.task_execution(
    data_type, base_path, index, dataset, test_data, progress_file,
    start_index, total_files, retrieval_num, ind, model_name,
)
```

Prefer the CLI for normal operation because it constructs all positional arguments consistently. Direct calls are useful for tests or bounded wrappers only after you recreate the same data loading, index building, progress handling, and environment variables.

## Utility functions

`easytool.util` provides the shared low-level helpers:

| Function | Purpose |
| --- | --- |
| `read_jsonline(address)` | Load a JSONL file into a list. |
| `save_json(ls, address)` | Write JSON with `ensure_ascii=False` and indentation. |
| `read_json(address)` | Load JSON from a file. |
| `remove_key(item, key_to_remove)` / `data_clean(dic, key)` | Recursively remove a key from nested dict/list structures. |
| `lowercase_parameter_keys(input_dict)` | Normalize `parameters` keys with `change_name`. |
| `build_index(base_path)` | Recursively index directory names under ToolBench tool code; values are parent paths. |
| `change_name(name)` | Prefix reserved/unsafe names such as `from`, `class`, `return`, `id`, `true`, `false`, or empty string. |
| `standardize(string)` | Lowercase, replace non-word characters with underscores, trim underscores, and prefix digit-leading names with `get_`. |
| `get_last_processed_index(progress_file)` | Read a plain integer progress file or return 0. |
| `update_progress(progress_file, index)` | Overwrite the progress file with the latest index. |

## Workflow internals

### FuncQA

- Multi-hop: decompose question into tasks, infer topology, retrieve a math tool for each subtask, call `data_funcqa/funchub/math.py`, generate sub-answers, summarize, and check the final answer.
- One-hop: treat the question as a single task, retrieve/call one or more math tools, summarize, and check.
- Tool-call failures can write `wrong_log.json` in the current working directory.
- Retry loops use `retrieval_num` for alternate tool attempts when call results are blank or `-1`.

### ToolBench direct

- Uses each test item's `Tool_dic` as the candidate tool list.
- `tool_check` asks the model whether a subtask needs an external API.
- If a tool is needed, `choose_tool`, `choose_API`, and `choose_parameter` parse model outputs using Python evaluation.
- `Call_function` imports a selected tool's `api.py`, injects `toolbench_rapidapi_key`, normalizes parameter names, and calls the selected API function.
- Failures can append JSON lines to `wrong_log.json`.

### ToolBench retrieve

- Loads local `(filenames, embedded_texts)` from `API_description_embeddings.pkl`.
- Calls OpenAI embeddings for each subtask query and selects the top five tool-description references by cosine similarity.
- Then follows the same choose/call/answer/check flow as ToolBench direct.
- `--retrieval_num` controls retries after selection/call/check failures; it does not change the fixed top-five embedding retrieval.

### RestBench

- Prompts the model to decompose each `query` into tool-use steps with IDs.
- Maps selected IDs to `tool_usage` strings from `tmdb_tool.json`.
- Writes `task_path` and `tool_choice_ls` to JSONL. This branch does not import external ToolBench tool code.

## Source-level caveats to preserve in wrappers

- The CLI default `--task funcqa_mh` does not match the dispatcher's accepted top-level `funcqa` task. Always pass `--task` explicitly.
- The ToolBench and ToolBench-retrieve branches call `answer_generation_direct(task)` when `tool_check` says no tool is needed, but the source function signature includes `model_name`. If that branch is reached, a `TypeError` is possible unless the source is patched or the workflow avoids the no-tool branch.
- Many model-output parsers use `eval` or `ast.literal_eval`; malformed JSON/Python-like text causes retry loops and can eventually return sentinel failures.
- Import-time `os.environ["OPENAI_API_KEY"]` means missing keys fail before the CLI can show help unless a dummy key is supplied for help-only checks.
- The code targets `openai==0.27.8`; newer OpenAI client APIs may break `openai.Embedding.create` and LangChain compatibility.
- Relative paths are hard-coded. Change the working directory or wrap file loading deliberately if embedding this code into another project.
