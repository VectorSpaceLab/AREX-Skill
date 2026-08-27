# Evaluation API and CLI reference

## Python API

MatterGen 1.0.3 exposes `mattergen.evaluation.evaluate.evaluate`:

```python
from mattergen.evaluation.evaluate import evaluate

metrics = evaluate(
    structures=structures,
    relax=True,
    energies=None,
    reference=None,
    structure_matcher=DefaultDisorderedStructureMatcher(),
    save_as=None,
    save_detailed_as=None,
    potential_load_path=None,
    device="cuda",
    structures_output_path=None,
    energy_correction_scheme=MaterialsProject2020Compatibility(),
)
```

Parameters:

| Parameter | Meaning and contract |
| --- | --- |
| `structures` | Non-empty list of pymatgen `Structure` objects. With relaxation, these are also the originals used for relaxation RMSD. |
| `relax` | If true, call MatterSim `relax_structures`; if false, use supplied structures as final structures. |
| `energies` | External total energies, one per structure, for `relax=False`. Passing it with `relax=True` raises `ValueError`. These are total energies, not energies per atom. |
| `reference` | `ReferenceDataset` used for matching and hull metrics. `None` selects an internal MP2020 or TRI2024 preset based on correction type. |
| `structure_matcher` | Ordered or disordered matcher. The default is `DefaultDisorderedStructureMatcher()`. |
| `save_as` | JSON aggregate metrics path. Parent directories are created by the evaluator. |
| `save_detailed_as` | Per-entry table serialized through `monty`; despite the name, it is not the same aggregate JSON shape. |
| `potential_load_path` | Local MatterSim checkpoint passed to `Potential.from_checkpoint`; no wrapper download is performed. `None` uses MatterSim's default resolution behavior. |
| `device` | MatterSim device, typically `cuda`, `cpu`, `mps`, or a CUDA-indexed device. The default is computed from the installed package at import time, although the documented source signature displays the current device. |
| `structures_output_path` | EXTXYZ path written by MatterSim relaxation. It is only meaningful for `relax=True`; no separate output is generated in no-relax mode. |
| `energy_correction_scheme` | Pymatgen `Compatibility` object. Source CLI choices are MP2020 and TRI2024. The reference must use the same convention. |

The result is a dictionary of metric name to scalar value. The implementation
computes every metric whose required capability is available. If a reference
lacks terminal data for a sampled chemical system, the energy capability can be
omitted while structure metrics still return.

## Structure loaders

`mattergen.common.utils.eval_utils.load_structures(Path)` accepts:

- a path whose suffix is exactly `.xyz` or `.extxyz`: ASE reads all frames;
- a path whose suffix is `.zip`: it is extracted to a temporary directory and
  files are read from there;
- a directory: each direct child is considered in `os.listdir` order;
- anything else raises `ValueError`.

Directory files ending in lowercase `.cif` are read with
`Structure.from_file`; lowercase `.xyz` and `.extxyz` files are read by ASE
with frame index `0`, so each directory XYZ file is assumed to contain one
structure. CIF parse failures are logged and skipped. A ZIP follows the same
extension rules after extraction. ZIP path traversal is not part of the source
loader's safety contract; use trusted archives.

## Matchers

`DefaultOrderedStructureMatcher` wraps pymatgen matching with default
`ltol=0.2`, `stol=0.3`, `angle_tol=5`, primitive-cell and scale normalization,
and no supercell/subset search. It groups ordered dataset comparisons by
reduced formula.

`DefaultDisorderedStructureMatcher` additionally uses
`OrderDisorderElementComparator`, allows supercells/subsets, and handles
partial occupancies and substitution-aware ordered-vs-disordered matches. Its
substitution heuristic uses relative atomic-radius difference `<= 0.3` and
electronegativity difference `<= 1.0`; disordered dataset comparisons group by
chemical system. Formal space-group labels are not used as a final equality
criterion. The evaluator asserts that a disordered input/reference combination
uses a disordered matcher.

## CLI adapter

The original console entry point is `mattergen-evaluate`, backed by
`mattergen.scripts.evaluate` and Python Fire. The safe bundled adapter uses
explicit argparse types and validates before importing heavy MatterGen
modules. Its option names and defaults are:

```text
--structures_path PATH                 required
--relax {True,False}                   True
--energies_path PATH                   None
--structure_matcher {ordered,disordered} disordered
--save_as PATH                         None
--save_detailed_as PATH                None
--potential_load_path PATH             None
--reference_dataset_path PATH          None
--device DEVICE                        auto
--structures_output_path PATH          None
--energy_correction_scheme {MP2020,TRI2024} MP2020
```

The adapter maps `--structure_matcher` to the two default matcher classes,
loads `--energies_path` with `numpy.load`, deserializes a supplied reference
with `LMDBGZSerializer`, maps MP2020 to
`MaterialsProject2020Compatibility()` and TRI2024 to
`TRI110Compatibility2024()`, calls the package API, and prints JSON.
