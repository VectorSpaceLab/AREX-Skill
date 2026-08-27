# Configuration workflows and trust gates

ModelScope `Config` is used throughout dataset, training, and pipeline code. Use this reference to parse config files safely and to make small overrides without executing untrusted code.

## Supported formats

`Config.from_file(path, trust_remote_code=False, model_dir=None)` supports:

- `.json`
- `.yaml`
- `.yml`
- `.py`

JSON and YAML/YML are passive data formats. Python config files are executed as modules to collect top-level variables, so they can run arbitrary top-level code.

`Config.from_string(cfg_str, file_format)` supports the same suffixes, including `.py`. Source evidence treats `from_string` as caller-provided in-process content and internally opts into Python execution for the temporary file. Do not feed untrusted remote text to `from_string(..., ".py")`.

## Safe defaults

Prefer JSON/YAML for recipes and model/task configs produced by agents:

```python
from modelscope.utils.config import Config

cfg = Config.from_file("configuration.yaml")
print(cfg.safe_get("dataset.train.file", default=None))
```

Use `.py` configs only when all are true:

1. The source is known and trusted.
2. The user or workflow explicitly accepts code execution.
3. The code is not being loaded merely to inspect passive settings.
4. The execution environment can tolerate arbitrary imports and side effects from that file.

Then make the opt-in visible:

```python
cfg = Config.from_file("trusted_config.py", trust_remote_code=True)
```

If a `.py` config is inside a trusted ModelScope owner group, the helper may allow it without explicit opt-in. Do not rely on that shortcut for user-provided paths; keep the explicit trust decision in your recipe or code review.

## Trust gate behavior

`check_trust_remote_code_for_config(filename, trust_remote_code=False, model_dir=None)` refuses to load `.py` configs from untrusted model repositories unless `trust_remote_code=True`. Non-Python paths pass through. `model_dir` overrides the inferred repository root used by the owner-group check.

Operational consequences:

- A `RuntimeError` saying ModelScope is refusing to load a Python config is expected protection, not a dependency failure.
- JSON/YAML config loads should not require `trust_remote_code=True`.
- A malicious `.py` config can execute before returning a `Config`; never use it as a data-only parser.
- `Config.from_string("a = 1", ".py")` executes the string. Treat it like `exec` over trusted local text.

## Basic parsing

```python
from modelscope.utils.config import Config

cfg = Config.from_file("config.json")
print(cfg.filename)
print(cfg.to_dict())
print(cfg.safe_get("model.backbone.type", default="unknown"))
```

The returned object supports attribute access for dict keys:

```python
print(cfg.model.type)
```

If a key may not exist, use `safe_get` instead of chained attributes.

## `safe_get` key chains

`safe_get(key_chain, default=None, type_field="type")` walks dot-separated keys and handles list indexing with brackets:

```python
cfg.safe_get("train.hooks[0].type", default="none")
```

For a list or tuple of dicts, it can select an object by a `type` field:

```python
hook_cfg = cfg.safe_get("train.hooks.CheckpointHook", default={})
```

When any lookup fails, ModelScope logs debug detail and returns the default.

## Merging overrides

`merge_from_dict(options, allow_list_keys=True, force=True)` accepts dot-separated keys:

```python
cfg.merge_from_dict({
    "train.batch_size": 8,
    "model.backbone.depth": 18,
})
```

List handling modes from source tests:

- A dict with string integer keys can replace list elements by index:

```python
cfg.merge_from_dict({"pipeline": {"0": {"type": "MyResize"}}})
```

- A list of dicts with `type` fields can merge by matching `type`, appending new `type` values. Order of appended entries is not guaranteed by the source comments.
- `force=False` preserves existing scalar or matching values but still allows new keys/entries to be added.
- `force=True` replaces existing values when keys match.

## Dumping configs

`cfg.dump(file=None)` returns a string when no file is provided. If `cfg.filename` is missing or ends in `.py`, it returns Python-like pretty text. Otherwise it uses the filename extension's JSON/YAML handler.

`cfg.dump("out.yaml")` or `cfg.dump("out.json")` writes local files via ModelScope file IO. `cfg.dump("out.py")` writes Python pretty text. Do not dump to HTTP/HTTPS/OSS paths; HTTP writes and OSS writes are unsupported.

## Common config shapes in examples

Small passive config:

```yaml
a: 1
b:
  c: [1, 2, 3]
  d: dd
```

Training-like config excerpt:

```yaml
framework: pytorch
task: text-classification
model:
  type: text-classification
dataset:
  train:
    file: data/train.csv
  valid:
    file: data/valid.csv
preprocessor:
  type: Tokenize
train:
  batch_size: 32
evaluation:
  metrics: [accuracy, f1]
```

After config parsing, training/evaluation semantics belong to `../training-and-evaluation/SKILL.md`. This sub-skill owns safe parsing, field lookup, local data path validation, and trust decisions.

## Checklist before using a config

- [ ] Is the file extension one of `.json`, `.yaml`, `.yml`, `.py`?
- [ ] If `.py`, did the user or task explicitly trust the code source?
- [ ] Are local dataset paths inside `dataset.train`, `dataset.val`, `dataset.valid`, or `dataset.test` present?
- [ ] Are overrides applied with the intended `force` behavior?
- [ ] Are list overrides by index/type intentional?
- [ ] Are secrets/tokens absent from dumped config text and logs?
