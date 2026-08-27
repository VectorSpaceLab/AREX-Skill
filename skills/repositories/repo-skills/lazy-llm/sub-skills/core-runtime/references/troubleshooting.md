# Core Runtime Troubleshooting

## `lazyllm --help` exits with an error

This is expected for the simple dispatcher. Use concrete command families such as `lazyllm skills list`, or inspect the command table in this sub-skill.

## Base import succeeds but workflow import fails

If `import lazyllm` works but `from lazyllm.tools import Document` fails with a dependency list, install the owning optional extra. Do not reinstall the base package first.

```bash
lazyllm install rag
python ../../scripts/check_lazyllm_env.py --require-rag
```

## Config values look stale

- Check whether a namespace context is active.
- Check whether the environment variable has the correct prefix, such as `LAZYLLM_GPU_TYPE` or a namespaced prefix.
- Call `lazyllm.config.refresh()` after changing environment variables outside a namespace.
- Remember that empty strings can fall back to defaults for configured keys.

## Component registration is missing an attribute

- Confirm that the group exists; call `comp_register.new_group("name")` before registering functions if the group is not created by a `ComponentBase` subclass.
- Check normalized names: tests verify lowercase aliases and capitalization-preserving aliases for component names.
- Avoid duplicate global registration names in long-lived Python processes.

## CLI command mutates state

`skills`, `review`, deployment, and service commands can create files, inspect git state, start services, or contact remotes. Use `skills list` for a safe CLI smoke. Ask before running commands that post reviews, start servers, install packages, or delete/import skills.

## Editable source checkout builds but optional imports fail

An editable install only proves the base package and native extension build path. Optional dependency checks still run at import time for groups such as RAG and advanced agents. Install the exact extra and rerun the bundled smoke script.
