# MCP tool API reference

The MCP server registers these functions with FastMCP. Input schemas are derived from the Python type hints and defaults; returns are plain strings.

## Shared task-mode type

The server defines a `TaskType` literal with values `standard`, `few-shot`, `multimodal`, and `documental`, but the actual wrapper implementation only supports standard local predictor paths for the current tools.

Do not infer support for few-shot, multimodal, or document-level workflows from the literal alone. Those workflows belong to other DeepKE examples and are not exposed by this MCP wrapper.

## `deepke_ner`

Signature:

```python
deepke_ner(task: TaskType, txt: str) -> str
```

Arguments:

- `task`: must be `standard`. Other values return a message indicating that only standard NER is supported.
- `txt`: input text to write into the local standard NER prediction config.

Behavior:

1. Resolves the local standard NER example directory under `DEEPKE_PATH`.
2. Reads the prediction YAML config.
3. Replaces the config `text` value with `txt`.
4. Runs the standard NER `predict.py` with the Python prefix from `CONDA_PY`.
5. Returns predictor stdout on success.

Side effects and limitations:

- Mutates the local NER prediction YAML.
- Requires a compatible local DeepKE environment and any model/config artifacts expected by the NER example.
- Failure returns text beginning with `[运行失败]` plus the exception text.

## `deepke_re`

Signature:

```python
deepke_re(
    task: TaskType,
    txt: str,
    head: str,
    head_type: str,
    tail: str,
    tail_type: str,
) -> str
```

Arguments:

- `task`: must be `standard`. Other values return a message indicating that only standard RE is supported.
- `txt`: sentence containing the two entity mentions.
- `head`: head-entity mention to classify from.
- `head_type`: head-entity type string expected by the local predictor.
- `tail`: tail-entity mention to classify to.
- `tail_type`: tail-entity type string expected by the local predictor.

Behavior:

1. Resolves the local standard RE example directory under `DEEPKE_PATH`.
2. Builds the interactive predictor stdin sequence: `n`, sentence, head, head type, tail, tail type.
3. Runs the standard RE `predict.py` with the Python prefix from `CONDA_PY`.
4. Returns stdout if the subprocess exits with status 0; otherwise returns `[运行失败]` and stderr.

Side effects and limitations:

- Does not edit a config file directly, but still depends on local example configs and checkpoints.
- Entity strings and types must match what the local model/config expects.
- No few-shot, multimodal, or document-level RE support is exposed through this MCP tool.

## `deepke_ae`

Signature:

```python
deepke_ae(
    txt: str,
    entity: str,
    attribute_value: str,
    task: TaskType = "standard",
) -> str
```

Arguments:

- `txt`: sentence containing the entity and attribute value.
- `entity`: entity mention to evaluate.
- `attribute_value`: attribute value mention to evaluate.
- `task`: defaults to `standard`. The current implementation does not enforce or branch on non-standard values.

Behavior:

1. Resolves the local standard AE example directory under `DEEPKE_PATH`.
2. Builds the interactive predictor stdin sequence: `n`, sentence, entity, attribute value.
3. Runs the standard AE `predict.py` with the Python prefix from `CONDA_PY`.
4. Returns stdout if the subprocess exits with status 0; otherwise returns `[运行失败]` and stderr.

Side effects and limitations:

- Depends on local example configs and checkpoints.
- Treat non-standard `task` values as unsupported even though the function accepts the argument.
- Failure may return `[运行失败]` or `[运行异常]` depending on whether the subprocess failed or Python raised before/around execution.

## `deepke_ee`

Signature:

```python
deepke_ee(txt: str) -> str
```

Arguments:

- `txt`: input event sentence.

Behavior:

1. Resolves the local standard EE example directory under `DEEPKE_PATH`.
2. Converts `txt` into one-line raw JSONL plus role and trigger TSV files with `\x02`-separated characters and `O` labels.
3. Sets the local EE training config `task_name` to `trigger` and runs event `run.py` with the Python prefix from `CONDA_EE_PY`.
4. Sets `task_name` to `role` and runs event `run.py` again.
5. Runs event `predict.py` with `CONDA_EE_PY`.
6. Reads trigger and role prediction/result files and returns a combined Chinese report.

Side effects and limitations:

- Mutates EE raw data, role TSV, trigger TSV, and training YAML files in the local checkout.
- May be slow or fail if local configs trigger training/evaluation instead of a lightweight prediction path.
- Requires event extraction data/config/checkpoint artifacts expected by the local EE example.
- Failure returns text beginning with `[运行失败]` plus the exception text.

## Return interpretation

The MCP wrapper does not normalize model outputs. Downstream agents should treat returns as human-readable logs and parse them conservatively:

- Empty stdout may still indicate a local predictor issue rather than an empty extraction result.
- Bracketed Chinese failure prefixes indicate wrapper-level or subprocess failures.
- EE output combines metrics-like result text and raw prediction content; a human or task-specific parser must map `B`, `I`, and `O` tags back to the original sentence.

## Unsupported task surfaces

The MCP wrapper does not expose:

- Training APIs.
- Few-shot, multimodal, cross-domain, document-level, or cnSchema-specific task variants.
- Triple extraction or LLM/instruction KGC tools.
- Remote hosted MCP service administration.
- Credential provisioning or model checkpoint download.
