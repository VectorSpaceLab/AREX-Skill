# Workflow Parser Reference

Dipy commands share one parser path: project script name -> `dipy.workflows.cli.run()` -> `dipy.workflows.cli.cli_flows` -> workflow class -> `dipy.workflows.flow_runner.run_flow()` -> `IntrospectiveArgumentParser`. This means help text and CLI arguments are generated from each workflow's `run` method signature and NumPy-style docstring.

## Dispatch Model

- Each `dipy_*` project script points to `dipy.workflows.cli:run`.
- `run()` reads the executable name from `sys.argv[0]` and looks it up in `cli_flows`.
- `cli_flows` maps command names to `(module_name, class_name)` tuples.
- The module is imported, the workflow class is instantiated, and `run_flow()` builds the parser.
- Unknown script names exit with an error and list available flows.
- Some aliases inject extra parser arguments before execution:
  - `dipy_fit_dsid` injects `--remove_convolution` default behavior.
  - `dipy_fit_msmtcsd` injects `--use_msmt` default behavior.
  - `dipy_fit_csa`, `dipy_fit_opdt`, and `dipy_fit_qball` inject a `method` default.
- `dipy_sh_convert_mrtrix` warns that it is deprecated and points to `dipy_convert_sh`.

## Shared Flags Added To Every Workflow CLI

| Flag | Default | Meaning | Guidance |
| --- | --- | --- | --- |
| `--help` / `-h` | argparse default | Show command-specific parser table | Run before constructing a new command. |
| `--version` | current Dipy version | Print `DIPY <version>` | Useful for environment handoffs. |
| `--force` | `False` | Allow output overwrite | Use only when existing outputs are expected to be replaced. |
| `--out_strat` | `absolute` | Output creation strategy | Keep default unless reproducing a documented workflow needing another strategy. |
| `--mix_names` | `False` | Prepend mixed input names to output names | Useful when processing multiple inputs with potentially colliding outputs. |
| `--log_level` | `INFO` | Logger level | Use `DEBUG` for parser/workflow diagnosis; keep `INFO` in recipes. |
| `--log_file` | empty string | Optional log file path | Set for reproducibility when commands are part of a pipeline. |

## How Arguments Are Derived

`IntrospectiveArgumentParser.add_workflow()` inspects the workflow instance's `run` method.

- The method signature supplies argument names, order, and Python defaults.
- The NumPy-style docstring `Parameters` section supplies argument type text and help descriptions.
- Arguments without defaults are positional unless their names start with `out_`.
- Arguments with defaults become `--optional` flags.
- Names containing `out_` are grouped as output arguments even when positional/optional classification differs.
- A docstring/signature parameter count mismatch raises a parser construction error.
- Docstring types drive argparse conversion:
  - text containing `str` -> `str`
  - text containing `int` -> `int`
  - text containing `float` -> `float`
  - text containing `bool` -> boolean handling
  - text containing `tuple` -> parsed as string for CLI purposes
  - text containing `variable` -> `nargs` behavior
- Optional booleans are store-true flags; positional booleans are parsed as integer choices `0` or `1`.
- The literal strings `None` and `none` are converted to Python `None` by `get_flow_args()`.
- RST roles and some LaTeX markup are stripped from help text for terminal display.

## Variable-Length Arguments

The parser treats docstring types containing `variable` as multi-value inputs.

- Optional variable arguments use `nargs="*"`; passing the flag without values can produce an empty list.
- Positional variable arguments use `nargs="+"`.
- More than one variable positional argument in one workflow is rejected because argparse cannot split the values reliably.
- When translating examples, preserve quoting and shell glob behavior; the workflow receives expanded shell arguments, not raw globs unless the shell leaves them unexpanded.

## Output Behavior

Dipy workflows inherit `Workflow.get_io_iterator()` and output-overwrite handling.

- Prefer explicit `--out_dir` in examples so outputs do not land in the current directory unexpectedly.
- Many workflows default `out_dir` to the current directory when the run signature default is `""`, `" "`, or `"."`.
- Output filenames are usually `out_*` parameters; set them explicitly when downstream steps refer to the files.
- If an output file already exists, the workflow logs the duplicates and does not continue unless `--force` is set.
- `--mix_names` can help avoid collisions when an input pattern expands to multiple files.
- `--out_strat absolute` is the default output strategy; do not change it unless you have checked the workflow's IO behavior.

## Sub-Workflow Arguments

Some workflows combine smaller workflows. `add_sub_flow_args()` exposes only optional inputs from sub-flows and prefixes them with the sub-flow short name.

- Sub-flow flags appear as `--short_name.parameter` in help.
- `run_flow()` strips those prefixed keys from the main argument dictionary and passes them into `flow.set_sub_flows_optionals()`.
- When troubleshooting a combined workflow, search help for argument groups named after sub-flows.

## Safe Help And Version Probes

Use probes before running data-modifying commands:

```bash
python scripts/dipy_cli_probe.py --format text
python scripts/dipy_cli_probe.py --check-help dipy_info dipy_fit_dti --timeout 8 --format json
COMMAND --version
COMMAND --help
```

`--help` is usually non-destructive, but it still imports the workflow module. Optional visualization or neural-network commands may fail help probes if optional dependencies are missing or if import-time backend checks are strict. Treat that as environment readiness information.

## Parser Debug Checklist

- If help does not show a flag you expected, inspect `COMMAND --help`; Dipy exposes workflow `run` parameters, not every lower-level API keyword.
- If a value parses as a string instead of a tuple, remember tuple-typed docstring parameters are accepted as strings and interpreted by workflow code.
- If `None` is needed, pass `None` or `none`, not an empty string.
- If an optional variable flag produces an empty list, provide values after the flag or omit the flag to use the workflow default.
- If a command unexpectedly refuses to overwrite outputs, add `--force` only after confirming the files are safe to replace.
- If command behavior differs from docs, list installed flows and run `--version`; local script tables and installed package versions can differ.
