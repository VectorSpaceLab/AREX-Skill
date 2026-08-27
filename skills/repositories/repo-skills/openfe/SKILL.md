---
name: openfe
description: "Use OpenFE for alchemical free energy setup, network planning,
  protocol configuration, CLI execution, and result analysis workflows in
  molecular simulation campaigns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# OpenFE

Use this repo skill when a task involves OpenFE, Open Free Energy, alchemical free energy calculations, RBFE/RHFE, ABFE/AHFE, SepTop, OpenMM-backed protocol setup, `openfe` CLI workflows, or post-run OpenFE result analysis.

OpenFE is a Python package and CLI for planning and executing alchemical free energy calculations. Keep future-agent work safe by separating planning, protocol configuration, execution commands, and result interpretation.

## Start Here

1. Read [Repository Provenance](references/repo-provenance.md) before deciding whether this skill matches a current checkout or should be refreshed.
2. Read [Installation and Environment](references/installation-and-environment.md) for public install routes, import checks, Python support, and OpenMM/GPU environment notes.
3. Run or adapt [check_openfe_environment.py](scripts/check_openfe_environment.py) for a safe local diagnostic that does not run simulations.
4. Use [Troubleshooting](references/troubleshooting.md) for cross-cutting install/import/OpenMM/CUDA/JAX/logging failures.
5. Route the actual task to one of the sub-skills below.

## Route by Task

- Use [network-planning](sub-skills/network-planning/SKILL.md) for components, ligand/protein/solvent inputs, atom mapping, ligand networks, RBFE/RHFE planning, mapper/scorer choices, and pre-execution data validation.
- Use [protocols](sub-skills/protocols/SKILL.md) for selecting `RelativeHybridTopologyProtocol`, `AbsoluteBindingProtocol`, `AbsoluteSolvationProtocol`, `SepTopProtocol`, or `PlainMDProtocol`; editing settings; understanding `Transformation`, `ProtocolDAG`, `execute_DAG`; and OpenMM backend settings.
- Use [cli-workflows](sub-skills/cli-workflows/SKILL.md) for `openfe` command routing, `plan-rbfe-network`, `plan-rhfe-network`, `quickrun`, `charge-molecules`, `fetch`, `test`, repeat-safe command generation, resume behavior, and command-line troubleshooting.
- Use [results-analysis](sub-skills/results-analysis/SKILL.md) for result JSON decoding, `estimate` / `uncertainty`, `ProtocolResult` methods, `gather`, `gather-abfe`, `gather-septop`, repeat folders, TSV interpretation, storage metadata, and partial/failed result diagnosis.

## Safe Defaults

- Prefer read-only inspection and command construction before execution. `openfe quickrun`, full planning commands, charge generation, `fetch`, and long tests can create files, download data, or run expensive simulation work.
- Use API-side planning for interactive or programmatic workflows; use CLI-side planning when the desired output is a directory of transformation JSONs for `quickrun`.
- Treat OpenFE components, ligand networks, protocols, transformations, and results as provenance-sensitive objects. Rebuild corrected objects rather than mutating existing ones in place.
- Keep repeat execution paths unique. Reusing the same `quickrun` output file or work directory across repeats risks overwrite or resume-cache confusion.
- Preserve physical units when reporting free energies and uncertainties.

## Minimal Checks

After installing OpenFE in a user environment, start with:

```bash
python - <<'PY'
import openfe, openfecli
print(openfe.__version__)
print(openfecli.__version__)
PY
openfe --help
```

For deeper non-mutating checks, run:

```bash
python scripts/check_openfe_environment.py --json
```

## Common Handoffs

- Planning produced transformation JSONs and the user wants to run them: go from [network-planning](sub-skills/network-planning/SKILL.md) to [cli-workflows](sub-skills/cli-workflows/SKILL.md).
- Planning found charged transformations or protocol-repeat concerns: go from [network-planning](sub-skills/network-planning/SKILL.md) to [protocols](sub-skills/protocols/SKILL.md), then back to [cli-workflows](sub-skills/cli-workflows/SKILL.md) for commands.
- `quickrun` finished or failed and the user has result files: go from [cli-workflows](sub-skills/cli-workflows/SKILL.md) to [results-analysis](sub-skills/results-analysis/SKILL.md).
- Gather output looks incomplete: use [results-analysis](sub-skills/results-analysis/SKILL.md) first, then route missing-input or failed-execution causes to [cli-workflows](sub-skills/cli-workflows/SKILL.md) or [protocols](sub-skills/protocols/SKILL.md).

## What Not to Do

- Do not run simulations, submit scheduler jobs, download tutorial data, or execute long tests just to answer a planning or diagnostic question.
- Do not assume a GPU warning means OpenMM simulation is on CPU; distinguish OpenMM platform settings from JAX/PyMBAR analysis warnings.
- Do not tell users to inspect original repository docs or tests as part of this runtime skill; use the bundled references and scripts here.
