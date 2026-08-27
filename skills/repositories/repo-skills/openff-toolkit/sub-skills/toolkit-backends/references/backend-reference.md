# Backend Reference

## Backend Model

OpenFF Toolkit exposes external chemistry functionality through `ToolkitWrapper` classes. Most user-facing APIs accept `toolkit_registry=`, which may be either a single wrapper instance such as `RDKitToolkitWrapper()` or a `ToolkitRegistry` containing wrappers in precedence order.

`ToolkitRegistry.call(method_name, *args, **kwargs)` tries registered wrappers in order and returns the first successful implementation. If no wrapper can provide the requested capability, it raises `ValueError` with the registered wrappers and any collected wrapper errors. `ToolkitRegistry.resolve(method_name)` returns the first registered method with that name and raises `NotImplementedError` if none exists.

`GLOBAL_TOOLKIT_REGISTRY` is built at import time from available wrappers, using preferred source order `NAGLToolkitWrapper`, `OpenEyeToolkitWrapper`, `RDKitToolkitWrapper`, `AmberToolsToolkitWrapper`, `BuiltInToolkitWrapper` where available. In the inspected environment, only `RDKitToolkitWrapper` and `BuiltInToolkitWrapper` were registered globally.

## Wrapper Capability Matrix

| Wrapper | Availability check | Main use | File read formats | File write formats | Charge methods | Install guidance |
| --- | --- | --- | --- | --- | --- | --- |
| `RDKitToolkitWrapper` | Imports `rdkit`; available in inspected environment | Free/open-source basic cheminformatics, SMILES/SDF/MOL/SMI I/O, conformers, SMARTS, many molecule operations | `SDF`, `MOL`, `SMI` | `SDF`, `MOL`, `SMI`, `PDB`, `TDT` | `mmff94`, `gasteiger` | Install RDKit from conda-forge; the full `openff-toolkit` conda package usually includes it |
| `OpenEyeToolkitWrapper` | Requires OpenEye modules and at least one valid OpenEye license; unavailable in inspected environment | Licensed OpenEye cheminformatics, broad file formats, OpenEye AM1-BCC/ELF10 charges, conformers, IUPAC/protomer/tautomer behavior | `CAN`, `CDX`, `CSV`, `FASTA`, `INCHI`, `INCHIKEY`, `ISM`, `MDL`, `MF`, `MMOD`, `MOL2`, `MOL2H`, `MOPAC`, `OEB`, `PDB`, `RDF`, `SDF`, `SKC`, `SLN`, `SMI`, `USM`, `XYC` | Same as read formats | `am1bcc`, `am1-mulliken`, `gasteiger`, `mmff94`, `am1bccnosymspt`, `am1elf10`, `am1bccelf10` | Install `openeye-toolkits` from the OpenEye channel and configure an OpenEye license |
| `AmberToolsToolkitWrapper` | Requires `antechamber` on `PATH` and RDKit availability; unavailable in inspected environment | Free AM1-BCC/AM1-Mulliken/Gasteiger charges and AM1-Wiberg fractional bond orders through AmberTools executables | None exposed directly; uses RDKit SDF I/O internally | None exposed directly; uses RDKit SDF I/O internally | `am1bcc`, `am1-mulliken`, `gasteiger` | Install AmberTools from conda-forge; ensure `antechamber` and RDKit are available |
| `NAGLToolkitWrapper` | Imports `openff.nagl`; unavailable in inspected environment | Graph neural network charges from an explicit NAGL model name/path | None | None | Model filenames discovered from `openff.nagl_models`; no default model | Install OpenFF NAGL and model packages, then pass an explicit model filename/path |
| `BuiltInToolkitWrapper` | Bundled with OpenFF Toolkit | Minimal fallback/testing charges only | None | None | `zeros`, `formal_charge` | No extra dependencies |

## Registry Patterns

### Prefer Explicit Registry Arguments

Use explicit registries for reproducibility and narrow dependency behavior:

```python
from openff.toolkit import Molecule, ToolkitRegistry, RDKitToolkitWrapper, BuiltInToolkitWrapper

rdkit_only = ToolkitRegistry([RDKitToolkitWrapper])
mol = Molecule.from_smiles("CCO", toolkit_registry=rdkit_only)
smiles = mol.to_smiles(toolkit_registry=rdkit_only)
```

Use wrapper instances when a call only needs one backend:

```python
from openff.toolkit import RDKitToolkitWrapper

smiles = mol.to_smiles(toolkit_registry=RDKitToolkitWrapper())
```

### Order Wrappers by Desired Precedence

Put the preferred provider first. For example, a free stack for AM1-BCC charges should place AmberTools before RDKit because RDKit cannot provide AM1-BCC:

