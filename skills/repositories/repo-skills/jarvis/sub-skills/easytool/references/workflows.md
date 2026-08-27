# EasyTool Workflows

Use these workflows to plan or troubleshoot EasyTool runs without reopening the original repository documentation. Commands assume the user has set `REPO_ROOT` to the checkout root and is allowed to run the stated network/API side effects.

## 1. Preflight without network/API calls

1. Check files and CLI importability:

   ```bash
   python scripts/easytool_cli_check.py --repo-root "$REPO_ROOT"
   ```

2. If the checker reports a nonzero help return code, fix dependency/import issues before preparing data or calling APIs.
3. If the checker reports missing generated data, decide whether the user wants to download benchmark data now. Do not run `data_process.py` automatically in a no-network or no-mutation context.
4. If the target is ToolBench or ToolBench retrieve, separately confirm the external `toolenv/tools` code and `RAPIDAPI_KEY` status. Missing ToolBench tool code is different from missing OpenAI credentials.

## 2. Prepare benchmark data

`data_process.py` is a networked data-construction script. It creates `test_data/` directories and downloads/extracts test files:

- FuncQA: downloads a zip, extracts `funcqa_oh.json` and `funcqa_mh.json` into `data_funcqa/test_data/`.
- RestBench: downloads `tmdb.json` into `data_restbench/test_data/` using a shell `wget` command.
- ToolBench: downloads a zip, extracts `G2_category.json` and `G3_instruction.json` into `data_toolbench/test_data/`, then mutates those JSON files by adding a compact `Tool_dic` list per test item from `toolbench_tool_instruction.json`.

Run only after approval for network and data mutation:

```bash
cd "$REPO_ROOT/easytool"
python data_process.py
```

After preparation, verify the expected generated files exist:

```bash
test -f data_funcqa/test_data/funcqa_mh.json
test -f data_funcqa/test_data/funcqa_oh.json
test -f data_restbench/test_data/tmdb.json
test -f data_toolbench/test_data/G2_category.json
test -f data_toolbench/test_data/G3_instruction.json
```

For ToolBench retrieval, extract the bundled embeddings pickle from the local zip if it is not present:

```bash
cd "$REPO_ROOT/easytool"
python -m zipfile -e data_toolbench/tool_instruction/API_description_embeddings.zip data_toolbench/tool_instruction/
test -f data_toolbench/tool_instruction/API_description_embeddings.pkl
```

If `data_process.py` is interrupted, inspect and clean partial `data/` extraction directories or incomplete temp zip files before rerunning.

## 3. FuncQA execution

FuncQA uses bundled mathematical functions from `data_funcqa/funchub/math.py`; it does not require RapidAPI or ToolBench external tool code.

Checklist:

- Requirements installed.
- `OPENAI_API_KEY` set for real model calls.
- `data_funcqa/tool_instruction/functions_data.json` and `tool_dic.jsonl` present.
- `data_funcqa/test_data/funcqa_mh.json` or `funcqa_oh.json` present.
- Working directory is `easytool/` and `PYTHONPATH` includes `easytool/easytool`.

Run one workflow per clean output directory or reconcile progress files first:

```bash
cd "$REPO_ROOT/easytool"
export PYTHONPATH="$PWD/easytool${PYTHONPATH:+:$PYTHONPATH}"
export OPENAI_API_KEY="..."
python main.py --task funcqa --data_type funcqa_mh --model_name gpt-3.5-turbo
```

Multi-hop (`funcqa_mh`) asks the model to decompose the question and infer task topology before retrieval/calling. One-hop (`funcqa_oh`) treats the original question as the single subtask.

## 4. RestBench execution

RestBench in this source selects/decomposes tool-use paths from `tmdb_tool.json` and writes selected tool usages; it does not import ToolBench `api.py` files or require `RAPIDAPI_KEY`.

Checklist:

- Requirements installed.
- `OPENAI_API_KEY` set.
- `data_restbench/tool_instruction/tmdb_tool.json` present.
- `data_restbench/test_data/tmdb.json` present.
- Working directory and `PYTHONPATH` set as above.

