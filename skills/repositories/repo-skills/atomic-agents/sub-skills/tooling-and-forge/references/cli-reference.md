# Atomic Assembler CLI Reference

## Entry point

- Command: `atomic`
- Module: `atomic_assembler.main:main`
- Use `atomic --help` to verify the command is installed.
- Use `atomic --version` to print the installed package version.

## Flags

| Flag | Meaning |
| --- | --- |
| `--enable-logging` | write debug logs to `atomic_assembler.log` |
| `--version` | print the CLI version and exit |
| `-h`, `--help` | show help text |

## What the TUI does

The Atomic Assembler TUI is a small Textual app that offers:

- browse files
- browse folders
- download tools
- open the Atomic Agents GitHub page
- exit the app

The tool downloader is intentionally opinionated: it lets users fetch a tool from Atomic Forge, inspect its README and config, and copy the tool into their own project.

## Common usage patterns

- Local check: `atomic --help`
- Version check: `atomic --version`
- Local repo smoke: `uv run atomic`

## Common failure modes

- The command is missing because the package is not installed in the active environment.
- The CLI launches but the user is not in an environment that contains the package dependencies.
- Tool downloads are not meant to be treated as live framework dependencies; they are user-project assets after download.

## When to read this file

Read this file when the user wants to launch, verify, or explain the `atomic` CLI/TUI.
