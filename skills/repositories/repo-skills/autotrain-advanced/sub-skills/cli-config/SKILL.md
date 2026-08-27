---
name: cli-config
description: "Operate AutoTrain Advanced top-level CLI, setup command, config
  parser, and task routing."
disable-model-invocation: true
metadata:
  disco-role: operating
  parent-skill: autotrain-advanced
license: Apache 2.0
---

# AutoTrain CLI and config routing

Use this sub-skill for command discovery, package-level checks, `autotrain --config`, `autotrain setup`, and deciding which task-specific sub-skill should own a request.

## Safe entry points

- `autotrain --help`
- `autotrain --version`
- `autotrain <subcommand> --help`
- `autotrain --config path/to/config.yml`
- `autotrain setup --help`

Bundled helpers from the root skill:

- `../../scripts/check_install.py` — import/version check.
- `../../scripts/inspect_cli.py` — run CLI help through the current interpreter.
- `../../scripts/validate_config.py` — parse a YAML config without launching training.

## Routing rules

1. Start with the top-level help or config parser if the user is not sure which task family they need.
2. If the request is `autotrain --config`, validate the file first, then route by parsed `task` and `backend`.
3. If the task is LLM-like (`llm`, YAML aliases such as `llm-sft`/`llm-dpo`, or app/API keys such as `llm:sft`/`llm:dpo`), go to `../llm-training/`.
4. If the task is text, token, seq2seq, extractive QA, sentence-transformers, or tabular, go to `../text-and-tabular/`.
5. If the task is image classification/regression, object detection, or VLM, go to `../vision-multimodal/`.
6. If the user asks about `app`, `api`, `spacerunner`, jobs, logs, or hosted backends, go to `../app-backends/`.
7. If the user asks about `autotrain tools`, go to `../model-tools/`.

Important exception: VLM is supported in the task registry/app/config path but is not a registered top-level `autotrain vlm` command in this checkout.

## Config workflow

For a YAML config:

```bash
python skills/disco/autotrain-advanced/scripts/validate_config.py path/to/config.yml
```

Then check:

- `task`: the owning trainer family.
- `backend`: `local`, `local-cli`, `local-ui`, `spaces-*`, `ep-*`, `ngc-*`, or `nvcf-*`.
- `params`: task-specific fields and column mappings.

Do not call `AutoTrainConfigParser(...).run()` until the user explicitly wants to launch a job.

## Setup command caution

`autotrain setup` is not a passive inspection command. It mutates the environment by changing `xformers`; with `--update-torch` it installs CUDA 12.1 PyTorch wheels. Use it only when the user explicitly wants this environment change.

## References

- `references/workflows.md` — CLI inventory and config decision flow.
- `references/troubleshooting.md` — invalid subcommands, parser errors, and setup/environment problems.
