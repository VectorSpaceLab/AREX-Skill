# Mellea `m` CLI reference

This reference describes Mellea `0.8.0.dev0`. The package exposes the console
entry point `m = cli.m:cli`. The CLI is a Typer application with five command
families:

```text
m serve
m alora {train|upload|add-readme}
m decompose run
m eval run
m fix genslots
```

Render the installed help before relying on flags. The bundled checker can do
that without invoking a command callback:

```bash
uv run python scripts/check_cli_surface.py --mode static
uv run python scripts/check_cli_surface.py --mode help --target root
uv run python scripts/check_cli_surface.py --mode help --target decompose-run
```

## Installation and lazy loading

Use the smallest extra that supplies the selected surface:

```bash
uv add "mellea[cli]"       # Typer and the m entry point
uv add "mellea[server]"    # FastAPI + Uvicorn + cli
uv add "mellea[hf]"        # Hugging Face/PEFT/TRL stack used by m alora
```

`server` includes `cli`. Provider-specific packages are separate from the CLI;
route their selection and credentials to `backends-and-models`. Command modules
delay heavy imports so `m --help` and nested help do not initialize a backend,
load a model, or start Uvicorn.

If `m` is absent after installation, use the environment's executable directly,
for example `uv run m --help`, and verify the package and entry point with the
bundled static check.

## Top-level safety table

| Command | Purpose | Side-effect boundary |
|---|---|---|
| `m serve` | Import an application and expose an OpenAI-shaped endpoint | Imports arbitrary top-level app code, binds a socket, and blocks |
| `m alora` | Train, upload, or document LoRA/aLoRA adapters | Model download, substantial compute, local mutation, prompts, and remote Hub writes |
| `m decompose` | Generate a dependency-aware Mellea program from a task | Multiple LLM calls and generated files |
| `m eval` | Generate candidate answers and score them with a judge | Generator and judge calls plus result files |
| `m fix` | Rewrite deprecated genslot API names | Recursive source mutation unless `--dry-run` |

Use help/static checks for discovery. Do not invoke any row above merely to test
whether installation succeeded.

## `m serve`

```text
m serve [SCRIPT_PATH] [--host TEXT] [--port INTEGER]
host default: 0.0.0.0
port default: 8080
```

Always provide an explicit script path. The illustrative default points to an
example path that may not exist in an installed distribution. The module must
define `serve`. Prefer a local bind:

```bash
uv run m serve app.py --host 127.0.0.1 --port 8080
```

There is no dry-run or daemon option. Starting the command executes app imports,
then starts a long-running process. Read [serving-api.md](serving-api.md) and
[deployment-and-config.md](deployment-and-config.md) first.

## `m decompose run`

Current surface:

```text
m decompose run --out-dir PATH
  [--out-name TEXT]
  [--input-file TEXT]
  [--model-id TEXT]
  [--backend ollama|openai]
  [--backend-req-timeout INTEGER]
  [--backend-endpoint TEXT]
  [--backend-api-key TEXT]
  [--version latest|v1|v2|v3]
  [--input-var TEXT]...
  [--log-mode demo|debug]
  [--enable-script-run|--no-enable-script-run]
```

Defaults are `out-name=m_decomp_result`,
`model-id=mistral-small3.2:latest`, `backend=ollama`, request timeout `300`,
`version=latest`, `log-mode=demo`, and script-run disabled. In this release,
`latest` resolves to template `v3`.

### Safe preparation

1. Create the output parent first; `--out-dir` must already be a directory.
2. Use `--input-file`, not the stale `--prompt-file` spelling found in some
   prose. Each non-empty line is one independent task job. Without a file, the
   CLI prompts for one line and converts literal `\n` sequences to newlines.
3. Choose a new `--out-name`. It must be 2-250 characters, start with an
   alphanumeric character, `_`, or `.`, and otherwise contain only letters,
   digits, `_`, `.`, `-`, and spaces.
4. Each repeated `--input-var` must be a valid, non-keyword Python identifier.
   Uppercase is conventional but not required by current validation. In
   interactive mode, the current command does not pass these names into the
   decomposition pipeline even though it still passes them to the output
   renderer; prefer file mode when external variables matter.
5. For `--backend openai`, both endpoint and API key are mandatory. Avoid putting
   the key in task files or committed shell scripts.

One job creates:

```text
<out-dir>/<out-name>/
├── <out-name>.json
├── <out-name>.py
└── validations/
    ├── __init__.py
    └── <generated-validator>.py
```

Multiple input lines create `<out-name>_1`, `<out-name>_2`, and so on. If a
later write fails, directories created by that invocation are removed before the
error is re-raised. The JSON contains `original_task_prompt`, `subtask_list`,
`identified_constraints`, and `subtasks`. Each subtask includes `subtask`, `tag`,
`constraints`, `prompt_template`, `general_instructions`,
`input_vars_required`, and `depends_on`.

The pipeline makes several model calls before it writes output. Review generated
Python and validators as untrusted generated code; executing the generated
program makes additional model calls. In `0.8.0.dev0`, the current `v3` template
hard-codes `mistral-small3.2:latest` in its generated `start_session()` call;
the `--model-id` and `--backend` used for decomposition are not reproduced as
the generated program's runtime route. The `--enable-script-run` value is passed
to the template renderer, but `v3` does not emit an argparse interface from it.
Inspect and edit the generated file instead of depending on either behavior.

