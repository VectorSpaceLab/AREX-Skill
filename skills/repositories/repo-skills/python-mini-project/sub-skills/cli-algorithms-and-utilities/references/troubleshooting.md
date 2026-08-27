# Troubleshooting

Use this table when a console-first utility in this subtree fails or behaves unexpectedly.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `python: can't open file ...` or `FileNotFoundError` | The command was run from the wrong working directory. | Run from the project folder, or pass an absolute path to the script and fixture. The smoke-check script accepts `--root` for the target checkout. |
| Path lookups fail for folders with spaces | The shell or caller split the path on spaces. | Quote the path when displaying it, and use `Path` objects or `subprocess.run([...])` for real execution. Examples in this repo include `Execute Shell Command` and `Email Slicer`. |
| `argparse` prints usage and exits | A required positional argument was missing or the wrong option name was used. | Run the script with `--help`, confirm the expected positional paths, and keep the help text accurate. `Cat_command/cat.py` is a good example of the one-positional-argument shape. |
| Shell execution looks dangerous or unpredictable | The helper is passing raw user input to `shell=True`. | Do not generalize shell helpers into arbitrary command execution. Keep the curated smoke test fixed to the repository's existing `echo` case only. |
| A module runs code as soon as it is imported | There are top-level side effects instead of a `main()` guard. | Move the demo or prompt loop behind `if __name__ == "__main__":` and keep imported helpers quiet. |
| `Smart_Calculator/calculator.py` opens a window or hangs headless runs | The module imports Tk and calls `Tk()`/`mainloop()` at import time. | Treat it as a GUI edge case. Do not run it in the default smoke path; inspect it statically or use a GUI-enabled session if the interface is the goal. |
| `ModuleNotFoundError` for `rich`, `pyperclip`, or similar extras | A project-local dependency is missing from the current environment. | Install only the dependency needed for that one project, or skip the project if the current task is about the safe stdlib subset. |
| A file-transformer overwrote output unexpectedly | The project used a fixed output file name. | Add an explicit output argument before broadening the workflow, or document the default output path very clearly. |
| A calculator or cipher produces the wrong answer | The I/O wrapper and the core math are tangled together. | Pull the transformation into a pure helper first, then test it with synthetic values before reattaching the prompt loop. |

## Quick sanity checklist

- Confirm the current working directory before running a project-local script.
- Re-check paths that contain spaces or punctuation.
- Use `--help` before guessing CLI flags.
- Keep shell commands fixed and reviewed.
- Refactor top-level side effects out of importable modules.
- Treat Tk-based utilities as GUI work, not headless smoke work.