Run:

```bash
cd "$REPO_ROOT/easytool"
export PYTHONPATH="$PWD/easytool${PYTHONPATH:+:$PYTHONPATH}"
export OPENAI_API_KEY="..."
python main.py --task restbench --model_name gpt-3.5-turbo
```

The `--data_type` value is ignored by the RestBench branch.

## 5. ToolBench direct execution

ToolBench direct uses the compact `Tool_dic` field already added to each generated test item by `data_process.py`. It can call external ToolBench `api.py` files.

Checklist:

- Requirements installed.
- `OPENAI_API_KEY` set for chat/model calls.
- `RAPIDAPI_KEY` set if real external API calls may be reached.
- `data_toolbench/tool_instruction/toolbench_tool_instruction.json` present.
- `data_toolbench/test_data/G2_category.json` or `G3_instruction.json` present and already processed with `Tool_dic` fields.
- External `toolenv/tools` tree present and passed with `--tool_root_dir`.
- Working directory and `PYTHONPATH` set.

Run:

```bash
cd "$REPO_ROOT/easytool"
export PYTHONPATH="$PWD/easytool${PYTHONPATH:+:$PYTHONPATH}"
export OPENAI_API_KEY="..."
export RAPIDAPI_KEY="..."
python main.py --task toolbench --data_type G2 --tool_root_dir ./toolenv/tools
```

`build_index` scans every directory under `--tool_root_dir`. At call time, EasyTool looks for a directory whose name matches the selected tool's standardized name and imports `<that-tool>/api.py`; the selected API function is called with normalized parameter names plus `toolbench_rapidapi_key`.

## 6. ToolBench retrieve execution

ToolBench retrieve combines an embedding retrieval step with ToolBench external tool execution.

Additional checklist beyond ToolBench direct:

- `data_toolbench/tool_instruction/API_description_embeddings.pkl` exists; extract it from the local zip if necessary.
- `OPENAI_API_KEY` has access to the embedding endpoint used by `openai.Embedding.create(engine="text-embedding-ada-002", ...)`.

Run:

```bash
cd "$REPO_ROOT/easytool"
export PYTHONPATH="$PWD/easytool${PYTHONPATH:+:$PYTHONPATH}"
export OPENAI_API_KEY="..."
export RAPIDAPI_KEY="..."
python main.py --task toolbench_retrieve --data_type G3 --tool_root_dir ./toolenv/tools
```

Important distinction: missing `toolenv/tools` prevents actual selected API code from running; missing or invalid `OPENAI_API_KEY` prevents both chat prompts and retrieval embeddings. A valid `RAPIDAPI_KEY` alone cannot make retrieval work.

## 7. Resume and clean-run procedure

Every workflow computes `start_index` from a progress text file in the current working directory. The progress file stores the next test index as plain text. Output JSONL files are append-only.

Before resuming:

1. Identify the expected progress filename in [cli-reference.md](cli-reference.md).
2. Inspect the text file value and compare it with the number of already accepted JSONL rows.
3. If the previous run crashed after writing a JSONL row but before updating progress, rerunning may duplicate that item; remove the duplicate row or advance the progress file deliberately.
4. If the progress file is stale or belongs to another workflow/model, move it aside before starting a clean run.
5. For ToolBench, do not mix `toolbench` and `toolbench_retrieve` in the same directory with the same data type/model unless you intend them to share the same progress file.

## 8. Safe adaptation guidelines

- For smoke checks, prefer `main.py --help`, schema validation, or tiny local fixture checks. Do not call OpenAI or RapidAPI in automated preflight.
- For real runs, start with a small manually sliced copy of a generated test file if the user wants bounded cost. The source CLI has no native `--limit` option.
- Keep API keys in the environment; do not put them in commands, logs, JSONL outputs, or shared notebooks.
- Expect LLM-output parsing retries. The source uses `eval`/`ast.literal_eval` on model responses and can retry many times before returning sentinel values.
