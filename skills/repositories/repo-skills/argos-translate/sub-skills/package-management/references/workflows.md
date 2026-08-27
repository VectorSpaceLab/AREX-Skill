# Package-Management Workflows

## Purpose

Use this reference to install or inspect model packages before running translation.

## Workflow 1: update and search the package index

```bash
argospm update
argospm search -f en -t es
```

Expected search output shape:

```text
translate-en_es: en -> es
```

`argospm update` downloads the package index from the configured `ARGOS_PACKAGE_INDEX` base URL. If the local index is missing, Python `package.get_available_packages()` also attempts to update it.

## Workflow 2: install from remote index

```bash
argospm install translate-en_es
argospm list
```

`argospm install NAME` searches available packages by `package.argospm_package_name(pkg)`. The special name `translate` installs every available translation package and can be very large.

Use filters before install when you are not sure of the exact package name:

```bash
argospm search --from-lang en --to-lang es
```

## Workflow 3: install from a local `.argosmodel`

Validate first:

```bash
python sub-skills/package-management/scripts/check_argosmodel.py translate-en_es.argosmodel
```

Install with Python:

```python
from pathlib import Path
from argostranslate import package

package.install_from_path(Path("translate-en_es.argosmodel"))
```

Then list installed packages:

```bash
argospm list
```

If this install occurs in a long-running Python process that already called `translate.get_installed_languages()`, restart the process or clear the cache.

## Workflow 4: list and inspect installed packages

CLI:

```bash
argospm list
```

Python:

```python
from argostranslate import package

for pkg in package.get_installed_packages():
    print(package.argospm_package_name(pkg), pkg.from_code, "->", pkg.to_code)
```

Custom directory inspection:

```python
from pathlib import Path
from argostranslate import package

for pkg in package.get_installed_packages(Path("/path/to/packages")):
    print(pkg.package_path, pkg.get_description())
```

Use a custom path only for inspection. For normal runtime discovery, set `ARGOS_PACKAGES_DIR` before import or use the default package directory.

## Workflow 5: remove an installed package

```bash
argospm remove translate-en_es
argospm list
```

Python:

```python
from argostranslate import package

for pkg in package.get_installed_packages():
    if package.argospm_package_name(pkg) == "translate-en_es":
        package.uninstall(pkg)
        break
```

Removal deletes the installed package directory. Confirm the requested package name and package directory before removing.

## Workflow 6: install a pair if available from Python

```python
from argostranslate import package

ok = package.install_package_for_language_pair("en", "es")
if not ok:
    raise RuntimeError("No direct en -> es package in the current package index")
```

This uses the available package index and downloads the package if found. It is a networked workflow unless the package is already cached.

## Workflow 7: debug package directory mismatch

Run the same environment for package listing and translation:

```bash
python - <<'PY'
from argostranslate import package, settings, translate
print("package_data_dir", settings.package_data_dir)
print("installed packages", [package.argospm_package_name(p) for p in package.get_installed_packages()])
print("languages", [(l.code, l.name) for l in translate.get_installed_languages()])
PY
```

If packages appear in one process but not another, compare `ARGOS_PACKAGES_DIR`, `XDG_DATA_HOME`, Snap variables, and the Python environment running each process.

## Workflow 8: archive preflight before installation

The bundled `sub-skills/package-management/scripts/check_argosmodel.py` is read-only. It checks zip validity, metadata presence, model directory, tokenizer files, and optional SBD resources.

```bash
python sub-skills/package-management/scripts/check_argosmodel.py --strict translate-en_es.argosmodel
```

Use `--strict` when the archive should be a runnable translation package. Without `--strict`, the helper reports warnings but only fails for invalid zip files or missing/invalid metadata.
