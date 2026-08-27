# CLI troubleshooting

## Command not found

Symptoms: `ns-train: command not found`, `No module named nerfstudio`, or a command resolves to an unexpected environment.

Actions:

1. Check the active Python: `python -c "import sys; print(sys.executable)"`.
2. Check package metadata: `python -c "from importlib.metadata import version; print(version('nerfstudio'))"`.
3. Reinstall in the same environment that will run the commands.
4. Run the bundled `inspect_ns_cli.py --commands ns-train ns-process-data --run-help`.

## Tyro says a flag is unrecognized

Likely cause: the flag belongs to a method/dataparser subcommand but was placed at the wrong level.

Recovery:

- Use `ns-train --help` to choose a method.
- Use `ns-train METHOD --help` for method flags.
- Use `ns-train METHOD DATAPARSER --help` for dataparser flags.
- Rebuild the command with method flags before the dataparser and dataparser flags after it.

## Help output is slow or imports graphics warnings

Some commands import optional mesh/viewer dependencies while building help. Non-fatal pymeshlab/OpenGL plugin warnings can appear on headless machines. Treat them as mesh/export prerequisites unless the command exits non-zero.

## Download command would be unsafe

`ns-download-data` can overwrite or populate output data folders and needs network. Confirm the dataset, capture name, save directory, free disk, and whether credentials/network rules permit the download before running it.
