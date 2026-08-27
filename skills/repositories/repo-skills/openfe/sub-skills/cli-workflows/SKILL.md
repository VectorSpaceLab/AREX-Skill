---
name: cli-workflows
description: "Use OpenFE console commands for planning networks, running
  quickrun jobs, gathering outputs, generating charges, fetching examples,
  viewing ligand networks, and testing installations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# OpenFE CLI Workflows

Use this sub-skill when the task is about the `openfe` command line interface: choosing a subcommand, ordering planning/execution/gathering steps, constructing `quickrun` commands, preparing repeat-safe job scripts, or troubleshooting CLI misuse.

## Route Tasks

- Plan RBFE/RHFE campaign files with `openfe plan-rbfe-network` or `openfe plan-rhfe-network`; see [planning and quickrun](references/planning-and-quickrun.md).
- Execute one transformation JSON with `openfe quickrun`, resume interrupted work, or generate shell/Slurm command plans; see [planning and quickrun](references/planning-and-quickrun.md) and [the repeat command helper](scripts/build_quickrun_repeat_commands.py).
- Gather completed result JSONs with `openfe gather`, `openfe gather-abfe`, or `openfe gather-septop`; use this sub-skill for command selection only, then route detailed TSV schemas and result interpretation to `../results-analysis/SKILL.md`.
- Generate charged ligand SDFs with `openfe charge-molecules`, view GraphML ligand networks with `openfe view-ligand-network`, fetch tutorial resources with `openfe fetch`, or run the OpenFE test suite with `openfe test`; see [CLI reference](references/cli-reference.md).
- Debug CLI symptoms such as misplaced global options, missing transformation JSONs, duplicate repeat outputs, malformed YAML, or quickrun cache issues; see [troubleshooting](references/troubleshooting.md).

## Safe Operating Rules

- Prefer help and inspection commands first: `openfe --help`, `openfe <command> --help`, and the bundled command generator with `--help` are safe.
- Treat `openfe quickrun`, planning commands, charge generation, `fetch`, and `openfe test` as potentially expensive or mutating; `openfe test --long` is especially slow. Do not run them unless the user explicitly wants execution.
- Put global options before the subcommand, for example `openfe --log logging.conf quickrun transformation.json -d work -o result.json`.
- Keep planning, execution, and gathering separate: planners write network files and transformation JSONs, `quickrun` runs exactly one transformation JSON, and gather commands summarize completed result JSONs.
- Use unique `-o` result paths and `-d` work directories for repeated quickrun jobs; never reuse the same output path for parallel repeats.

## Boundary Handoffs

- Python object construction, molecule/protein component concepts, atom mapper tradeoffs, and ligand-network topology decisions belong in `../network-planning/SKILL.md`.
- Protocol class settings, OpenMM backend details, protocol repeat semantics beyond CLI flags, and execution internals belong in `../protocols/SKILL.md`.
- Result JSON contents, TSV columns, error propagation, and estimate/uncertainty interpretation belong in `../results-analysis/SKILL.md`.
