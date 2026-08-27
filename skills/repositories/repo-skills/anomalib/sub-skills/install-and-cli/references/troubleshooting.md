# Troubleshooting

## Purpose

Read this when CLI help shrinks unexpectedly, a config file targets the wrong class path, or install/export flags do not behave as expected.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `anomalib -h` only shows `install` | The runtime stack is incomplete and the CLI fell back to the install-only path. | Reinstall with `uv pip install "anomalib[cpu]"` or `pip install "anomalib[cpu]"`, then rerun the help smoke script. |
| `To use other subcommand using \`anomalib install\`` appears in help | The subcommands that depend on the main runtime could not be imported. | Treat this as an installation problem, not a docs problem. Reinstall with `uv pip install "anomalib[cpu]"` or `pip install "anomalib[cpu]"`, then rerun `scripts/check_cli_help.sh`. |
| `anomalib install --option core` still leaves `torch` unavailable | The CLI install option is an add-on bundle, not a backend selector. | Use a direct package install such as `pip install "anomalib[cpu]"` or `pip install -e ".[cpu]"`. |
| `anomalib install --option openvino` does not give a runnable CPU stack by itself | OpenVINO bundles are optional packages, not the CPU wheel set. | Install `anomalib[cpu,openvino]` or `pip install -e ".[cpu,openvino]"` when you need a fresh environment. |
| `unknown option --data_path` or `--datamodule.class_path` | An older shell example is being reused against the current CLI syntax. | Translate the command to the current `--data` syntax and use fully qualified public class paths. |
| Export help is missing OpenVINO flags or `openvino` imports fail | The OpenVINO extra is missing or the environment is not importing the optional stack. | Install `anomalib[cpu,openvino]` or add `openvino` to an editable source install, then rerun the CLI smoke helper. |
| A config file selects the right subcommand but the wrong data class path | The `class_path` or `init_args` entry in the config is wrong, or the config shape does not match the subcommand. | Inspect the merged config with `--print_config`, then fix the public class path and init arguments. |
| `benchmark` is missing from help | The pipeline module is not importable in the current environment. | Confirm the pipeline package imports cleanly; if the command is still absent, route the user to the sibling pipeline sub-skill and the relevant install path. |
| `anomalib train -h -v` does not show the expected quick-start panel | The help formatter is not seeing the right subcommand or the CLI is too incomplete to render the richer help. | Rerun `scripts/check_cli_help.sh` and confirm the runtime import stack before debugging the formatter. |

## Recovery sequence

1. Run [scripts/check_cli_help.sh](../scripts/check_cli_help.sh).
2. Check whether `torch`, `lightning`, and `anomalib` import in the target environment.
3. Reinstall with the correct package extra if the runtime stack is incomplete.
4. Use [references/cli-reference.md](cli-reference.md) to translate stale examples into the current CLI syntax.
5. If the issue is really about benchmark workflow details, hand off to the sibling pipeline sub-skill.

## Notes

- The `install` subcommand's `-v` flag is installer logging, not help verbosity.
- The current predict CLI uses `--data`; treat `--data_path` as a legacy example, not the canonical syntax.
- `anomalib install` is useful for add-on bundles, but it is not the first step for backend selection or bootstrapping a new environment.
