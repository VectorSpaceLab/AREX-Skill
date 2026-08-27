# External Data API Reference

This reference covers the baseline `pymatgen` external clients available with the base package install on Python 3.11+. All three clients can perform live HTTP requests; use this reference to plan and validate code before asking the user for explicit network authorization.

## Materials Project: `pymatgen.ext.matproj`

Import and construct:

```python
from pymatgen.ext.matproj import MPRestError, MPRester

with MPRester(api_key=None, include_user_agent=True) as mpr:
    ...
```

Constructor behavior:

- Signature: `MPRester(api_key: str | None = None, include_user_agent: bool = True) -> None`.
- If `api_key` is `None`, `MPRester` reads `PMG_MAPI_KEY` through pymatgen settings.
- Construction raises `ValueError` when the resulting key is not exactly 32 characters, before any endpoint request.
- `include_user_agent=True` adds pymatgen, Python, and platform information to HTTP headers; set `False` only when the user's policy requires reduced user-agent metadata.
- The endpoint defaults to the Materials Project API endpoint from settings, with advanced override through `PMG_MAPI_ENDPOINT`.

Implementation model:

- Pymatgen's `MPRester` mirrors documented Materials Project API endpoints and field names rather than `mp-api` convenience aliases. Use `nelements` and `nsites`, not `num_elements` or `num_sites`.
- Common endpoint searches work both as simplified attributes and under `materials`, for example `mpr.summary.search(...)` and `mpr.materials.summary.search(...)`.
- The client targets common pymatgen workflows. For routes or models not exposed here, use the separate `mp-api` package instead of calling missing attributes on pymatgen's `MPRester`.

Search documents exposed as attributes include `summary`, `core`, `elasticity`, `phonon`, `eos`, `similarity`, `xas`, `grain_boundaries`, `electronic_structure`, `tasks`, `substrates`, `surface_properties`, `robocrys`, `synthesis`, `magnetism`, `insertion_electrodes`, `conversion_electrodes`, `oxidation_states`, `provenance`, `alloys`, `absorption`, `chemenv`, `bonds`, `piezoelectric`, and `dielectric`.

| Method or path | Purpose | Return shape |
| --- | --- | --- |
| `mpr.summary.search(**kwargs)` | Query `materials/summary` using documented filters and `_fields`. | `list[dict]` |
| `mpr.materials.summary.search(**kwargs)` | Equivalent full path for summary searches. | `list[dict]` |
| `mpr.search(doc, **kwargs)` | Query a supported Materials Project document endpoint. | `list[dict]` |
| `mpr.get_summary(criteria, fields=None)` | Query summary docs by criteria dict such as `{"formula": "Fe2O3"}`. | `list[dict]` |
| `mpr.get_summary_by_material_id(material_id, fields=None)` / `mpr.get_doc(...)` | Fetch one summary doc by Materials Project id. | `dict` |
| `mpr.get_material_ids(formula)` / `get_materials_ids(...)` | Return Materials Project ids for a formula. | `list[str]` |
| `mpr.get_structures(chemsys_formula, final=True)` | Fetch structures for a chemical system or formula; `final=False` requests initial structures. | `list[Structure]` |
| `mpr.get_structure_by_material_id(material_id, conventional_unit_cell=False)` | Fetch one final structure, optionally converted to a conventional standard cell. | `Structure` |
| `mpr.get_initial_structures_by_material_id(material_id, conventional_unit_cell=False)` | Fetch initial structures for one material id. | `list[Structure]` |
| `mpr.get_entries(criteria, compatible_only=True, property_data=None, summary_data=None, **kwargs)` | Fetch entries by chemical system, formula, material id, or list; optionally process with MP2020 compatibility. | entry list |
| `mpr.get_entry_by_material_id(material_id, *args, **kwargs)` | Fetch the first entry for one material id. | entry object |
| `mpr.get_entries_in_chemsys(elements, *args, **kwargs)` | Fetch entries for all sub-systems of a chemical system. | entry list |
| `mpr.get_phonon_bandstructure_by_material_id(material_id)` | Fetch phonon band structure from Materials Project open data. | `PhononBandStructureSymmLine` |
| `mpr.get_phonon_dos_by_material_id(material_id)` | Fetch phonon density of states from Materials Project open data. | `CompletePhononDos` |

Field and pagination behavior:

