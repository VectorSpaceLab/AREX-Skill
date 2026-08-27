# Foolbox zoo troubleshooting

Diagnose the stage that failed. A clone failure, Python import failure,
factory failure, bad model result, HTTP failure, and archive failure have
different remedies. Do not retry networked operations blindly.

## Invalid repository URL or clone failure

**Symptom:** `get_model(...)` raises `foolbox.zoo.GitCloneError` with
`Failed to clone repository`.

**Checks:**

1. Confirm the URL is the intended Git URI, including the scheme/host and
   repository suffix. Test DNS and Git access only if network access is
   approved.
2. Check that GitPython is importable and that the `git` executable/transport
   needed by the URI is available. A missing GitPython import can fail while
   importing Foolbox and therefore is not necessarily wrapped in
   `GitCloneError`.
3. For a private repository, use an approved SSH agent or credential helper.
   Do not add a token to the URL. Check repository permissions and host policy.
4. Look at the logged underlying clone exception if it is available, but do not
   expose credentials in copied logs.

The cloner catches exceptions from `Repo.clone_from` and replaces their detail
in the raised exception. A successful clone only means Git produced a
checkout; it says nothing about `foolbox_model.py` or its dependencies.

## Missing module, missing `create()`, or import collision

**Symptom:** `ModuleNotFoundError`, an import-time dependency error, or an
`AttributeError` such as a module lacking `create` after the clone succeeds.

- Confirm the path passed to `ModelLoader.load` is the directory containing the
  module, not the module file itself.
- Confirm the requested `module_name` matches an importable `.py` file. The
  default is `foolbox_model`; passing `module_name="model"` requires
  `model.py` or an importable `model` package.
- Confirm the module exposes a callable `create`. The default loader calls
  `module.create(**kwargs)` directly and does not provide a friendlier error.
- Check the factory's imports and optional backend dependencies separately.
- In a long-lived process, unload a previously imported module with the same
  name or use a distinct module name. `ModelLoader` inserts the new path at
  `sys.path[0]`, but `importlib` still honors an existing `sys.modules` entry.

Do not solve a missing factory by guessing another module or executing an
unreviewed repository entry point. First inspect the repository contract.

## Factory keyword or wrong return type

**Symptom:** `TypeError` from `create`, a model that lacks `bounds`, or a
later call failure such as `'NoneType' object is not callable`.

`get_model` and `DefaultLoader.load` forward all extra keywords to
`create(**kwargs)`. Remove misspelled/unsupported keywords or use the factory's
actual signature. Foolbox's `cast(Model, model)` is static typing only; it does
not enforce the runtime type. A valid result should satisfy:

```python
import foolbox
assert isinstance(model, foolbox.Model)
print(model.bounds)
# Exercise one small backend-native input batch as well.
```

A raw PyTorch/TensorFlow/JAX module, an unwrapped callable, `None`, or an
object with an incompatible `__call__` is not a Foolbox-zoo model. Use the
model-wrapper route to construct a wrapper inside `create()`; do not mix attack
logic into the zoo loader.

## GitPython or requests is unavailable

This Foolbox version declares `GitPython>=3.0.7` and `requests>=2.24.0` as
package requirements, but a partial install, vendored environment, or broken
interpreter may omit them.

- `GitPython` is needed for the `foolbox.zoo` import and remote clone path.
  Repair the environment using its approved package-management process; do not
  copy a local `git` module into the repository.
- `requests` is needed for `fetch_weights`. A local `ModelLoader` check does
  not need to make an HTTP request, so use the bundled checker while the
  network dependency is being repaired.
- Frameworks used by a factory (PyTorch, TensorFlow, JAX, or their vision
  packages) are separate optional backend requirements and may fail after the
  loader itself has worked.

Do not install packages from an unapproved index or run a remote factory as an
installation test.

## Download, HTTP, and cache failures

**Symptom:** `fetch_weights` raises `RuntimeError: Failed to fetch weights
from ...`, hangs, or returns a path that is not usable.

- The implementation accepts only status `200`; 3xx, 4xx, 5xx, authentication,
  proxy, DNS, TLS, and connection failures can fail the request or produce the
  generic runtime error. Verify the exact approved URI and access policy.
- There is no request timeout, checksum, content-type check, atomic temporary
  file, or automatic retry. Interrupt a transfer that is not progressing and
  inspect the exact cache directory before removing a partial file.
- A cache directory is considered present by existence alone. Foolbox can
  therefore reuse a stale or incomplete file and does not automatically
  refresh it. There is no `overwrite` parameter for `fetch_weights`.
- Query parameters affect the hash directory but are removed from the derived
  filename. A URI with no final filename can produce an unusable path.
- `weights_uri=None` triggers an assertion, not a network error.

Never paste a secret-bearing URL into diagnostics. When a source or response
is unexpected, stop and request a reviewed source rather than following
redirects or trying alternate hosts.

## Archive extraction failures and safety

With `unzip=True`, the source recognizes a path containing `.zip` first and
then a path containing `.tar.gz`. Unsupported archive names can result in an
empty extraction directory in this version. Bad ZIP/tar data, permissions, and
filesystem errors propagate from the standard-library extractor.

The implementation uses `extractall` without validating archive member paths.
Only extract archives from a trusted, approved source. Before a model consumes
the result, inspect the extraction directory and expected files. If an archive
is untrusted or has suspicious `../` or absolute members, stop; do not invoke
it and do not attempt an ad-hoc extraction workaround in the model repository.

Existing extraction directories are reused, so a previous partial extraction
can mask a later download. Inspect the directory and remove only the exact
URI-hash entry after stopping all users of it. Re-run only after approval and,
when possible, a source with a verifiable checksum.

## Cache overwrite and safe stopping

`get_model(..., overwrite=True)` deletes the exact URI-hash clone before
cloning; it is destructive to local edits and can leave no usable checkout if
the new clone fails. Start with the default `False` and copy any needed local
changes elsewhere before approving overwrite.

To stop safely:

1. Do not call `get_model` or `fetch_weights` until network, source, and
   credential approval is explicit.
2. If a call is running without a timeout, interrupt it at the process/job
   boundary rather than starting a second copy.
3. Record the exact URL, module, and cache hash; inspect before cleanup.
4. Remove only the intended clone, file, or extraction directory after closing
   model/file handles. Never recursively delete the entire home directory or
   the whole `~/.foolbox_zoo` cache as a generic fix.
5. Use the no-network checker to verify the local Foolbox loader independently.

Report unresolved permissions, missing dependencies, and partial downloads as
blocking gaps. Do not claim a remote model or external weights were verified
when only the local loader contract passed.
