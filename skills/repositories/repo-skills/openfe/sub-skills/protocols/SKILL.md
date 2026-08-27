---
name: protocols
description: "Choose and configure OpenFE protocol classes, default settings,
  ProtocolDAG creation, API execution boundaries, OpenMM backend settings, and
  simulation failure modes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# OpenFE Protocols

Use this sub-skill when the task is about selecting an OpenFE protocol class, customizing protocol settings before construction, creating `Transformation` or `ProtocolDAG` objects, setting OpenMM backend options, or diagnosing protocol-level simulation failures.

## Route Tasks

- Choose among `RelativeHybridTopologyProtocol`, `AbsoluteBindingProtocol`, `AbsoluteSolvationProtocol`, `SepTopProtocol`, and `PlainMDProtocol`; see [protocol reference](references/protocol-reference.md).
- Inspect and edit `default_settings()` safely before protocol construction, including `protocol_repeats`, lambda/window settings, sampling lengths, output/checkpoint settings, OpenMM platform settings, and optional `_adaptive_settings()` caveats; see [settings and execution](references/settings-and-execution.md).
- Create API-side work with `Transformation.create()` or `protocol.create(...)`, understand what a `ProtocolDAG` contains, and know when `execute_DAG` actually runs expensive simulations; see [settings and execution](references/settings-and-execution.md).
- Print protocol default settings without creating systems or running simulations using [the defaults inspector](scripts/inspect_protocol_defaults.py).
- Troubleshoot wrong protocol topology, immutable protocol/settings surprises, invalid OpenMM settings, CUDA/PTX/platform issues, optional parameterization packages, analysis warnings, checkpoint/resume boundaries, and wall-time interruptions; see [troubleshooting](references/troubleshooting.md).

## Safe Operating Rules

- Treat `execute_DAG`, `openfe quickrun`, and any protocol `create(...)` followed by execution as expensive and potentially file-writing; inspect settings and construct objects only when the user wants API planning.
- Customize the `Settings` object before constructing the protocol. If a protocol already exists, rebuild a new protocol from a copied or fresh settings object instead of mutating the existing protocol.
- Prefer `default_settings()` for a known baseline. Use `_adaptive_settings()` only when the protocol documents it, the required `ChemicalSystem` and mapping inputs are available, and the user accepts that the method is experimental.
- Use the bundled defaults inspector for safe defaults discovery; it imports protocol classes and serializes settings, but it never builds chemical systems, submits jobs, runs OpenMM, or downloads data.
- Keep protocol guidance separate from execution orchestration: CLI command syntax and scheduler command generation belong in `../cli-workflows/SKILL.md`, and post-run estimates or gathered tables belong in `../results-analysis/SKILL.md`.

## Boundary Handoffs

- Ligand/protein/solvent loading, `ChemicalSystem` construction, atom mapping, and ligand-network planning belong in `../network-planning/SKILL.md`.
- CLI flags, `openfe quickrun`, resume command syntax, repeat-safe shell/Slurm command generation, and gather command selection belong in `../cli-workflows/SKILL.md`.
- Result JSON decoding, `ProtocolResult.get_estimate()`, uncertainty interpretation, plots, and network result aggregation belong in `../results-analysis/SKILL.md`.