The callable `cli.decompose.pipeline.decompose(...)` exposes structured
intermediate data for advanced use, but it is a CLI package path rather than the
stable `mellea.*` public namespace. Prefer the CLI unless that coupling is
acceptable.

## `m eval run`

```text
m eval run TEST_FILES...
  [--backend TEXT|-b TEXT]
  [--model TEXT]
  [--max-gen-tokens INTEGER]
  [--judge-backend TEXT|-jb TEXT]
  [--judge-model TEXT]
  [--max-judge-tokens INTEGER]
  [--output-path TEXT|-o TEXT]
  [--output-format TEXT]
  [--continue-on-error]
```

Defaults are generator backend `ollama`, generation and judge token caps `256`,
output path `eval_results`, output format `json`, and continue-on-error true.
The implementation recognizes backend names `ollama`, `openai`, `hf` or
`huggingface`, `watsonx`, and `litellm`. Backend choice, credentials, and model
compatibility belong to `backends-and-models`; judge methodology and score
interpretation belong to `sampling-and-evaluation`.

Input is parsed with a normal JSON parser even though help mentions JSONL. Use a
JSON object or JSON array whose items contain:

```json
{
  "id": "concise-answers",
  "source": "local",
  "name": "Concise answers",
  "instructions": "Score 1 only when the answer is correct and concise.",
  "examples": [
    {
      "input_id": "one",
      "input": [{"role": "user", "content": "What is 2 + 2?"}],
      "targets": [{"role": "assistant", "content": "4"}]
    }
  ]
}
```

Only the last user message in each example becomes generator input; assistant
targets become references. The judge backend defaults to the generator backend.
If `--judge-model` is omitted, current code chooses the package default model;
it does not necessarily reuse an explicitly supplied generator model.

`json` output contains a summary plus results. `jsonl` writes one test result per
line. A judge score of `1` passes; absent or unparseable scores fail as `0`.
Treat the result as qualitative evidence, not a deterministic test gate.

## `m fix genslots`

```text
m fix genslots PATH [--dry-run]
```

The command recursively scans Python files and performs line-based rewrites:

- `mellea.stdlib.components.genslot` to `.genstub`
- imported `genslot` module names to `genstub`
- `GenerativeSlot`, `SyncGenerativeSlot`, and `AsyncGenerativeSlot` to the
  corresponding `GenerativeStub` names

For a directory, it scans `*.py` recursively and skips `.git`, `.venv`,
`node_modules`, and `__pycache__`. An explicitly supplied single file is
processed regardless of suffix. Because matching is line-based rather than an
AST migration, review comments, strings, formatting, and syntax after rewriting:

```bash
uv run m fix genslots src --dry-run
# Review the listed lines and ensure version control or a backup exists.
uv run m fix genslots src
```

A missing path exits nonzero. Reapplying the migration should find no additional
matches, but idempotence does not replace diff review.

## Bounded `m alora` guidance

The entire group requires `mellea[hf]`. No aLoRA command is a safe probe.

### Train

```text
m alora train DATAFILE --basemodel TEXT --outfile TEXT
  [--promptfile TEXT] [--adapter alora|lora]
  [--device auto|cpu|cuda|mps]
  [--epochs 6] [--learning-rate 6e-6]
  [--batch-size 2] [--max-length 1024] [--grad-accum 4]
```

`DATAFILE` is JSONL with `item` and `label` fields. If supplied, `--promptfile`
is JSON containing `invocation_prompt`. Validate adapter and device values
before execution, use a small approved model and dataset for a bounded trial,
set explicit epochs/token length, estimate model-download and output size, and
use a new dedicated output parent. Current training cleanup may remove a
`README.md` in the parent directory of `--outfile`; never point it at a valuable
or shared directory. CPU is supported but can be impractically slow. GPU memory
failures require a smaller model, more memory, or an intentionally accepted CPU
run.

### Upload

```text
m alora upload WEIGHT_PATH --name OWNER/REPO
  [--intrinsic|--no-intrinsic] [--io-yaml PATH]
```

This creates or updates a private Hugging Face repository. `--intrinsic`
requires `io.yaml` and packages the adapter under an intrinsic/base-model/type
layout. Current intrinsic packaging copies `io.yaml` into `WEIGHT_PATH` and may
remove `README.md` there, so back up or stage a disposable copy before upload.
Confirm the account, target repository, privacy expectation, files, and remote
write approval first.

### Generate and upload README

```text
m alora add-readme DATAFILE --basemodel TEXT --name OWNER/REPO
  [--promptfile TEXT] [--hints TEXT] [--io-yaml TEXT]
```

This calls the default Mellea session, prints generated documentation, asks
`yes`/`no`, and then creates or updates a private Hub repository. There are no
CLI flags for selecting the README-generation backend. The accepted `--io-yaml`
value is not used by the current command. It is interactive and remote-write
capable; do not run it unattended or as a local documentation preview.
