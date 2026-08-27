---
name: cli-and-containers
description: "Orchestrate safe pySCENIC CLI, command-file, container, and HPC
  workflows across GRN, motif pruning, and AUCell."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# CLI And Containers

Use this sub-skill when a task needs an end-to-end pySCENIC command plan, container invocation, `@args.txt` command file, resource checklist, or operational decision between local, container, and scheduler-backed execution.

## Read First

- [CLI reference](references/cli-reference.md): subcommand map, full `grn -> ctx -> aucell` templates, `@args.txt` rules, output suffix choices, and resource checks.
- [Container and HPC reference](references/container-and-hpc.md): Docker, Podman, Singularity, Apptainer, mount planning, image variants, Dask cluster constraints, and scheduler-safe planning.
- [Troubleshooting](references/troubleshooting.md): missing resources, path and mount mismatch, `@args.txt` quoting, output extension mistakes, import/help failures, Dask/HPC filesystems, and scanpy extras.
- [CLI smoke helper](scripts/pyscenic_cli_smoke.py): safe installed-command help checks, tiny optional fixture writer, and command-template generator.

## Route By Task

- **End-to-end CLI run plan**: start with the CLI reference to assemble `pyscenic grn`, optional `pyscenic add_cor`, `pyscenic ctx`, and `pyscenic aucell` commands.
- **Container command plan**: use the container and HPC reference before writing Docker, Podman, Singularity, or Apptainer commands so every host path is mounted consistently.
- **Operational smoke check**: run the bundled helper with `--check-help` before expensive runs; add `--emit-template` or `--write-args-dir` to create dry-run-ready command templates.
- **Phase-specific depth**: route GRNBoost2/GENIE3 internals to [network inference](../network-inference/SKILL.md), motif database pruning and regulon formats to [motif pruning and regulons](../motif-pruning-and-regulons/SKILL.md), and AUCell scoring or binarization details to [AUCell and binarization](../aucell-and-binarization/SKILL.md).

## Safe Starting Point

```bash
python scripts/pyscenic_cli_smoke.py --check-help --emit-template
```

The helper only probes command help and prints templates by default. It does not download ranking databases, run GRN inference, launch motif pruning, score AUCell, start containers, or mutate existing files unless `--write-args-dir` or `--make-fixtures` is explicitly supplied.
