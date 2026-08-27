# Troubleshooting Pipelines and Workflows

Use this reference when a txtai pipeline/workflow does not run, runs but produces unexpected shapes, or fails while resolving YAML configuration.

## Workflow Appears To Do Nothing

Symptoms:

- No output, no printed logs, no indexing side effects, and no exception.
- `workflow(elements)` was assigned to a variable but not iterated.

Cause:

- `Workflow.__call__` returns a lazy generator. Execution starts only when the generator is consumed.

Fix:

```python
# Force execution and keep results
results = list(workflow(elements))

# Stream execution
for result in workflow(elements):
    print(result)

# Force execution while discarding outputs
for _ in workflow(elements):
    pass
```

If the workflow uses `index`/`upsert` finalizers, failing to consume the generator also prevents the final indexing flush.

## Optional Pipeline Extras Missing

Symptoms:

- `ImportError` mentions a pipeline, workflow task, model backend, parser, audio library, Pillow, `croniter`, `requests`, `xmltodict`, `pandas`, or `openpyxl`.
- A task class reports it is unavailable and suggests an extra.

Fix by choosing the focused extra:

```bash
python -m pip install 'txtai[workflow]'
python -m pip install 'txtai[pipeline-data]'
python -m pip install 'txtai[pipeline-text]'
python -m pip install 'txtai[pipeline-audio]'
python -m pip install 'txtai[pipeline-image]'
python -m pip install 'txtai[pipeline-llm]'
python -m pip install 'txtai[pipeline-train]'
```

Avoid `txtai[all]` unless the user explicitly needs every optional family; it is broad and can pull heavyweight dependencies.

## Model Downloads or Offline Failures

Symptoms:

- Workflow construction hangs or fails while downloading a model.
- Errors mention Hugging Face Hub, local cache, authorization, SSL, proxy, or missing model files.
- Default `Summary`, `Translation`, `Transcription`, `Caption`, `Questions`, `LLM`, or other model-backed pipelines fail in offline mode.

Fix:

- Use explicit `path` values that are already cached or locally available.
- For validation, replace model-backed pipelines with pure Python callables or `Nop` until the workflow wiring is proven.
- Keep no-download smoke tests separate from model acceptance tests.
- For hosted/LiteLLM or llama.cpp backends, route backend credential/model details to [agents-and-llm-orchestration](../../agents-and-llm-orchestration/SKILL.md).
- For GPU-only expectations, confirm `torch.cuda.is_available()` and installed backend packages before assuming acceleration.

## YAML Action Does Not Resolve

Symptoms:

- `KeyError` or resolver/import errors during `Application(config)` creation.
- `action: summary` or `action: translation` fails because no corresponding pipeline section exists.
- A custom callable path cannot be imported.

Resolution checklist:

1. If `action` should be a pipeline, define it as a top-level YAML section:

   ```yaml
   summary:

   workflow:
     run:
       tasks:
         - action: summary
   ```

2. If `action` should be a Python function/class, use a fully qualified import path visible on `PYTHONPATH`, such as `mypackage.transforms.clean`.
3. If `action` should be a configured workflow, define that workflow name before using it as an action in another workflow.
4. If using `index`, `upsert`, `search`, or `transform`, ensure the YAML has a valid `embeddings` section and route detailed embeddings setup to [embeddings-search](../../embeddings-search/SKILL.md).
5. Do not use absolute checkout paths in reusable YAML; package the callable in importable code or keep the workflow in Python.

## Args Passed In The Wrong Order

Symptoms:

- A callable receives a language/model/limit argument as data, or receives the data list in the wrong position.
- Multi-action YAML tasks apply the wrong `args` to an action.

Facts:

- Task actions receive workflow data first.
- YAML `args` are appended after the incoming workflow data for normal tasks.
- For multi-action tasks, `args` is indexed per action.

Example:

```yaml
translation:

workflow:
  fr:
    tasks:
      - action: translation
        args: [fr]
```

Equivalent callable shape: `translation(inputs, "fr")`.

## File Selector Regex Skips Inputs

Symptoms:

- Some files pass through unchanged.
- `FileTask` or `ImageTask` does not process files expected to match.

Checklist:

- `FileTask` only accepts existing local files or `file://` URLs pointing to existing local files.
- `select` is a regex applied to the lower-cased path after removing `file://`.
- Escape backslashes correctly in YAML: `select: "\\.wav$"`, `select: "\\.pdf$"`, or `select: "\\.(jpg|jpeg|png)$"`.
- `ImageTask` only accepts image file extensions and requires Pillow.
- `RetrieveTask` is needed before file-only tasks when the input is a remote URL.

## Unexpected Tuple/List Shapes

Symptoms:

- A downstream task receives only tuple column `1` instead of the full tuple.
- Multi-action task returns tuples when a flattened list was expected.
- A segmentation/chunking step expands one input into many rows.

Facts and fixes:

- `Task` unpacks `(id, data, tags)` tuples by default, processes `data`, then repacks into the original tuple shape.
- Set `unpack=False` to pass whole tuples through, especially before custom indexing sinks.
- Use `column=0`, `column=1`, or a per-action map such as `column={0: 0, 1: 1}` for tuple-column extraction.
- Multi-action merge modes are `hstack` for tuple rows, `vstack` for row-wise flattening, `concat` for string joining, and `None` for separate action outputs.
- Set `onetomany=False` when a list output should remain a single row rather than expand.

## Batching or Streaming Surprises

Symptoms:

- A callable expects one item but receives a list.
- Memory grows on large inputs.
- A stream action expands inputs unexpectedly.

Fix:

- Write generic `Task` actions to accept a list/batch and return a list.
- Reduce `Workflow(batch=...)` for memory-heavy model pipelines.
- Use a custom `Task` subclass or wrap the callable if it only accepts single elements.
- Remember `stream` processors run before batching and can expand elements.
- For YAML stream tasks, set `batch: true` when the stream action expects the full iterable.

## Schedule Fails Or Never Runs

Symptoms:

- `ImportError: Workflow scheduling is not available`.
- YAML schedule starts but the process exits immediately.
- Cron expression is rejected or runs at the wrong frequency.

Fix:

- Install `txtai[workflow]` for `croniter`.
- Use valid five-field or six-field cron expressions. Six fields include seconds.
- In YAML applications, call `app.wait()` when the process should stay alive for scheduled workflows.
- Provide `schedule.elements`; schedules repeatedly run the workflow over those elements.
- Use `iterations` during tests so the schedule terminates.
- Scheduled workflow exceptions are logged and the schedule continues; inspect logs for the original failure.

## Service, Retrieve, Audio, Image, and Training Are Too Heavy

Symptoms:

- Smoke tests hang on network, audio devices, GPU/model downloads, or cloud/storage access.
- CI lacks hardware or credentials.

Fix:

- Keep deterministic smoke tests pure Python; use `scripts/workflow_smoke.py --mode all` first.
- Treat `ServiceTask`, `RetrieveTask` remote URLs, audio streams/microphone, object detection, transcription, LLMs, and training/export as integration tests with explicit prerequisites.
- Use `FileTask` with local fixtures for offline file workflows.
- For API serving of configured workflows, route to [api-and-deployment](../../api-and-deployment/SKILL.md).

## Console Caveat

Do not use `python -m txtai.console --help` as an argparse-style help check. The console treats the first argument as an index path and can fail trying to load `--help/config`. Console/API deployment behavior belongs in [api-and-deployment](../../api-and-deployment/SKILL.md).
