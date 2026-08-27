# Contributor Guidance

- Keep changes scoped to the relevant WOD module and run focused tests first.
- Include clear reproduction information when reporting issues: command, environment, Bazel output, TensorFlow/package versions, and whether full datasets or optional dependencies are involved.
- For hard-to-diagnose repository failures, capture a verbose Bazel log with `--test_output=errors --subcommands --verbose_failures --sandbox_debug --keep_going`.
- Respect license boundaries: the root repository is Apache-licensed except WDL-limited subdirectories, which carry additional license and patent terms.
- Do not modify generated skill artifacts when making upstream code changes unless the task is refreshing this repo skill.
