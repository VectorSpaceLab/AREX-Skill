# EasyTool Troubleshooting

Start with the safe checker whenever the symptom involves import, CLI help, missing files, or task/data layout:

```bash
python scripts/easytool_cli_check.py --repo-root "$REPO_ROOT"
```

The checker does not perform downloads, OpenAI calls, RapidAPI calls, or ToolBench tool execution.

## Common failures and fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'util'` when running `main.py` or importing `funcQA`, `toolbench`, or `toolbench_retrieve` | Internal modules use absolute `from util import *`; the inner `easytool/easytool` directory is not on `PYTHONPATH`. | Run from `easytool/` and set `PYTHONPATH="$PWD/easytool${PYTHONPATH:+:$PYTHONPATH}"`, or use the bundled checker to verify the workaround. |
| `KeyError: 'OPENAI_API_KEY'` during import or `main.py --help` | Module top levels read `os.environ["OPENAI_API_KEY"]`. | For help-only checks, set a dummy value or use the checker. For real runs, export a valid `OPENAI_API_KEY`; do not print or log it. |
| OpenAI authentication/model errors during execution | Dummy key, expired key, unsupported `--model_name`, incompatible `openai`/`langchain` versions, or no access to embeddings for retrieve. | Use a real key, keep package versions aligned with `openai==0.27.8` and `langchain==0.0.260`, verify the chosen chat model, and for `toolbench_retrieve` verify embedding access. |
| `KeyError: 'RAPIDAPI_KEY'` in ToolBench `Call_function` | Real ToolBench tool code was reached and the environment lacks `RAPIDAPI_KEY`. | Export `RAPIDAPI_KEY` only for approved real ToolBench calls. Remember that this key does not satisfy OpenAI chat/embedding calls. |
| ToolBench retrieve fails before external tool calls | Missing OpenAI key/model access, missing `API_description_embeddings.pkl`, or malformed local embedding pickle. | Extract the local zip to create `API_description_embeddings.pkl`; then verify OpenAI chat and embedding credentials separately from `toolenv/tools`. |
| ToolBench direct/retrieve repeatedly returns blank call results or prints retry messages | `toolenv/tools` is absent, `--tool_root_dir` points to the wrong layout, selected standardized tool directory is missing, selected `api.py` lacks the normalized function, or RapidAPI call failed. | Confirm external tool code is present under the path passed to `--tool_root_dir`; ensure each selected tool directory contains `api.py`; inspect `wrong_log.json` for parameter/function errors. |
| `FileNotFoundError` for `data_funcqa/test_data/...`, `data_restbench/test_data/tmdb.json`, or `data_toolbench/test_data/...` | `data_process.py` has not been run, failed, or was run from the wrong directory. | With user approval for network/data mutation, run `python data_process.py` from `easytool/`; verify generated files; clean partial temp files after interruptions. |
| `FileNotFoundError` for `API_description_embeddings.pkl` | The zip is present but not extracted; `toolbench_retrieve.py` opens the `.pkl` directly. | Run `python -m zipfile -e data_toolbench/tool_instruction/API_description_embeddings.zip data_toolbench/tool_instruction/` from `easytool/`. |
| `Wrong task name` | The CLI dispatch accepts `funcqa`, `toolbench`, `toolbench_retrieve`, or `restbench`; the default `funcqa_mh` is not a valid `--task`. | Pass `--task funcqa --data_type funcqa_mh` or another valid combination. |
| Local variable or missing test data errors for ToolBench | `--data_type` was not `G2` or `G3`; the dispatcher only sets `test_data` for those values. | Use `--data_type G2` or `--data_type G3`. |
| Progress resumes from the wrong index | Stale progress file in current working directory; regular ToolBench and retrieve share `<data_type>_<model>_Easytool.txt`; output JSONL is append-only. | Compare progress integer with JSONL rows, then move/remove/edit the progress file deliberately. Use separate directories for direct and retrieve runs. |
| Duplicate rows after crash/retry | JSONL write and progress update are separate operations; a crash can happen between them. | Deduplicate the last JSONL row or advance the progress file after checking the last completed item. |
| `TypeError` around `answer_generation_direct()` in ToolBench | Source branch calls `answer_generation_direct(task)` without `model_name` when the model says no external tool is needed. | Patch the call locally to include `model_name`, or avoid relying on no-tool branches in production runs until patched. Record the patch in run notes outside runtime skill files. |
| Repeated `choose tool fails`, `Choose Parameter fails`, `task decompose fails`, `answer generation fails`, or `****Try Again****` | Model output was not parseable by the source's `eval`/`ast.literal_eval` expectations, API call results were blank, or answer checks rejected the response. | Lower cost/risk by running a tiny slice first; inspect stdout and JSONL `answer_wrong`; consider stricter prompts or a patched parser if repeated parse failures occur. |
| Download hangs or fails in data preparation | `data_process.py` uses Google Drive downloads and `wget`; network, quota, proxy, or URL availability may fail. | Do not retry indefinitely. Confirm network permission, clean partial temp files/extraction directories, then rerun or provide files manually in the expected layout. |

## Separating ToolBench missing-tool-code from missing credentials

ToolBench has three independent prerequisite groups:

1. OpenAI chat/model calls: required by both `toolbench` and `toolbench_retrieve` before any tool code can succeed.
2. Retrieval embeddings: required only by `toolbench_retrieve`, through `openai.Embedding.create` and the local `API_description_embeddings.pkl` file.
3. External API tool code and RapidAPI: required only when a selected ToolBench API function is actually imported and called from `toolenv/tools`.

If a user lacks `toolenv/tools` and `RAPIDAPI_KEY`, do not diagnose it as an embedding problem. If a user lacks `OPENAI_API_KEY`, do not diagnose it as missing `toolenv/tools`. The safe checker can validate the import workaround and source files, but it cannot prove real OpenAI/RapidAPI execution.

## Progress-file names and resume safety

- FuncQA progress: `FuncQA_<data_type>_<model>_Easytool.txt`; output uses lowercase `easytool` in the JSONL filename.
- RestBench progress: `restbench_<model>_Easytool.txt`.
- ToolBench direct and retrieve progress: `<data_type>_<model>_Easytool.txt`, shared across both workflows.
- ToolBench direct output: `<data_type>_<model>_Easytool.jsonl`.
- ToolBench retrieve output: `<data_type>_<model>_retrieve_Easytool.jsonl`.

Before changing `--model_name`, `--data_type`, or `--task`, archive old progress/output files or move to a clean working directory.

## Data preparation side effects

`data_process.py` may create directories, download files, extract zips, remove temporary files, and mutate ToolBench generated test JSON by adding `Tool_dic`. In automated contexts, ask before running it and prefer preflight checks first. If the user provides data manually, validate filenames and minimum keys instead of running downloads.

## Credential handling

- Never echo real `OPENAI_API_KEY` or `RAPIDAPI_KEY` values.
- Use a dummy OpenAI key only for help/import checks.
- Treat `toolenv/tools` as executable third-party code; review or sandbox before real RapidAPI calls if the user cares about safety.
