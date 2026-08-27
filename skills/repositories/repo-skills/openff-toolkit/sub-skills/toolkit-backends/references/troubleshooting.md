# Toolkit Backend Troubleshooting

## Quick Diagnosis

1. Run `python scripts/check_toolkit_backends.py --json` to see which wrappers are importable, instantiable, and globally registered.
2. Compare the requested file format or charge method with `references/backend-reference.md`.
3. If a method fails through a registry, inspect the `ValueError` text. It lists available toolkits and wrapper-specific errors collected during registry iteration.
4. Prefer fixing the explicit `toolkit_registry=` argument before mutating `GLOBAL_TOOLKIT_REGISTRY`.

## Missing RDKit

Symptoms:

- Import/instantiation reports `RDKitToolkitWrapper available=False`.
- The startup warning says no basic cheminformatics toolkit is available.
- SMILES, SMARTS, SDF/MOL/SMI I/O, conformer generation, or AmberTools wrapper setup fails.

Cause and fix:

- RDKit is the primary free basic cheminformatics backend. Install RDKit from conda-forge or install the full `openff-toolkit` package rather than a base-only package.
- AmberTools wrapper also depends on RDKit because it uses RDKit SDF I/O internally, so installing AmberTools alone is not enough for `AmberToolsToolkitWrapper`.

## Missing OpenEye or OpenEye License

Symptoms:

- `OpenEyeToolkitWrapper.is_available()` is false.
- Instantiation raises `ToolkitUnavailableException` saying OpenEye toolkits are not installed.
- Instantiation raises `LicenseError` saying OpenEye is installed but not licensed.
- `am1bccelf10`, `am1elf10`, OpenEye MOL2/OEB workflows, or OpenEye-specific canonicalization cannot run.

Cause and fix:

- OpenEye requires both `openeye-toolkits` and a valid license. Install the package from the OpenEye channel and configure licensing according to OpenEye instructions.
- If the user does not need OpenEye-specific behavior, choose RDKit for basic open-source chemistry or AmberTools plus RDKit for free AM1-BCC style charges.
- Do not silently fall back from OpenEye to RDKit when the requested behavior is license-specific; explain the expected behavior change.

## Missing AmberTools or `antechamber`

Symptoms:

- `AmberToolsToolkitWrapper.is_available()` is false.
- Instantiation raises `ToolkitUnavailableException` for AmberTools.
- Charge assignment raises `AntechamberNotFoundError`.
- `am1bcc`, `am1-mulliken`, or AM1-Wiberg fractional bond order workflows fail in a free-only stack.

Cause and fix:

- AmberTools wrapper requires the `antechamber` executable on `PATH` and RDKit availability.
- Install AmberTools from conda-forge and confirm the runtime shell exposes `antechamber`.
- Use `ToolkitRegistry([AmberToolsToolkitWrapper, RDKitToolkitWrapper])` for AM1-BCC charges; RDKit alone supports only `mmff94` and `gasteiger`.

## Missing OpenFF NAGL

Symptoms:

- `NAGLToolkitWrapper.is_available()` is false.
- The wrapper reports no supported charge methods.
- `assign_partial_charges` raises for a blank or missing model name.

Cause and fix:

- Install OpenFF NAGL and the relevant NAGL model package or provide a model file.
- NAGL does not have a default model in the wrapper; pass a model filename/path as `partial_charge_method`.
- `use_conformers` and `strict_n_conformers` are ignored by NAGL because charges are graph-based, not coordinate-based.

## Unsupported File Format

Symptoms:

- File loading/writing raises `ValueError`, `OSError`, or a registry `ValueError` saying no wrapper can provide `from_file`/`to_file` for the arguments.
- RDKit-only registry fails on `MOL2`, `PDB` reading, `OEB`, `INCHI`, or other OpenEye-oriented formats.

Cause and fix:

- Match the format to wrapper support. RDKit reads `SDF`, `MOL`, and `SMI`; it writes `SDF`, `MOL`, `SMI`, `PDB`, and `TDT`.
- OpenEye covers broad formats including `MOL2`, `PDB`, `OEB`, `INCHI`, `INCHIKEY`, `FASTA`, `CSV`, `SDF`, and `SMI`, but requires installation and licensing.
- AmberTools and Built-in wrappers are not general file I/O providers in OpenFF Toolkit.

