# English Web UI Reference

## Entry point and working-directory behavior

The English UI is implemented as `owl/webapp.py` and creates a Gradio app in
`create_ui()`, with `main()` setting up logging and launching it. The module
imports `run_society` using `from utils import run_society`, not a package-
relative import. Run it in the script/project layout expected by that import;
plain `import owl.webapp` from an unrelated directory may fail even though the
source script works. This is a source behavior to account for in deployment,
not a recommendation to alter `sys.path` globally.

## Request flow

1. `validate_input(question)` rejects empty or whitespace-only questions.
2. `run_owl(question, example_module)` loads dotenv values, rejects a module
   absent from `MODULE_DESCRIPTIONS`, imports `examples.<module>`, and requires
   that module to export `construct_society`.
3. The UI calls `construct_society(question)`, runs the returned society through
   `run_society`, and displays answer, token totals, status, and simplified logs.
4. Model/tool errors are caught and converted to user-visible status text. The
   UI does not make a missing provider key or missing example module valid.

The checked-in module description mapping lists 15 names, while the inspected
`examples/` directory contains only seven `run*.py` modules. Before selecting a
module, run `check_web_ui_config.py --examples-dir <dir> --module <name>`.
Treat a listed-but-missing module as a source/check-out mismatch and choose an
available provider route rather than retrying the same import.

## Environment variable behavior

The UI can create an `.env` if `find_dotenv()` finds none, load values from the
process and file, and save/add/delete values with python-dotenv. Its documented
priority is frontend state first, `.env` second, and system environment last.
`save_env_vars`, `add_env_var`, `delete_env_var`, and the editable environment
table mutate the file and process environment.

Use these controls only when a user has authorized credential-file changes:

- Keep the file private and out of source control.
- Never copy keys into Gradio logs, bug reports, command history, or prompts.
- Use a dedicated environment file for each deployment rather than editing a
  shared account's configuration through the web page.
- Read [workforce-workflows](../../workforce-workflows/SKILL.md) to select the
  provider variables and model capabilities before starting the UI.

## Logs and cancellation

The UI creates a date-stamped log under an `owl/logs` directory, filters chat
agent INFO records for display, and runs work in a background thread. Treat log
content as potentially sensitive model/task output. A stop request is an
application control, not proof that an external browser, provider request, or
file operation was rolled back; inspect external artifacts separately.
