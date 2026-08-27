# CLI Reference

## Purpose

Use this when exact command syntax matters. The installed entry points verified for Argos Translate 1.11.1 are `argos-translate` and `argospm`.

## `argos-translate`

`argos-translate` translates one text string or stdin using already-installed language packages.

Help shape verified from the installed command:

```text
usage: argos-translate [-h] [--from-lang FROM_LANG] [--to-lang TO_LANG] [TEXT]
```

Options:

| Option | Meaning |
| --- | --- |
| `TEXT` | Text to translate. If omitted while both languages are provided, stdin is read. |
| `--from-lang FROM_LANG`, `-f FROM_LANG` | Source language code, normally ISO 639-style such as `en`. |
| `--to-lang TO_LANG`, `-t TO_LANG` | Target language code, normally ISO 639-style such as `es`. |
| `-h`, `--help` | Print help. |

Examples:

```bash
argos-translate --from-lang en --to-lang es "Hello world"

echo "Text to translate" | argos-translate -f en -t es
```

Important behavior:

- `argos-translate --from-lang en --to-lang es` with no `TEXT` reads stdin.
- `argos-translate "Hello"` without both language flags uses identity translation and prints the input unchanged. Do not treat that as a successful language-pair translation.
- If the source or target code is not installed, the CLI reports a parser error such as `'en' is not an installed language.`
- If both languages exist but no path connects them, the CLI reports `No translation installed from <from> to <to>`.
- Current installed help uses `--from-lang` and `--to-lang`. Older examples may show `--from` and `--to`; do not assume those aliases exist in this release.

## `argospm`

`argospm` manages package index and installed language packages.

Help shape verified from the installed command:

```text
usage: argospm [-h] {update,search,install,list,remove} ...
```

Subcommands:

| Command | Meaning | Network? |
| --- | --- | --- |
| `argospm update` | Download the remote package index. | Yes |
| `argospm search [-f FROM] [-t TO]` | Search available packages from the local/updated package index. | Usually yes on first use or stale/missing index |
| `argospm install NAME` | Install a package by index name, such as `translate-en_es`. | Yes unless already cached |
| `argospm install translate` | Install all available packages. This can be very large. | Yes, large |
| `argospm list` | Print installed package names. | No |
| `argospm remove NAME` | Remove one installed package. | No |

`argospm search` filters:

```bash
argospm update
argospm search --from-lang en --to-lang es
argospm search -f en -t de
```

Install/remove examples:

```bash
argospm install translate-en_es
argospm list
argospm remove translate-en_es
```

Failure signals:

- `Package not found` means the index did not contain the requested `argospm` package name after filtering/loading.
- Download failures are usually network, package index, or package link problems. See `troubleshooting.md` and `sub-skills/package-management/references/troubleshooting.md`.
- Removing a missing package prints `Package not found` and exits non-zero.

## Local package installation from Python

There is no separate CLI command for installing an arbitrary local `.argosmodel` path. Use Python:

```python
from pathlib import Path
from argostranslate import package

package.install_from_path(Path("translate-en_es.argosmodel"))
```

Before installing an unknown archive, validate its structure with `sub-skills/package-management/scripts/check_argosmodel.py`.

## Legacy wrappers and shell completion

The source repository includes thin `bin/` wrappers and a legacy `argos-translate-cli` wrapper, but the supported installed console scripts in `setup.py` are `argos-translate` and `argospm`.

For bash completion, read or source the bundled `scripts/completion.bash`. It completes the current `argos-translate` and `argospm` commands and also includes the legacy `argos-translate-cli` completion target for older environments.
