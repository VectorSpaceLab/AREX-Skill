# UltraRAG Pipeline DSL

## Purpose

Read this when you need to write, review, or debug a YAML pipeline.
It distills the verified step shapes and data-flow rules from `src/ultrarag/client.py`
and the example pipelines under `examples/`.

## Basic file shape

A pipeline file has two top-level keys:

```yaml
servers:
  benchmark: servers/benchmark
  retriever: servers/retriever
pipeline:
  - benchmark.get_data
  - retriever.retriever_init
  - retriever.retriever_search
```

`servers` maps server names to a server directory or path.
`pipeline` is the ordered list of steps.

## Step forms

### Plain step

```yaml
- retriever.retriever_search
```

### Step with input and output remapping

```yaml
- generation.generate:
    input:
      prompt_ls: prompt_ls
    output:
      ans_ls: final_answer_ls
```

### Loop

```yaml
- loop:
    times: 3
    steps:
      - retriever.retriever_search
      - generation.generate
```

### Branch

```yaml
- branch:
    router:
      - router.webnote_check_page
    branches:
      incomplete:
        - prompt.webnote_gen_subq
      complete: []
```

## Data-flow rules verified from source

- `build` reads the pipeline and generates merged `parameter/<name>_parameter.yaml`
  and `server/<name>_server.yaml` files.
- `run` loads those generated files unless a custom parameter file is supplied.
- `$param_name` values resolve from a server's `parameter.yaml`.
- Bare variable names resolve from the pipeline's shared variable pool.
- Memory fields use the `memory_*` naming convention and are tracked across steps.
- Branch-aware data is wrapped with `data` and `state` metadata.
- `loop` and `branch` behavior is implemented in the client; the YAML does not
  need a separate DSL extension for each example family.

## Output and remapping rules

- Tool outputs are JSON-serializable dicts.
- Prompt outputs usually become `prompt_ls`.
- Output remapping in the step-level `output:` block changes which variable name
  later steps see.
- `build` depends on the same input/output names that the server registered.
  Mismatched names are a common source of breakage.

## Minimal smoke example

The bundled `scripts/smoke_sayhello_pipeline.py` helper writes a temporary
pipeline equivalent to this shape after you pass `--repo-root <checkout>`:

```yaml
servers:
  sayhello: <checkout>/servers/sayhello
pipeline:
  - sayhello.greet
```

The `sayhello` server uses the `name` parameter from its parameter file and
returns `msg`. Let the helper generate the temp file so build artifacts stay out
of the checkout.

## Pattern reminders

- If a step is a dict with a single key that contains `.` the key is treated as
  `server.tool` with inline remapping.
- `show case` expects memory-case JSON or JSONL, not a pipeline YAML.
- `ultrarag build` is the right way to materialize generated server/parameter
  YAML before a later `run` or `PipelineCall`.
