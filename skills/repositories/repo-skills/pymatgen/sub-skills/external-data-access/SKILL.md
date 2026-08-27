---
name: external-data-access
description: "Use pymatgen external data clients for Materials Project, COD, and
  OPTIMADE safely with credentials, fields, pagination, and network boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# External Data Access

Use this sub-skill when a task mentions `MPRester`, `PMG_MAPI_KEY`, Materials Project API fields, `summary.search`, `materials.summary.search`, `get_entries`, `get_structure_by_material_id`, `COD`, Crystallography Open Database, `OptimadeRester`, OPTIMADE aliases, filters, API keys, endpoint fields, network/rate limits, or skip-network behavior.

## Read This First

- For imports, constructor signatures, endpoint paths, common methods, `_fields`, pagination, and return objects, read [references/api-reference.md](references/api-reference.md).
- For credential-safe query planning, no-network defaults, context-manager patterns, and downstream handoffs, read [references/workflows.md](references/workflows.md).
- For invalid keys, `PMG_MAPI_KEY`, endpoint field names, network/rate limits, COD timeouts, OPTIMADE aliases, secret redaction, and `mp-api` confusion, read [references/troubleshooting.md](references/troubleshooting.md).
- To check local importability, public constructor shapes, OPTIMADE offline filter building, and Materials Project key shape without network calls, run [scripts/external_access_probe.py](scripts/external_access_probe.py) with `--help` first.

## Routing Boundaries

- Stay here for credential setup, safe data-source selection, offline query plans, Materials Project endpoint fields, COD formula/ID lookup planning, OPTIMADE aliases/filters, network diagnostics, pagination/rate boundaries, and redacted logging.
- Route fetched Materials Project entries to `../entries-thermodynamics-and-batteries/SKILL.md` for compatibility corrections, phase diagrams, reactions, or battery workflows.
- Route fetched `Structure` objects from Materials Project, COD, or OPTIMADE to `../structures-local-environments-and-transformations/SKILL.md` for neighbor finding, structure graphs, transformations, prototypes, dimensionality, or magnetism.
- Route external data feeding Pourbaix, slab, Wulff, surface, or interface workflows to `../surfaces-interfaces-and-electrochemistry/SKILL.md` after the fetch plan is complete.
- Route persistent configuration mutations such as `pmg config --add PMG_MAPI_KEY ...` to `../cli-and-configuration/SKILL.md`.

## Default Approach

1. Start with a no-network plan: identify provider, filters, requested fields, expected return type, result volume risk, required credentials, and the downstream sub-skill that owns analysis.
2. Make live HTTP calls only when the user explicitly authorizes network access and provides or confirms required credentials; never make surprise Materials Project, COD, or OPTIMADE requests.
3. For Materials Project, prefer `from pymatgen.ext.matproj import MPRester`, validate only key presence and 32-character shape, request minimal `_fields`, and never echo keys, headers, `.pmgrc.yaml`, or raw secret-bearing logs.
4. Use documented Materials Project API field names with pymatgen's `MPRester`; paths like `mpr.summary.search(...)` and `mpr.materials.summary.search(...)` both route to common endpoints.
5. For COD and OPTIMADE, narrow formula/provider choices before live calls; avoid all-provider OPTIMADE queries unless the user accepts slow, network-dependent behavior.
6. Preserve provenance such as material ids, COD ids, provider aliases, filters, fields, and timeout choices in user-facing handoffs, then switch to the owning analysis sub-skill.
