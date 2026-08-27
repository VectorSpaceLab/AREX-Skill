# Package-Management Troubleshooting

## Purpose

Use this when `argospm`, `package.install_from_path()`, package discovery, or `.argosmodel` validation fails.

## Package index cannot update

Symptoms:

- `argospm update` returns without writing a usable index.
- `argospm search` finds nothing for pairs that should exist.
- Python `package.get_available_packages()` repeatedly tries to update the index.

Likely causes:

- Network unavailable.
- `ARGOS_PACKAGE_INDEX` is wrong or missing a trailing slash/base path.
- The remote package index changed or is unreachable.

Recovery:

```bash
python - <<'PY'
from argostranslate import settings
print(settings.package_index)
print(settings.remote_package_index)
print(settings.local_package_index)
PY
argospm update
```

If network access is not allowed, use a local `.argosmodel` archive and `package.install_from_path()` instead.

## `Package not found`

Symptoms:

```text
Package not found
```

Likely causes:

- The requested name is not in the package index.
- The language codes are reversed or misspelled.
- The local index is stale.

Recovery:

```bash
argospm update
argospm search -f en -t es
```

Install the exact name printed by `search`, such as `translate-en_es`.

## Invalid `.argosmodel` archive

Symptoms:

- `Not a valid Argos Model (must be a zip archive)`.
- `FileNotFoundError` for `metadata.json` after extraction or when constructing `Package(path)`.
- Translation fails because tokenizer or model files are missing.

Recovery:

```bash
python sub-skills/package-management/scripts/check_argosmodel.py translate-en_es.argosmodel
python sub-skills/package-management/scripts/check_argosmodel.py --strict translate-en_es.argosmodel
```

If metadata is missing or not parseable, get a new archive. If strict mode warns about missing `model/` or tokenizer files, do not expect normal local OpenNMT translation from that package.

## Installed package is not discovered

Symptoms:

- `argospm list` is empty after installing.
- Python `package.get_installed_packages()` returns no packages.
- `translate.get_installed_languages()` does not include the expected language.

Likely causes:

- Package installed into a different `ARGOS_PACKAGES_DIR` or XDG data directory.
- A long-running process cached languages before install.
- Extraction layout does not put package directories under the configured package dir.

Recovery:

1. Print active settings:

   ```bash
   python - <<'PY'
   from argostranslate import settings
   print(settings.package_data_dir)
   print(settings.package_dirs)
   PY
   ```

2. Run `argospm list` from the same environment that will translate.
3. Restart the Python process or call `translate.get_installed_languages.cache_clear()` after manual changes.

## Permission errors writing package/cache dirs

Likely causes:

- The configured package directory is not writable.
- A package was installed as another user.
- Snap or XDG variables point to unexpected directories.

Recovery:

- Set `ARGOS_PACKAGES_DIR` to a writable directory before import.
- Avoid mixing root/user installs.
- Reinstall packages in the intended directory.
- Do not run destructive cleanup unless the user explicitly approves deleting packages/caches.

## Removing packages fails or removes the wrong package

`argospm remove NAME` matches `package.argospm_package_name(installed_package)`. Verify names first:

```bash
argospm list
```

If using Python, compare the computed name before calling `package.uninstall(pkg)`. Removal uses `shutil.rmtree(pkg.package_path)`, so it deletes the directory recursively.

## Installing every package is too large

`argospm install translate` calls the install-all path. This can download many language packages and consume large disk space.

Recovery:

- Prefer `argospm search -f SOURCE -t TARGET` and install only the needed pair.
- If all packages are required, get explicit approval for network, time, and disk use.

## Remote downloads succeed but translation still fails

A package can download and extract successfully but still fail during translation due to CTranslate2 compatibility, missing tokenizer, optional SBD resources, device mode, or corrupted model files.

Recovery:

1. Validate archive/package structure with `sub-skills/package-management/scripts/check_argosmodel.py`.
2. Switch to `ARGOS_DEVICE_TYPE=cpu` and `ARGOS_COMPUTE_TYPE=auto` for a tiny translation.
3. Then route to the translation troubleshooting file for runtime model-load or device errors.
