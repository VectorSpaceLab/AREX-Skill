# Model Zoo Workflows
All shell paths in this reference are relative to the generated Foolbox skill
root, not to the native Foolbox checkout and not to the caller's cwd. From any
cwd, set and enter that root first (or substitute an equivalent absolute path):

```bash
# Replace this non-executable placeholder with the absolute directory containing the root SKILL.md.
export SKILL_ROOT=/path/to/installed/skills/disco/foolbox
cd "$SKILL_ROOT"
```

Keep generated reports/plots in an explicit absolute output directory such as
`"$SKILL_ROOT/outputs/"`; do not write into `references/`, `scripts/`, or native
checkout source assets. The model-zoo helpers write clones, downloaded weights,
and extracted archives to Foolbox's cache (typically `~/.foolbox_zoo`), not to
the skill root. Record and inspect returned paths; never remove the whole cache.

Network and external-state boundary: obtain explicit approval immediately before
running a remote clone or weights download/extraction, even when a cache entry
already exists. The local checker below is the no-network alternative.

## Validate a local model repository

Create or inspect a directory containing `foolbox_model.py` with a callable
`create(**kwargs)`. The function should construct the underlying model,
configure bounds/preprocessing, wrap it in a Foolbox `Model`, and return it.
Use the bundled local checker for a no-network validation:

```bash
cd "$SKILL_ROOT"
python sub-skills/zoo/scripts/check_local_zoo_model.py --help
python sub-skills/zoo/scripts/check_local_zoo_model.py
```

A local loader imports the requested module by temporarily putting the model
repository path on `sys.path`; keep the module name unique in a long-lived
process and avoid loading untrusted code without review.

## Load a remote repository

Only after explicit approval and network checks. The `example.invalid` URL below
is a documentation placeholder and must not be executed; replace it only with an
approved repository URL.

```python
from foolbox import zoo
fmodel = zoo.get_model(
    "https://example.invalid/model-repo.git",
    module_name="foolbox_model",
    overwrite=False,
    # model-specific kwargs are forwarded to create()
)
```

Verify `fmodel.bounds`, a small forward pass, and clean accuracy before using
it in an attack. `overwrite=True` deletes the cached clone before recloning;
use it only when replacement is intended.

## Fetch weights

```python
path = zoo.fetch_weights(weights_uri, unzip=False)
archive_dir = zoo.fetch_weights(zip_uri, unzip=True)
```

The helper derives a cache path from the URI hash, streams a successful HTTP
response to disk, and raises `RuntimeError` for a non-200 response. ZIP and
`.tar.gz` extraction are supported. Inspect downloaded archives before loading
weights and avoid path traversal or untrusted model code.

## Model-zoo handoff to attacks

The zoo helper only returns a model. After loading, switch to the models route
to verify bounds, preprocessing, data format, and logits; then use the attacks
route to choose a threat model and report attack results. Keep remote clone and
weight-download logs separate from scientific robustness metrics.
