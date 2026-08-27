# Cross-Cutting Troubleshooting

## Purpose

Use this before executing an indexed medical-research workflow or when catalog
selection, installation, data access, backend setup, or output validation fails.
Read the nearest sub-skill troubleshooting reference for domain-specific errors.

| Symptom | Likely cause | Recovery | Stop condition |
|---|---|---|---|
| Catalog query returns no result | Over-specific wording, wrong category/collection filter, or an uncovered capability | Remove filters, search by artifact/data/API synonyms, and inspect the category route; then ask for the missing task details | No candidate's input/output contract fits; report a gap rather than forcing a match |
| Several plausible candidates | Broad request spans stages or overlapping packages | Name the primary artifact, environment, data modality, and acceptance check; select one owner and explicit supporting routes | The user has not decided whether they need planning, execution, or writing |
| `scripts/` or `requirements.txt` exists but execution fails | Presence flags do not prove installed dependencies or compatible language/backend | Read the specialist entry, identify exact Python/R/Node/system packages, create an isolated minimal environment, run parser/help/import checks, then a tiny fixture | Dependency or backend is unavailable and no evidence-backed substitute exists |
| Import/package not found | The repository itself is not a root Python package, or a per-skill dependency was not installed | Do not run `pip install .` at the catalog root. Prepare the selected specialist environment only and use its documented package/import names | Resolving the package would require broad or destructive mutation without approval |
| API timeout, 401/403/429, or empty retrieval | Missing key, invalid endpoint/query, rate limit, network failure, or no records | Validate endpoint/query and credentials without exposing secrets; use bounded retries/backoff; save response metadata; offer an offline/manual route | Access is unauthorized, credentials are unavailable, or results cannot be verified |
| R/Node/system binary absent | Selected script uses a non-Python runtime or external executable | Identify exact runtime and package lock/version from the selected workflow; ask before host-level installation | A compatible runtime cannot be prepared within budget or permissions |
| GPU/accelerator unavailable | A model workflow requires CUDA/ROCm/MPS/vendor hardware or a matching wheel | Probe hardware/driver/framework; use a documented CPU alternative only when behavior is fully equivalent; otherwise narrow scope or report the block | Required backend has no full substitute; never treat CPU import as verification |
| Data validation fails | Wrong orientation, units, schema, identifiers, missingness, outcome encoding, or protected fields | Preserve raw data; validate with the data-analysis schema reference; create a corrected copy and provenance log | Fix would require guessing labels, outcomes, units, or patient identity |
| Citations/PMIDs/DOIs cannot be verified | Placeholder, stale metadata, hallucinated identifier, inaccessible source, or claim mismatch | Mark unverified; retrieve authoritative metadata when allowed; weaken/remove claim or request the source | Never fabricate identifiers or present an inaccessible citation as verified |
| Output sounds clinical/prescriptive | Research-support task crossed into diagnosis/treatment | Reframe as evidence or protocol support, list uncertainty, and require qualified clinical review | Patient-specific diagnosis, prescribing, dosing, or emergency advice is requested |
| PHI or identifiable images/text are present | Data were not de-identified or output retains metadata | Minimize and de-identify locally, preserve an audit trail, restrict output, and manually inspect transformed files | Authorization, lawful basis, or secure environment is missing |
| Installer would overwrite a skill | Destination collision or bulk installer policy differs from the user's intent | Dry-run/list targets, compare versions/provenance, and request explicit overwrite approval per destination | Never delete or overwrite silently |
| Generated skill appears stale | Source commit, category count, descriptions, or tool contract changed | Compare `repo-provenance.md`, refresh the repo skill, rebuild the index, rerun offline validation and usability checks | Do not silently mix old index metadata with new source claims |

## Safe recovery order

1. Preserve the failing input, exact command/API request shape (without secrets),
   exit status, and concise error.
2. Classify the failure: selection, missing input, dependency, backend,
   credential/network, schema, privacy, scientific integrity, or unsupported
   scope.
3. Apply the smallest reversible repair. Do not install broad extras or mutate a
   user-owned environment just to make one candidate import.
4. Rerun the nearest deterministic gate: index check, parser/help, schema
   validator, tiny fixture, citation lookup, or backend smoke.
5. Mark the result `complete`, `partial`, or `blocked`, with unresolved evidence
   and the next viable action.
