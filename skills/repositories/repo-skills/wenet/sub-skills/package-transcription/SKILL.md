---
name: package-transcription
description: "Use WeNet as an installed Python package or console CLI for speech
  transcription, model loading, model-directory checks, and safe backend
  selection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# WeNet Package Transcription

Use this sub-skill when the task is to transcribe audio with the installed
`wenet` package, load a pretrained or local WeNet model from Python, validate a
local model directory, or diagnose the user-facing package CLI.

## Start here

1. Confirm the package imports before planning any download or inference:

   ```bash
   python - <<'PY'
   import wenet
   from wenet import load_model, load_feature, load_tokenizer
   print("WeNet package import OK")
   PY
   ```

2. For CLI tasks, inspect the installed console entry point:

   ```bash
   wenet --help
   ```

3. For local model directories, run the bundled checker before loading the
   model:

   ```bash
   python sub-skills/package-transcription/scripts/check_wenet_package.py \
     --model-dir /path/to/model_dir --device cpu
   ```

## Route by task

- Read [references/api-reference.md](references/api-reference.md) when the user
  asks for Python usage, model loading, model directory contents, feature or
  tokenizer loading, built-in model names, or return-object expectations.
- Read [references/cli-reference.md](references/cli-reference.md) when the user
  asks for the `wenet` command, CLI flags, alignment, context biasing, device
  selection, or punctuation options.
- Run [scripts/check_wenet_package.py](scripts/check_wenet_package.py) for safe
  import checks, backend availability checks, and local model-directory
  preflight validation. The script does not download models or transcribe audio.
- Read [references/troubleshooting.md](references/troubleshooting.md) when
  imports fail, model loading downloads unexpectedly, a model directory is
  incomplete, `--device cuda`/`--device npu` fails, or audio/alignment/context
  options behave unexpectedly.

## Key decisions

- Use the installed package API (`import wenet`) for simple transcription and
  model loading. Do not rely on source-checkout scripts for package tasks.
- Built-in model names may trigger a network download through the model hub.
  Validate network and storage constraints before calling `load_model()` with a
  built-in name.
- A local model directory must contain `train.yaml`, `final.pt`, and
  `units.txt`; `global_cmvn` is optional and used when present.
- `device="cpu"` is the safest default. `device="cuda"` and `device="npu"`
  require matching framework/runtime support in the user's environment; the CLI
  accepting the flag does not prove the backend exists.
- Route batch/offline decoding of a trained experiment to
  [../training-and-decoding/SKILL.md](../training-and-decoding/SKILL.md), and
  route export/deployment artifacts to
  [../model-export/SKILL.md](../model-export/SKILL.md).
