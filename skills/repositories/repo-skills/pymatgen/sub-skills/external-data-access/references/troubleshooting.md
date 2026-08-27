# External Data Troubleshooting

Diagnose external-data failures as combinations of credentials, endpoint semantics, network availability, query scale, provider quirks, and downstream analysis assumptions. Do not expose secrets while debugging.

## Materials Project API Key Fails Immediately

Symptoms:

- `ValueError: Invalid or old API key. Please obtain an updated API key...`
- `MPRester()` fails before any endpoint request.
- Tests skip with `PMG_MAPI_KEY not set` or fail with invalid key length.

Likely causes and fixes:

- `PMG_MAPI_KEY` is missing. Set it for the current process, or route persistent setup to `../cli-and-configuration/SKILL.md` for `pmg config --add PMG_MAPI_KEY <USER_API_KEY>` only when the user approves config mutation.
- The key is from an old Materials Project API, copied incorrectly, or includes whitespace/prompt text. Check only presence and `len(key.strip()) == 32`; never print the key.
- The wrong config scope is being read. Ask whether the user set an environment variable, notebook variable, pymatgen config file, or shell profile value.

Safe response pattern:

```text
The failure occurs during MPRester construction, before a network call. pymatgen validates that the key exists and is 32 characters. Please rotate or re-copy the key from the Materials Project dashboard, then set PMG_MAPI_KEY without sharing it here.
```

## Secret Redaction

Never include any of the following in replies, logs, notebooks, issue reports, or generated scripts:

- Raw `PMG_MAPI_KEY` values.
- HTTP headers containing `x-api-key`.
- Full `.pmgrc.yaml` contents when it may contain credentials.
- Shell history lines with inline API keys.
- Full tracebacks if custom user logging may include request headers or secrets.

Safer diagnostics:

- Print `present=True/False`, `length=<integer>`, and `valid_shape=True/False` only.
- Redact keys as `<redacted>` or state `expected 32 characters, got <n>`.
- Prefer environment variables or approved config files over embedding keys in scripts.
- If a key appeared in shared text, advise the user to rotate it.

## Network, Timeout, Availability, and Rate Failures

Symptoms:

- `requests.exceptions.ConnectionError`, `Timeout`, `ReadTimeout`, HTTP status errors, empty live results, or provider warnings.
- COD or OPTIMADE tests skip because a website/provider is down.
- Broad Materials Project queries are slow or return server/rate-limit errors.

Likely causes and fixes:

- Network is unavailable in the execution environment. Switch to no-network dry planning and provide code for the user to run locally.
- A provider is down, redirected, or blocking automated requests. Retry later, narrow providers, or cautiously increase timeout.
- A query is too broad. Add filters, reduce `_fields`, split chemical systems, or query by explicit ids.
- Corporate proxies or SSL inspection interfere with requests. Ask the user to verify network policy rather than disabling TLS verification.

Do not treat network skips as package failures. The repo's external tests are credential- and provider-gated by design.

## Endpoint Field or Search Parameter Errors

Symptoms:

- Materials Project returns malformed-query errors.
- A field works with `mp-api` but not with `pymatgen.ext.matproj.MPRester`.
- Results include too many fields or lack expected fields.

Likely causes and fixes:

- Pymatgen's `MPRester` mirrors Materials Project API field names. Use `nelements` and `nsites`, not `num_elements` or `num_sites`.
- Put returned field names in `_fields`; put filters as normal kwargs.
- Use `mpr.summary.search(...)` or `mpr.materials.summary.search(...)` for summary docs.
- If a specialized route is unsupported by pymatgen's simpler client, install and use `mp-api` separately for that task.

Example correction:

```python
docs = mpr.summary.search(
    nelements=2,
    nsites=(1, 20),
    _fields=["material_id", "formula_pretty"],
)
```

## Pagination and Large Query Surprises

Symptoms:

- Very slow `get_entries_in_chemsys` calls.
- More results than expected from formula or chemical-system queries.
- Secondary summary lookups add time after entries are fetched.

Likely causes and fixes:

- `get_entries_in_chemsys(["Li", "Fe", "O"])` expands to every subsystem as well as the full system.
- `MPRester` internally pages in chunks of 1000 until completion.
- `summary_data` for entries adds chunked summary endpoint searches.
- Ask before running broad live requests; use explicit ids, smaller chemical systems, and minimal fields first.

## Materials Project Entries Look Inconsistent

Symptoms:

- `entry.data["summary"]` values do not match entry energy or calculation metadata.
- Phase diagrams differ from expected Materials Project values.
- Compatibility processing removes entries.

Likely causes and fixes:

- `property_data` comes from the thermo endpoint and is kept consistent with returned entries.
- `summary_data` comes from the summary endpoint and may describe a different best calculation.
- `compatible_only=True` processes entries with `MaterialsProject2020Compatibility`, which can adjust or remove entries.
- Continue in `../entries-thermodynamics-and-batteries/SKILL.md` for compatibility and thermodynamic interpretation.

## Missing Full `mp-api` Feature or Optional Plugin

Symptoms:

- `AttributeError` says an attribute is not supported by pymatgen's `MPRester` implementation.
- A user asks for `mp-api`-specific data models, builder routes, or field aliases.
- Tests skip because a plugin such as an alloys package is unavailable.

Guidance:

- Baseline pymatgen skill generation assumes the base package install; optional extras are conditional.
- Pymatgen's `MPRester` covers common summary, thermo entries, structures, document searches, and phonon open-data helpers.
- Install `mp-api` or optional plugins only when the requested workflow requires them and the user approves dependency changes.
- Keep issue ownership clear: pymatgen client issues belong to pymatgen, while `mp-api` client issues belong to `mp-api`.

## COD Lookup Fails

Symptoms:

- `get_cod_ids` raises a request error.
- `get_structure_by_formula` is slow or fails on one CIF.
- `Structure.from_str` fails while parsing a downloaded CIF.

Likely causes and fixes:

- COD is a live network service and may be down, slow, or blocked.
- Formula queries are converted to Hill formula; verify the formula and consider querying ids before structures.
- Some CIFs may be malformed or incompatible with parser defaults. Try a specific COD id, parser kwargs, or a different data source.
- Increase `COD(timeout=...)` only when the user accepts longer waits.

## OPTIMADE Alias or Filter Fails

Symptoms:

- `OptimadeRester()` is slow before a query.
- Warnings mention invalid aliases, provider parsing, or a failed provider.
- One provider returns no structures while another succeeds.
- Formula filters return unexpected matches.

Likely causes and fixes:

- Calling `OptimadeRester()` with no aliases attempts all known providers. Use explicit aliases such as `"mp"`, `"cod"`, or a specific Materials Cloud alias.
- `refresh_aliases=True` requires the live providers list and can fail independently of structure queries.
- OPTIMADE anonymous and Hill formulas may differ from pymatgen formulas. Inspect `OptimadeRester._build_filter(...)` output or write a raw filter.
- Some providers are offline, redirected, or bot-protected. Narrow providers, retry later, or use a different source.
- Use `get_snls(..., additional_response_fields=...)` when extra provider metadata is needed for debugging.

## Live Provider Validation Boundary

For local validation, prefer the bundled offline probe. Live smoke checks require user authorization, credentials when needed, and the narrowest endpoint or provider because Materials Project, COD, and OPTIMADE availability can vary independently from local package correctness.
