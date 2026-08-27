# Preferences, files, and caches

Brian's global `prefs` object is a validated mapping with both dotted-key and
attribute access. Preference changes are process-local unless written to a
preference file; importing Brian automatically loads the supported files.

## Inspect and set preferences safely

These forms are equivalent:

```python
from brian2 import prefs

current_target = prefs["codegen.target"]
current_cache = prefs["codegen.runtime.cython.cache_dir"]
prefs["codegen.target"] = "numpy"
prefs.codegen.runtime.cython.cache_dir = None
```

Use `prefs[key]` for a fully qualified name and the attribute form for
interactive autocompletion. A category such as `prefs.codegen` is a view, not
a value that can be replaced. Preferences cannot be deleted.

Brian validates direct assignments against the registered preference definition:
type mismatches, incompatible units, illegal names, unknown categories, and
unknown preference names raise `PreferenceError`. A spelling mistake is not a
harmless new setting. When a preference file is read before a third-party device
registers its category, `devices.*` values may be deferred; unresolved values
produce a warning at a later validation/checkpoint and usually indicate a
misspelling or missing package import.

For a minimal, path-conscious inspection, use targeted values rather than
copying the entire preference dump into a report:

```python
from brian2 import prefs

for name in (
    "codegen.target",
    "codegen.string_expression_target",
    "codegen.max_cache_dir_size",
    "codegen.runtime.cython.cache_dir",
    "codegen.runtime.cython.multiprocess_safe",
    "codegen.runtime.cython.delete_source_files",
    "codegen.cpp.compiler",
    "logging.file_log",
    "logging.file_log_level",
    "logging.console_log_level",
):
    try:
        print(name, repr(prefs[name]))
    except KeyError:
        print(name, "not registered")

print("unvalidated preference names:", sorted(prefs.prefs_unvalidated))
prefs.check_all_validated()
```

`prefs.as_file` serializes current values and `prefs.defaults_as_file` serializes
default values. They are useful for a controlled comparison, but can contain
user-specific include/library/cache paths. Redact those values before sharing a
report. `prefs.reset_to_defaults()` is process-local but still changes the
running application; use it only in a controlled diagnostic and restore the
application's intended settings afterward.

## Preference-file precedence and syntax

Brian reads, in order:

1. the user file `~/.brian/user_preferences`;
2. `brian_preferences` in the current working directory.

Missing files are ignored. Later values override earlier values, so the
current-directory file wins. The old package `default_preferences` file is no
longer the supported source and triggers a deprecation warning if present.

The file is plain text. Blank lines and lines beginning with `#` are ignored;
values are evaluated in a namespace containing NumPy and Brian units:

```text
codegen.target = 'numpy'
codegen.runtime.cython.cache_dir = None
[logging]
file_log = True
console_log_level = 'DEBUG'
```

Strings must be quoted. Numeric values, booleans, `None`, NumPy names, and unit
expressions are evaluated; do not place arbitrary code in an untrusted file.
A section prefixes subsequent keys, so `[logging] file_log = False` means
`logging.file_log`. Entries must contain `=` or a well-formed `[section]`; a
malformed line raises `PreferenceError` while loading.

When a preference unexpectedly selects a target or cache:

1. Start a fresh interpreter from the same working directory as the failing
   command.
2. Inspect the targeted effective values and `prefs.prefs_unvalidated`.
3. Temporarily move or rename the current-directory `brian_preferences` only
   with explicit user approval, then re-check whether the user file is the
   remaining source.
4. Repair the smallest offending key with a quoted value and restart Python.
5. Do not paper over a spelling error by setting an unregistered key. If a
   device-specific key is intended, import that device package and verify its
   registration before using it.

A process assignment is often safer than editing a global file for an
experiment. Keep configuration changes explicit and restore the prior state
when an embedding application continues after the diagnostic.

## Cache ownership and clearing

Brian tracks the on-disk Cython cache and warns when it exceeds
`prefs.codegen.max_cache_dir_size` (default: 1000 MB). The effective cache is
normally a `brian_extensions` directory under Cython's cache root, unless
`prefs.codegen.runtime.cython.cache_dir` is set to a string. Cython cache keys
include the generated code, Python version/interpreter, Cython version, NumPy
major/minor version, and `CC`/`CXX` values; a compiler or package change can
therefore make an old artifact unusable even when its filename remains.

Read-only triage should check, without creating anything:

- whether the configured cache value is `None` or a string;
- whether its directory exists and is writable by the active user;
- whether another process is compiling there;
- whether the Python/Cython/NumPy/compiler combination changed;
- whether a user or current-directory preference file changed the setting.

Do not print or share the cache path in a public report. Do not clear a cache
while a Brian process may be compiling or using it.

When the user has approved destructive cleanup and all relevant processes have
stopped, Brian exposes a guarded API:

```python
from brian2 import clear_cache
clear_cache("cython")
```

The API raises `ValueError` when the target has no registered cache. It scans
for unexpected file extensions and raises `OSError` rather than deleting a
file it cannot classify; inspect and resolve that condition manually. It
removes the registered cache directory, not arbitrary directories. A missing
cache is treated as a no-op. Re-run the smallest intended simulation after
cleanup so the cache is rebuilt deliberately.

For parallel Cython work on NFS, the source guidance recommends an independent
cache directory per process and `prefs.codegen.runtime.cython.multiprocess_safe
= False`, because file locking can be very slow on NFS. This is an operational
trade-off: unique directories avoid cross-process collisions, while disabling
locking in a shared directory is unsafe.

## Logging-related preferences

Relevant validated preferences include:

- `logging.file_log` and `logging.file_log_level` (default file logging and
  `DEBUG` file level);
- `logging.console_log_level` (default `INFO`);
- `logging.file_log_max_size` (default 10 MB rotation with one backup);
- `logging.std_redirection` and `logging.std_redirection_to_file` (compiler
  output suppression/capture);
- `logging.save_script` and `logging.delete_log_on_exit`;
- `logging.display_brian_error_message` and
  `logging.warn_for_unused_objects`.

Changing these values affects the next logger initialization or the current
process as appropriate. See [troubleshooting](troubleshooting.md) for a
minimal diagnostic sequence and the routing boundary for workflow errors.