```python
from openff.toolkit import ToolkitRegistry, AmberToolsToolkitWrapper, RDKitToolkitWrapper

free_am1bcc = ToolkitRegistry([AmberToolsToolkitWrapper, RDKitToolkitWrapper])
mol.assign_partial_charges("am1bcc", toolkit_registry=free_am1bcc)
```

For OpenEye-specific charge behavior, prefer OpenEye first:

```python
from openff.toolkit import ToolkitRegistry, OpenEyeToolkitWrapper, RDKitToolkitWrapper

openeye_first = ToolkitRegistry([OpenEyeToolkitWrapper, RDKitToolkitWrapper])
mol.assign_partial_charges("am1bccelf10", toolkit_registry=openeye_first)
```

### Temporarily Override the Global Registry

Use `toolkit_registry_manager` only when code paths do not expose `toolkit_registry=` or when a whole block should share the same temporary global registry:

```python
from openff.toolkit import ToolkitRegistry, RDKitToolkitWrapper, BuiltInToolkitWrapper
from openff.toolkit.utils import toolkit_registry_manager

registry = ToolkitRegistry([RDKitToolkitWrapper, BuiltInToolkitWrapper])
with toolkit_registry_manager(registry):
    mol = Molecule.from_smiles("CCO")
```

The context manager deregisters the current global wrappers, registers the temporary wrappers, and restores the original list afterward. Do not assign a new object to `GLOBAL_TOOLKIT_REGISTRY`; modify its contents or use the context manager.

### Mutating a Registry

`register_toolkit()` accepts wrapper classes or instances and instantiates classes if available. With `exception_if_unavailable=False`, unavailable wrappers are skipped instead of raising. `deregister_toolkit()` removes matching wrappers by class or instance and raises if the wrapper is absent.

```python
from openff.toolkit import ToolkitRegistry, RDKitToolkitWrapper, OpenEyeToolkitWrapper

registry = ToolkitRegistry([RDKitToolkitWrapper])
registry.register_toolkit(OpenEyeToolkitWrapper, exception_if_unavailable=False)
registry.deregister_toolkit(RDKitToolkitWrapper)
```

## Choosing the Smallest Optional Dependency

- Basic molecule I/O from `SDF`, `MOL`, or `SMI`, SMILES handling, SMARTS matching, conformer generation, and RDKit-style charges: install/use RDKit.
- `MOL2`, `OEB`, `INCHI`, `INCHIKEY`, `FASTA`, `CSV`, or broad OpenEye file formats: install/use OpenEye and configure a license.
- `am1bcc` or `am1-mulliken` without OpenEye: install/use AmberTools plus RDKit, and confirm `antechamber` is available.
- `am1bccelf10`, `am1elf10`, or OpenEye-specific AM1 charge workflows: install/use OpenEye with license.
- GNN model charges: install/use OpenFF NAGL plus the needed NAGL model package or model file; always pass the explicit model name/path.
- Trivial formal-charge or zero-charge placeholders: the built-in wrapper is enough, but it is not a general cheminformatics backend.

## Common Backend Selection Examples

### RDKit-only registry with AM1-BCC failure explanation

If the user asks why `mol.assign_partial_charges("am1bcc", toolkit_registry=ToolkitRegistry([RDKitToolkitWrapper]))` fails, explain that RDKit supports only `mmff94` and `gasteiger` partial charge methods in this wrapper. For free AM1-BCC, use `ToolkitRegistry([AmberToolsToolkitWrapper, RDKitToolkitWrapper])` after installing AmberTools. For OpenEye AM1-BCC or ELF10 variants, use OpenEye with a valid license.

### File format choice

If `Molecule.from_file(..., file_format="MOL2")` fails with an RDKit-only registry, recommend OpenEye for MOL2 reading or convert the file to SDF/SMI/MOL with a trusted external tool before using RDKit. RDKit wrapper reads `SDF`, `MOL`, and `SMI`; it writes `SDF`, `MOL`, `SMI`, `PDB`, and `TDT`.

### Avoiding OpenEye when reproducibility matters

If a workflow should avoid licensed/proprietary behavior, construct an explicit registry that excludes OpenEye even if it is installed:

```python
from openff.toolkit import ToolkitRegistry, RDKitToolkitWrapper, AmberToolsToolkitWrapper, BuiltInToolkitWrapper

free_only = ToolkitRegistry([RDKitToolkitWrapper, AmberToolsToolkitWrapper, BuiltInToolkitWrapper])
```

### Inspecting the active environment

Use the bundled helper:

```shell
python scripts/check_toolkit_backends.py --json
python scripts/check_toolkit_backends.py --require rdkit builtin --json
```

It imports wrappers safely, reports availability, global registry contents, supported formats, supported charge methods where instantiation succeeds, and exits nonzero only when `--require` names an unavailable wrapper.
