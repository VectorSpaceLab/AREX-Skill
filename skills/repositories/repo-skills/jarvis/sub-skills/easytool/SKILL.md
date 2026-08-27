---
name: easytool
description: "Operate and troubleshoot EasyTool tool-instruction workflows for
  FuncQA, ToolBench, ToolBench retrieval, and RestBench."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# EasyTool

Use this sub-skill when a user asks to run, adapt, or debug EasyTool's concise tool-instruction workflows for FuncQA, ToolBench, ToolBench retrieval, RestBench, data preparation, CLI options, module signatures, API-key handling, progress/resume files, or the ToolBench external tool code layout.

Do not use this sub-skill for TaskBench benchmark construction/evaluation; route that work to the TaskBench owner. Do not use it for HuggingGPT chat execution; route chat-agent work to the HuggingGPT chat owner. Do not start real dataset downloads, OpenAI calls, RapidAPI calls, or external tool execution unless the user explicitly approves the credentials/network side effects.

## Start here

1. Confirm the user has an EasyTool checkout and an environment with EasyTool requirements installed.
2. Run the safe checker before any real workflow:

   ```bash
   python scripts/easytool_cli_check.py --repo-root "$REPO_ROOT"
   ```

   The checker only verifies files and `main.py --help`; it sets a dummy OpenAI key for help parsing when needed and applies the local `util` import workaround.
3. For commands, task/data_type combinations, and progress files, read [references/cli-reference.md](references/cli-reference.md).
4. For end-to-end preparation and execution flows, read [references/workflows.md](references/workflows.md).
5. For data/test/tool layout expectations, read [references/data-formats.md](references/data-formats.md).
6. For callable module signatures and source-level caveats, read [references/api-reference.md](references/api-reference.md).
7. For import failures, missing keys, missing ToolBench tools, resume confusion, parsing retries, or download problems, read [references/troubleshooting.md](references/troubleshooting.md).

## Operating rules

- Run EasyTool commands from the checkout's `easytool/` directory so relative data paths resolve.
- Add the inner package directory to `PYTHONPATH` before importing or running `main.py`; several modules use absolute `from util import *` imports.
- `OPENAI_API_KEY` is required even for importing `main.py` unless a dummy value is supplied for help-only checks. Real workflows require a real key.
- `RAPIDAPI_KEY` is only required when ToolBench executes external API tool code. It does not replace the OpenAI key used for chat/embedding calls.
- Treat `data_process.py` as a network/data mutation step: it downloads and extracts benchmark test data. Do not run it silently.
- ToolBench real execution requires separately obtained `toolenv/tools` code with each tool's `api.py`; EasyTool's repository does not bundle that tree.
- Progress text files are read from the current working directory and output JSONL files are append-only. Use clean run directories or reconcile progress before resuming.

## Evidence distilled

This sub-skill is distilled from source evidence named `easytool/README.md`, `easytool/main.py`, `easytool/requirements.txt`, `easytool/data_process.py`, `easytool/easytool/util.py`, `easytool/easytool/funcQA.py`, `easytool/easytool/toolbench.py`, `easytool/easytool/toolbench_retrieve.py`, `easytool/easytool/restbench.py`, and the `easytool/data_*` schema files. These names are provenance only; runtime guidance is self-contained in this sub-skill.
