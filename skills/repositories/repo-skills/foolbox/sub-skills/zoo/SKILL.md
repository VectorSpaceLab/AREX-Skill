---
name: zoo
description: "Foolbox model-zoo guidance for loading local or remote
  Foolbox-compatible repositories, implementing foolbox_model.py create()
  contracts, fetching weights, and diagnosing networked model-loader failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Foolbox model zoo

Use this route when a task mentions `foolbox.zoo`, `get_model`,
`foolbox_model.py`, `ModelLoader`, shared model repositories, downloaded model
weights, or a `GitCloneError`. Read [`references/api-reference.md`](references/api-reference.md)
for signatures and [`references/workflows.md`](references/workflows.md) for
local and remote procedures.
## Command, cache, and approval paths

The checker command in the workflow reference is relative to the generated
Foolbox skill root, not a native Foolbox checkout and not the caller's current
directory. From any cwd, set the root and change into it first:

```bash
# Replace this non-executable placeholder with the absolute directory containing the root SKILL.md.
export SKILL_ROOT=/path/to/installed/skills/disco/foolbox
cd "$SKILL_ROOT"
```

Use the actual skill-root path when it differs from this installation, or use an
absolute script path. Local checker output is temporary and does not write model
zoo data into the skill. `get_model()` clones into Foolbox's cache and
`fetch_weights()` writes downloads/extractions there (typically under
`~/.foolbox_zoo`), not beside these documents; record and inspect the returned
path before cleanup. Plot or report files belong in an explicit absolute output
directory such as `"$SKILL_ROOT/outputs/"`, never in source/reference assets.

The local checker is offline. A zoo clone or weights download/extraction is
networked and may execute untrusted code or consume substantial disk; obtain
explicit approval immediately before `zoo.get_model(...)` or
`zoo.fetch_weights(...)`, even if a cache entry exists. Do not treat cache
presence as approval.


## Choose a safe route

- **Local repository:** prefer a local fixture or a user-owned repository,
  inspect its `foolbox_model.py`, and validate `create()` without network.
  Run [`scripts/check_local_zoo_model.py`](scripts/check_local_zoo_model.py).
- **Remote repository:** `fb.zoo.get_model(url, module_name='foolbox_model',
  overwrite=False, **kwargs)` clones into Foolbox's cache and imports the module.
  This executes remote code and may install/use framework dependencies; obtain
  approval before cloning.
- **Weights only:** `fb.zoo.fetch_weights(uri, unzip=False)` downloads to a
  Foolbox cache; `unzip=True` extracts ZIP or tar.gz archives. Treat this as a
  networked, potentially large operation and verify checksums/provenance outside
  the normal smoke path.

A compatible model module must expose `create(**kwargs)` and return a Foolbox
`Model` wrapper. The default module name is `foolbox_model`. Keep model loading
separate from attack benchmarking so a failed clone or weight download does
not look like an attack failure.

Use [`references/troubleshooting.md`](references/troubleshooting.md) for module
imports, invalid URLs, missing `create()`, return types, cache/overwrite,
network failures, and archive extraction. Do not run remote examples from the
original repository as part of a routine offline verification.