## Unsupported Charge Method

Symptoms:

- `ChargeMethodUnavailableError` from a wrapper.
- Registry `ValueError` with messages such as the method is not available from `RDKitToolkitWrapper`, `OpenEyeToolkitWrapper`, `AmberToolsToolkitWrapper`, or the built-in toolkit.

Resolution map:

- `mmff94`, `gasteiger`: RDKit or OpenEye; AmberTools also supports `gasteiger`.
- `am1bcc`, `am1-mulliken`: OpenEye or AmberTools; AmberTools is the free route but requires `antechamber` and RDKit.
- `am1bccnosymspt`, `am1elf10`, `am1bccelf10`: OpenEye only among the bundled wrappers.
- `zeros`, `formal_charge`: Built-in wrapper only; useful for placeholders/testing, not general physical charges.
- NAGL model charges: NAGL wrapper with an explicit model filename/path.

If the task asks for AM1-BCC in an RDKit-only environment, do not claim RDKit can do it. Recommend installing AmberTools for the smallest free stack, or OpenEye when OpenEye-specific AM1/ELF behavior is required.

## Registry Resolution Failures

Symptoms:

- `ToolkitRegistry.resolve("method")` raises `NotImplementedError`.
- `ToolkitRegistry.call("method", ...)` raises `ValueError` despite wrappers being registered.
- Behavior changes unexpectedly after editing `GLOBAL_TOOLKIT_REGISTRY`.

Cause and fix:

- The method may not exist on any registered wrapper, or every wrapper that implements it rejected the specific arguments.
- Put the desired wrapper first. Registry precedence matters: the first successful wrapper wins.
- Construct a fresh `ToolkitRegistry([...])` for reproducible calls instead of depending on environment-dependent global registration.
- If temporarily changing global behavior, use `toolkit_registry_manager(registry)` and keep the context small.
- Avoid assigning a new object to `GLOBAL_TOOLKIT_REGISTRY`; source docs warn this is easy to get wrong and may fail silently.

## No Basic Cheminformatics Toolkit Warning

Symptoms:

- Importing toolkit modules prints a warning that no basic cheminformatics toolkit is available.
- `GLOBAL_TOOLKIT_REGISTRY` contains only non-basic or built-in wrappers.

Cause and fix:

- OpenFF Toolkit expects at least one basic toolkit from `RDKitToolkitWrapper` or `OpenEyeToolkitWrapper` for SMARTS matching and file I/O.
- Install RDKit for the smallest open-source fix, or OpenEye if the user already has a license and needs OpenEye behavior.

## OpenEye vs RDKit Behavior Caveats

OpenEye and RDKit can differ in canonical SMILES strings, hydrogens, stereochemistry perception, tautomer/protomer enumeration, PDB hierarchy metadata, and edge-case molecule parsing. Tests in the source tree intentionally account for differences such as distinct canonical SMILES and OpenEye-specific hierarchy metadata.

When the user compares outputs:

- First confirm which wrapper produced each result.
- Re-run with explicit `toolkit_registry=RDKitToolkitWrapper()` or `toolkit_registry=OpenEyeToolkitWrapper()` instead of relying on the global registry.
- Treat differences as backend behavior until proven otherwise; do not normalize them away without checking the downstream scientific requirement.

## Common Safe Responses

- "Your global registry has RDKit and Built-in only, so OpenEye/AmberTools/NAGL-specific charge methods will fail until those optional dependencies are installed."
- "For `MOL2` reading, RDKit is not enough in this wrapper; install/configure OpenEye or convert to SDF/SMI/MOL before using RDKit."
- "For free AM1-BCC charges, install AmberTools and use `ToolkitRegistry([AmberToolsToolkitWrapper, RDKitToolkitWrapper])`; RDKit-only supports `mmff94` and `gasteiger`."
- "For temporary backend changes, wrap the block in `toolkit_registry_manager(...)`; for most calls, pass an explicit `toolkit_registry=` argument."
