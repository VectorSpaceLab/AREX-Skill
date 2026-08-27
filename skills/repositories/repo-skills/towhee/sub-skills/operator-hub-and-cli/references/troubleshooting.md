# Troubleshooting operator and CLI issues

Use this guide to keep operator and CLI work safe. Do not use failures here as a reason to start live servers, initialize templates, or fetch Hub content unless the user explicitly asks for those side effects.

## `ModuleNotFoundError: No module named 'pkg_resources'`

Towhee imports `pkg_resources` during package import and operator loading. Some modern Python environments do not include it by default, and very new `setuptools` layouts can expose compatibility problems.

Safe fix:

```bash
python -m pip install --upgrade 'setuptools<81'
```

Then rerun the smallest import/help check:

```bash
python -m towhee --help
```

If the environment has a strict dependency policy, ask before changing global packages and prefer an isolated environment.

## Hub download, network, and cache failures

Symptoms:

- `RuntimeError: Loading operator with error:...`
- `RuntimeError: Load operator failed`
- `Fetch op <author>/<repo>:<tag> info failed`
- HTTP timeout, 429, missing LFS content, or unexpected package installation from an operator `requirements.txt`.

Facts that matter:

- `_OperatorWrapper` loads lazily; the network/cache path is usually triggered on first operator call, not when the wrapper is constructed.
- If a name cannot be resolved as an internal or registered operator, Hub loading is attempted. Names without `/` may fall back to the `towhee/` Hub namespace.
- The default cache root is controlled by `TOWHEE_HOME`; otherwise Towhee uses `~/.towhee`.
- `TOWHEE_URL` can override the Hub endpoint.
- `.revision(tag)` pins the selected tag or branch. `.latest()` requests a refresh and should be avoided in reproducible/offline work.

Triage:

1. Confirm whether the intended operator should be local/registered or remote Hub-backed.
2. For local registered operators, verify the `@register` name and `ops` expression before debugging network.
3. For Hub-backed operators, pin a revision and avoid `.latest()` unless refreshing is intentional.
4. If the cache is corrupt, remove only the specific operator/revision cache after user approval; do not delete the entire cache blindly.
5. If the failure mentions package installation from a Hub operator, ask before allowing dependency changes.

## Accidentally starting servers

`towhee server --help` is safe. `towhee server ...` is not a smoke test: it can start HTTP or GRPC servers, bind ports, import local modules, fetch Hub pipelines, and remain running.

If a server was started unintentionally:

1. Stop the process promptly.
2. Check for occupied ports before retrying any service task.
3. Move service planning to [serving-and-triton](../../serving-and-triton/SKILL.md).
4. Replace routine CLI validation with [../scripts/check_cli_help.py](../scripts/check_cli_help.py).

## Template writes from `towhee init`

`towhee init --help` is safe. `towhee init <author>/<repo> ...` downloads a template and writes an operator repository under `--dir`.

Common mistakes:

- Running init in a non-empty directory and mixing generated template files with existing work.
- Forgetting that `-t nnop` selects an NN operator template, not a complete trainable model.
- Treating init as offline; it requires Hub access for template download.
- Interrupting a run and leaving a temporary template directory behind.

Safe pattern:

1. Use `towhee init --help` for parser validation.
2. For real initialization, choose an empty scratch target and record whether `pyop` or `nnop` is wanted.
3. Inspect target contents after completion before editing.
4. If interrupted, remove only the temporary template directory after confirming no user files are inside.

## Local operator registration name mismatches

Symptoms:

- A registered operator unexpectedly falls through to Hub loading.
- `ops.foo_bar()` works but `ops.foo-bar()` is invalid Python syntax.
- A class is registered under one namespace while the call uses another.

Rules:

- Python attribute underscores are normalized to hyphens in the wrapper name.
- Dotted attributes become namespace/repo separators.
- `@register(name='add_operator')` resolves as an anonymous repo-style name like `anon/add-operator`; `ops.add_operator(...)` can still find it because registry lookup tries anonymous names.
- `@register(name='custom/add_operator')` should be called with a namespace-compatible expression such as `ops.custom.add_operator(...)`.
- `ops.local.<name>(...)` refers to the local-operator cache convention; it is not the same thing as anonymous `@register` unless the target name exists in that local cache.

Minimal diagnostic:

```python
from towhee.runtime.operator_manager import OperatorRegistry
print(OperatorRegistry.op_names())
```

Use this only to inspect registered names in the current Python process; registration is process-local.

## `NNOperator` training fails because no model exists

`NNOperator.train()` calls `setup_trainer()`. The trainer setup imports PyTorch and requires `self.model` or `self._model` to be a `torch.nn.Module`.

Failure signal:

```text
AttributeError: There is no trainable model attr in this operator.
```

Fix direction:

- For inference-only NN operators, implement `__call__` and do not call `train()`.
- For trainable operators, initialize a real PyTorch module in `self.model` or `self._model` before training.
- Route optimizer, dataset, scheduler, checkpoint, and trainer configuration work to [training-and-models](../../training-and-models/SKILL.md).

## CLI help check fails

1. Retry with module fallback:

   ```bash
   python ../scripts/check_cli_help.py --python-module
   ```

2. If the error is `pkg_resources`, install compatible `setuptools` as above.
3. If `towhee server --help` fails because optional serving dependencies are missing, inspect the error before installing packages; help should normally parse without starting HTTP/GRPC servers.
4. If help output changed intentionally in a newer Towhee version, update the expected flags in the validation script and this reference together.
