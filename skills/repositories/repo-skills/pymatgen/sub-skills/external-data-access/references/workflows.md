# External Data Workflows

Use these workflows to plan external data access without leaking credentials or making surprise network calls. Every live request should be explicit, narrow, and followed by a handoff to the analysis sub-skill that owns the fetched object type.

## No-Network First Checklist

Before any live request, record:

- Data source: Materials Project, COD, OPTIMADE alias/resource URL, or multiple providers.
- Query shape: material ids, formula, chemical system, OPTIMADE filter, COD id, endpoint document, and requested `_fields` or response fields.
- Credential state: whether `PMG_MAPI_KEY` is needed, present, and 32 characters, without printing the key.
- Result risk: likely result count, pagination, all-provider OPTIMADE behavior, COD multiple-CIF downloads, or broad `get_entries_in_chemsys` expansion.
- Downstream owner: entries to `../entries-thermodynamics-and-batteries/SKILL.md`, structures to `../structures-local-environments-and-transformations/SKILL.md`, or electrochemistry/surface workflows to `../surfaces-interfaces-and-electrochemistry/SKILL.md`.

Run the bundled [../scripts/external_access_probe.py](../scripts/external_access_probe.py) for import/key-shape/filter checks only. It intentionally performs no network calls.

## Credential-Safe Materials Project Setup

Recommended decision flow:

1. Ask whether the user authorizes a live Materials Project request if the task can be answered offline.
2. Check whether an API key is available without printing it.
3. Validate only key presence and 32-character shape before constructing `MPRester`; the constructor raises for missing, invalid, or old keys.
4. Use a context manager so the HTTP session closes cleanly.
5. Request only required fields with `_fields`.

Minimal live pattern, after user authorization:

```python
import os
from pymatgen.ext.matproj import MPRester

api_key = os.environ.get("PMG_MAPI_KEY")
if not api_key or len(api_key.strip()) != 32:
    raise RuntimeError("Set a current 32-character PMG_MAPI_KEY before making live MP requests.")

with MPRester(api_key.strip()) as mpr:
    docs = mpr.summary.search(
        material_ids="mp-19017",
        _fields=["material_id", "formula_pretty", "energy_above_hull"],
    )
```

Do not print `api_key`, HTTP headers, `.pmgrc.yaml` contents, shell history lines, or full exception contexts that may contain credentials.

## Materials Project Summary Queries

Use pymatgen's documented endpoint parity:

```python
with MPRester(api_key) as mpr:
    docs = mpr.summary.search(
        formula="Fe2O3",
        _fields=["material_id", "formula_pretty", "band_gap", "energy_above_hull"],
    )

    same_docs = mpr.materials.summary.search(
        formula="Fe2O3",
        _fields="material_id,formula_pretty",
    )
```

Planning notes:

- Use Materials Project API field names exactly; for example `nelements` and `nsites`, not `num_elements` or `num_sites`.
- Put returned field names in `_fields`; put filters as normal kwargs.
- Omitting `_fields` requests all fields, which is rarely appropriate for first-pass agent work.
- For repeated or broad queries, describe likely result shape and ask the user to narrow formulas, fields, or chemical systems first.

## Fetch Structures for Structural Analysis

Use one-id fetches when possible:

```python
with MPRester(api_key) as mpr:
    structure = mpr.get_structure_by_material_id("mp-19017")
```

Use formula or chemical-system fetches only when the result count is acceptable:

```python
with MPRester(api_key) as mpr:
    structures = mpr.get_structures("Mn3O4")
```

Handoff:

- Continue with `../structures-local-environments-and-transformations/SKILL.md` for coordination numbers, near-neighbor models, dimensionality, graphs, transformations, prototypes, or magnetism.
- Preserve provenance such as material id, fields, source, and whether `conventional_unit_cell=True` was requested.
- Do not repeat network fetches in the downstream analysis unless the user requests fresh data.

## Fetch Entries for Thermodynamics and Batteries

Use `get_entries` or `get_entries_in_chemsys` only after the user accepts result volume and compatibility assumptions:

```python
with MPRester(api_key) as mpr:
    entries = mpr.get_entries_in_chemsys(
        ["Li", "Fe", "O"],
        compatible_only=True,
        property_data=["formation_energy_per_atom"],
        summary_data=["band_gap"],
    )
```

Handoff:

- Continue with `../entries-thermodynamics-and-batteries/SKILL.md` for compatibility corrections, phase diagrams, reactions, battery electrodes, or Borg assimilation.
- Explain that `property_data` comes from the thermo endpoint and is consistent with returned entries, while `summary_data` may describe a different best Materials Project calculation.
- Avoid very broad systems and multi-element expansions until the user accepts runtime and rate implications.

## COD Structure Lookup

COD is useful when the task asks for crystallographic structures and does not require Materials Project computed properties:

```python
from pymatgen.ext.cod import COD

cod = COD(timeout=30)
ids = cod.get_cod_ids("Li2O")
structure = cod.get_structure_by_id(ids[0])
```

Planning notes:

- COD does not need `PMG_MAPI_KEY`, but all lookups and CIF downloads are live network calls.
- `get_structure_by_formula` can download and parse many CIFs. Prefer `get_cod_ids` first when the user needs to choose a candidate.
- Pass `Structure.from_str` parser kwargs through `get_structure_by_id` or `get_structure_by_formula` when the user needs parser tolerance changes.
- Continue with `../structures-local-environments-and-transformations/SKILL.md` after structures are fetched.

## OPTIMADE Queries

Use OPTIMADE when the user needs provider-agnostic structure search or names OPTIMADE directly:

```python
from pymatgen.ext.optimade import OptimadeRester

with OptimadeRester("mp", timeout=10) as optimade:
    structures_by_provider = optimade.get_structures(elements=["Ga", "N"], nelements=2)
```

Use raw filters for advanced syntax:

```python
query = 'elements HAS ALL "Ga", "N" AND nelements=2'
with OptimadeRester("mp", timeout=10) as optimade:
    structures_by_provider = optimade.get_structures_with_filter(query)
```

Use `get_snls` when provenance or extra response fields matter:

```python
with OptimadeRester("mp", timeout=10) as optimade:
    snls = optimade.get_snls(
        elements=["Ga", "N"],
        nelements=2,
        additional_response_fields={"nsites", "nelements"},
    )
```

Planning notes:

- Always pass explicit aliases or resource URLs unless the user intentionally wants a slow all-provider query.
- `refresh_aliases=True` and `refresh_aliases()` are live provider-list requests.
- Some providers are intermittently unavailable, redirected, or bot-protected; narrow providers rather than treating every provider failure as a local package error.
- Extra OPTIMADE fields are easiest to preserve through `StructureNL.data["_optimade"]` from `get_snls`.

## User-Safe Handoff Templates

Entries to thermodynamics:

```text
Planned/fetched MP entries for <chemsys/formula/material ids> with compatible_only=<bool>, property_data=<fields>, summary_data=<fields>. Continue with entries-thermodynamics-and-batteries for compatibility assumptions, phase diagrams, batteries, or reaction workflows.
```

Structures to local analysis:

```text
Planned/fetched <n> structures from <MP/COD/OPTIMADE> with provenance <ids/providers>. Continue with structures-local-environments-and-transformations for neighbor finding, graph/dimensionality, transformations, prototypes, or magnetism.
```

Structures or entries to electrochemistry:

```text
External data is ready for Pourbaix/surface/interface analysis. Continue with surfaces-interfaces-and-electrochemistry and verify formation-energy, concentration, pH/voltage, slab, and compatibility assumptions before interpreting results.
```
