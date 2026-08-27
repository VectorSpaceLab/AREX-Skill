---
name: nuclear-data-depletion
description: "Use OpenMC nuclear-data libraries, cross_sections.xml indexes,
  depletion chains, MGXS/MicroXS workflows, depletion integrators, restarts, and
  data-dependent validation with explicit runtime gates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Nuclear data and depletion

Use this route when the task involves continuous-energy or multigroup nuclear
data, ENDF/ACE/HDF5 conversion, a depletion or activation chain, MGXS/MicroXS,
transport-independent depletion, depletion results, or a restart/decay/R2S
workflow. This route explains the data and depletion contract; it does not
replace the model, executable, or result-reader routes.

## Triage before changing code or running anything

1. **Identify the requested artifact.** Is it a data index, a referenced HDF5
   library, a depletion-chain XML, an MGXS library, a MicroXS table, a model
   input, or a `depletion_results.h5` file? Do not treat one as another.
2. **Check the smallest gates.** A Python API/XML check can work with no
   transport data. A continuous-energy transport or coupled depletion run
   needs a native executable and a usable cross-section index. A coupled
   depletion operator additionally needs the native shared library because it
   uses `openmc.lib`. An independent operator needs a valid chain and supplied
   flux/MicroXS data; its numerical solve can be transport-free, but import and
   operator behavior still depend on the installed package and, for some
   helpers, the native binding.
3. **Validate paths before blaming physics.** Run the bundled, read-only XML
   diagnostic with an explicit index path:
   `python path/to/validate_data_paths.py --cross-sections /path/to/cross_sections.xml`.
   It never downloads data. Read [data-formats.md](references/data-formats.md)
   for path resolution and HDF5 checks.
4. **Choose the workflow.** Read
   [depletion-and-mgxs-workflows.md](references/depletion-and-mgxs-workflows.md)
   for chain/operator/integrator/MGXS choices. Read
   [troubleshooting.md](references/troubleshooting.md) before repairing a
   failure or retrying a data-dependent run.

## Runtime gates and honest claims

Report these independently rather than collapsing them into “OpenMC works”:

- **API gate:** `import openmc`, `openmc.data`, and the requested pure-Python
  classes/signatures work. This supports object construction, XML parsing,
  chain/MicroXS shape checks, and some result-file readers.
- **Native-library gate:** `import openmc.lib` loads `libopenmc.so` (or the
  platform equivalent). It is required for C API/library mode and the
  transport-coupled depletion operator. Base Python import can succeed while
  this gate fails.
- **Executable gate:** an OpenMC executable is available for transport, MGXS
  tally generation, and helpers that launch a transport subprocess.
- **Continuous-energy data gate:** `cross_sections.xml` parses, its referenced
  files exist, and each referenced HDF5 file has a compatible file type/schema.
  An index alone is not a library.
- **Chain gate:** the selected chain XML parses and contains the nuclides,
  decay paths, reactions, and fission-yield data needed by the calculation.
- **MG gate:** a supplied or generated `mgxs.h5` has compatible group metadata,
  datasets, materials/nuclides, and model `energy_mode='multi-group'` settings.

With the known inspection environment, treat Python 3.12 and the representative
base APIs as available, `libopenmc.so` as unavailable until a native build proves
otherwise, and `OPENMC_CROSS_SECTIONS` as unset. Do not download a data bundle or
run transport merely to improve this verdict.

## Route by need

- **Index, HDF5, ENDF/ACE, chain schema, or path semantics:** read
  [data-formats.md](references/data-formats.md), then run the validator.
- **Coupled depletion, independent/decay-only depletion, timestep units,
  integrators, transfer rates, MicroXS, MGXS generation, or restart:** read
  [depletion-and-mgxs-workflows.md](references/depletion-and-mgxs-workflows.md).
- **A missing file, XML parse error, unknown nuclide/reaction, unit mismatch,
  zero/negative rates, restart mismatch, or MGXS schema issue:** read
  [troubleshooting.md](references/troubleshooting.md).
- **Materials, geometry, source, or settings construction:** route to
  [model-geometry](../model-geometry/SKILL.md); return here for depletion
  volumes, data gates, chain choice, and normalization.
- **Executable, build, `OPENMC_CROSS_SECTIONS`, or broad environment setup:**
  route to [setup-runtime](../setup-runtime/SKILL.md).
- **Statepoint, summary, tally, or generic HDF5 result analysis:** route to
  [tallies-results](../tallies-results/SKILL.md). Depletion-result semantics
  stay here, including `Results.get_atoms`, `get_keff`, and reaction rates.
- **C API lifecycle, optional native integrations, or C++ build details:**
  route to [advanced-solvers](../advanced-solvers/SKILL.md).

## Safe operating procedure

1. Record the package/API version, requested data artifact, selected files, and
   whether the intended result is data-free, data-dependent, native-library,
   executable, or optional-backend work.
2. Use explicit paths and a dedicated output directory. Never infer a data path
   from the current working directory when the input can name it explicitly.
3. Validate the index and referenced HDF5 files before creating a transport
   operator. Validate the chain independently; inspect naming, units, reaction
   coverage, and fission yields before interpreting a result.
4. For MGXS, fix the energy-group edges and ordering before constructing tallies
   or consuming arrays. For MicroXS, verify the `(nuclide, reaction, group)`
   shape and barn units, and ensure each flux has the matching group count.
5. For depletion, state the operator, normalization (`power`, `power_density`,
   or `source_rates`), timestep units, integrator, solver/substeps, material
   volumes, and restart/continuation policy. A zero source rate is a valid
   decay-only setup, not evidence that transport data was checked.
6. Preserve raw paths and validation output in the task's review area, not in
   this runtime tree. Report skipped transport/native/data checks explicitly.

## Definition of done

A data/depletion task is complete only when the requested files and units are
identified, relevant data paths and schemas are checked, the chosen operator and
integrator semantics are consistent, and every unavailable native or data gate
is reported. A successful API/XML/parser check must not be reported as a
successful transport, MGXS tally, or coupled depletion run.

## Bundled check

The validator is intentionally narrow and safe: it accepts an explicit
`--cross-sections` XML path, parses without network access, resolves
`<directory>`, `<library>`, and `<depletion_chain>` references, reports missing
files and malformed XML, and performs lightweight HDF5 file-type, version, and
listed-top-level-group checks when `h5py` is available. See
[validate_data_paths.py](scripts/validate_data_paths.py) for its command-line
contract.

## Evidence boundary

This skill distills the public `openmc.data`, `openmc.deplete`, and `openmc.mgxs`
APIs, user-guide data/depletion/processing guidance, nuclear-data/depletion/MGXS
format descriptions, the small depletion and multigroup examples, and the data,
depletion, MGXS, restart, and transport-free test expectations. It deliberately
omits bundled nuclear-data archives, download automation, private environment
paths, and expensive transport/regression commands.