- Search kwargs that do not start with `_` are filter criteria sent as request payload.
- `_fields` restricts returned fields and sets `_all_fields=False`; omit `_fields` only when the task truly needs full documents.
- `_fields` and list-valued filters may be lists or comma-separated strings; pymatgen comma-joins list values internally.
- Other underscore kwargs are passed as query parameters.
- `MPRester.request` paginates with `_per_page=1000` and `_page`; routes that reject those legacy pagination params are retried once without them.
- `get_entries(..., property_data=[...])` adds thermo endpoint properties directly to each entry's `data`.
- `get_entries(..., summary_data=[...])` performs chunked summary searches and stores values under `entry.data["summary"]`; these summary values may describe a different best Materials Project calculation than the thermo entry.
- Deprecated kwargs `inc_structure`, `conventional_unit_cell`, and `sort_by_e_above_hull` warn and have no effect for `get_entries`.

Exceptions and logging:

- `MPRestError` is raised for malformed REST responses, non-200/400 statuses, missing `data`, and request/decoding failures.
- The client logs query parameters, not the API key. Future code should still avoid logging request headers, `.pmgrc.yaml`, or raw user exception contexts.

## Crystallography Open Database: `pymatgen.ext.cod`

Import and construct:

```python
from pymatgen.ext.cod import COD

cod = COD(timeout=60)
```

| Method | Purpose | Return shape |
| --- | --- | --- |
| `COD(timeout=60)` | Create a COD client with class-level request timeout in seconds. | `COD` |
| `get_cod_ids(formula)` | Query COD ids by formula after converting to Hill formula. | `list[int]` |
| `get_structure_by_id(cod_id, timeout=None, **kwargs)` | Download one CIF by COD id and parse with `Structure.from_str(..., fmt="cif", **kwargs)`. | `Structure` |
| `get_structure_by_formula(formula, **kwargs)` | Query matching COD entries, download each CIF, and parse structures. | `list[{"structure": Structure, "cod_id": int, "sg": str}]` |

Operational notes:

- COD does not require a Materials Project API key.
- COD methods are live HTTP requests and can fail due to service availability, timeout, or CIF parsing.
- `get_structure_by_id(..., timeout=...)` still accepts a per-call timeout but warns that this is deprecated in favor of the class-level timeout.
- Formula queries may match many CIFs; prefer `get_cod_ids` before downloading structures when the user needs a selectable list.

## OPTIMADE: `pymatgen.ext.optimade`

Import and construct:

```python
from pymatgen.ext.optimade import OptimadeRester

with OptimadeRester("mp", timeout=5) as optimade:
    ...
```

Constructor behavior:

- Signature: `OptimadeRester(aliases_or_resource_urls: str | list[str] | None = None, refresh_aliases: bool = False, timeout: int = 5)`.
- `aliases_or_resource_urls` can be one alias, multiple aliases, a structure resource URL, or `None`.
- Passing `None` attempts all known aliases and is intentionally slow; prefer explicit aliases such as `"mp"`, `"cod"`, `"mcloud.mc2d"`, or `"mcloud.mc3d"`.
- `refresh_aliases=True` and `refresh_aliases()` fetch the live provider list before or during use.
- The class is in-development and does not expose the full OPTIMADE specification; use OPTIMADE Python tools for advanced client needs.

| Method | Purpose | Return shape |
| --- | --- | --- |
| `OptimadeRester._build_filter(...)` | Build a simple OPTIMADE filter for elements, `nelements`, `nsites`, anonymous formula, and Hill formula. | `str` |
| `get_structures(...)` | Query structures through the convenience filter builder. | `dict[provider, dict[id, Structure | Molecule]]` |
| `get_snls(..., additional_response_fields=None)` | Query `StructureNL` objects and preserve requested extra attributes under `data["_optimade"]`. | `dict[provider, dict[id, StructureNL]]` |
| `get_structures_with_filter(optimade_filter)` | Query structures with a raw OPTIMADE filter string. | `dict[provider, dict[id, Structure | Molecule]]` |
| `get_snls_with_filter(optimade_filter, additional_response_fields=None)` | Query `StructureNL` objects with a raw filter string. | `dict[provider, dict[id, StructureNL]]` |
| `describe()` | Return human-readable provider information. | `str` |
| `refresh_aliases()` | Replace aliases with structure resources discovered from the live providers list. | `None` |

Response and filter behavior:

- Mandatory OPTIMADE response fields needed to build pymatgen structures are `lattice_vectors`, `cartesian_site_positions`, `species`, and `species_at_sites`.
- `additional_response_fields` may be a string, list, or set and is merged with mandatory fields.
- `get_snls_with_filter` follows `links.next` pagination until no next link remains.
- OPTIMADE formula conventions can differ from pymatgen strings: anonymous formulas may be ordered differently, and Hill formulas follow OPTIMADE/IUPAC-Hill semantics.
- Provider validation and queries are live HTTP operations and may log warnings for unavailable providers while returning results from others.
