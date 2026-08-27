# EasyTool CLI Reference

EasyTool is operated as scripts, not as an installed console entry point. Use an environment with these requirements installed: `openai==0.27.8`, `langchain==0.0.260`, `gdown==4.6.0`, `tqdm`, `argparse`, `numpy`, `requests`, `pickle-mixin`, and `scikit-learn`.

## Safe help/import check

From the sub-skill directory, use the bundled checker:

```bash
python scripts/easytool_cli_check.py --repo-root "$REPO_ROOT"
```

Manual equivalent for a help-only check:

```bash
cd "$REPO_ROOT/easytool"
export PYTHONPATH="$PWD/easytool${PYTHONPATH:+:$PYTHONPATH}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-sk-dummy-for-help-only}"
python main.py --help
```

The dummy key is only safe for parsing `--help`; real inference, embeddings, and model calls require a valid `OPENAI_API_KEY`.

## CLI options

`main.py` defines these argparse options:

| Option | Default | Meaning and caveats |
| --- | --- | --- |
| `--model_name` | `gpt-3.5-turbo` | Passed to LangChain `ChatOpenAI` calls. Keep it compatible with the installed `openai`/`langchain` versions. |
| `--task` | `funcqa_mh` | Dispatch key. Valid top-level values in the source dispatcher are `funcqa`, `toolbench`, `toolbench_retrieve`, and `restbench`. The default string is not itself accepted by the dispatcher, so pass `--task` explicitly. |
| `--data_type` | `G3` | Dataset selector. Use `funcqa_mh` or `funcqa_oh` with `--task funcqa`; use `G2` or `G3` with `toolbench` and `toolbench_retrieve`; ignored by `restbench`. Invalid ToolBench data types can leave `test_data` unset. |
| `--tool_root_dir` | `.toolenv/tools/` | Base directory for external ToolBench tool code. The README command examples use `./toolenv/tools`; pass an explicit path instead of relying on the default. Not used by FuncQA or RestBench. |
| `--retrieval_num` | `5` | Retry/attempt count inside task execution loops after failed tool selection/call/answer checks. In `toolbench_retrieve`, the embedding top-k is fixed at 5 in source; this option still controls retry attempts. |

## Valid task/data_type combinations

| Workflow | Command selector | Required `data_type` | Required local data | Keys | Progress file | Output JSONL |
| --- | --- | --- | --- | --- | --- | --- |
| FuncQA multi-hop | `--task funcqa` | `funcqa_mh` | `data_funcqa/tool_instruction/functions_data.json`, `data_funcqa/tool_instruction/tool_dic.jsonl`, `data_funcqa/funchub/math.py`, `data_funcqa/test_data/funcqa_mh.json` | `OPENAI_API_KEY` | `FuncQA_funcqa_mh_<model>_Easytool.txt` | `FuncQA_funcqa_mh_<model>_easytool.jsonl` |
| FuncQA one-hop | `--task funcqa` | `funcqa_oh` | same as FuncQA plus `data_funcqa/test_data/funcqa_oh.json` | `OPENAI_API_KEY` | `FuncQA_funcqa_oh_<model>_Easytool.txt` | `FuncQA_funcqa_oh_<model>_easytool.jsonl` |
| RestBench | `--task restbench` | ignored | `data_restbench/tool_instruction/tmdb_tool.json`, `data_restbench/test_data/tmdb.json` | `OPENAI_API_KEY` | `restbench_<model>_Easytool.txt` | `restbench_<model>_Easytool.jsonl` |
| ToolBench direct | `--task toolbench` | `G2` or `G3` | `data_toolbench/tool_instruction/toolbench_tool_instruction.json`, `data_toolbench/test_data/G2_category.json` or `G3_instruction.json`, external `toolenv/tools` tree | `OPENAI_API_KEY`, `RAPIDAPI_KEY` for real calls | `<G2-or-G3>_<model>_Easytool.txt` | `<G2-or-G3>_<model>_Easytool.jsonl` |
| ToolBench retrieve | `--task toolbench_retrieve` | `G2` or `G3` | same ToolBench data plus extracted `data_toolbench/tool_instruction/API_description_embeddings.pkl` | `OPENAI_API_KEY`; `RAPIDAPI_KEY` only once external tool code is called | `<G2-or-G3>_<model>_Easytool.txt` | `<G2-or-G3>_<model>_retrieve_Easytool.jsonl` |

The regular and retrieve ToolBench workflows share the same progress filename for the same `data_type` and `model_name`. Run them in separate working directories or reset/reconcile the progress file before switching workflows.

## Command templates

Always run from the `easytool/` directory inside the checkout:

```bash
cd "$REPO_ROOT/easytool"
export PYTHONPATH="$PWD/easytool${PYTHONPATH:+:$PYTHONPATH}"
export OPENAI_API_KEY="..."     # required for real model calls
```

FuncQA:

```bash
python main.py --model_name gpt-3.5-turbo --task funcqa --data_type funcqa_mh
python main.py --model_name gpt-3.5-turbo --task funcqa --data_type funcqa_oh
```

RestBench:

```bash
python main.py --model_name gpt-3.5-turbo --task restbench
```

ToolBench direct:

```bash
export RAPIDAPI_KEY="..."
python main.py \
  --model_name gpt-3.5-turbo \
  --task toolbench \
  --data_type G2 \
  --tool_root_dir ./toolenv/tools
```

ToolBench retrieve:

```bash
export RAPIDAPI_KEY="..."  # needed only if selected tool code performs real RapidAPI calls
python main.py \
  --model_name gpt-3.5-turbo \
  --task toolbench_retrieve \
  --data_type G3 \
  --tool_root_dir ./toolenv/tools
```

## Side-effect summary

- `main.py --help` imports EasyTool modules but should not call networks or external APIs.
- Real `main.py` execution calls OpenAI chat APIs for decomposition, selection, parameter generation, answer generation, and checks.
- `toolbench_retrieve` additionally calls the OpenAI embedding API for each retrieval query.
- ToolBench external tool calls may import and execute arbitrary `api.py` files under `toolenv/tools` and pass `RAPIDAPI_KEY` into them.
- Results are appended to JSONL files in the current working directory; progress text files are overwritten with the next start index.
