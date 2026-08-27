# Data, APIs, credentials, and provenance

Evidence-insight outputs are auditable only when a later reader can distinguish
what a database returned from what an analyst inferred. Use this ledger for
PubMed/PMC, registries, other database signals, and citation verification.

## Source signal types

| Signal | What it can establish | What it cannot establish by itself |
|---|---|---|
| PubMed/MEDLINE record | bibliographic identity, indexed terms, abstract text when present, publication type/date, PMID | complete methods/results, quality, causal effect, current clinical recommendation |
| PMC full text | the accessible article text, tables/figures/supplements actually inspected, PMCID | that the article is peer-reviewed in every version, independent replication, clinical utility |
| Clinical-trial or study registry | registered design, sponsor, recruitment/status fields, dates, protocol-level fields as reported | efficacy, safety, completion quality, publication of results, eligibility for a particular person |
| DOI or publisher metadata | identity/linkage signals, version and bibliographic fields | source content, validity of findings, retraction status unless separately checked |
| Search-engine or citation-network result | discovery lead, related records, citation direction | eligibility, primary-source status, support for a claim |
| Preprint | a clearly labeled non-peer-reviewed research report, if accessible | peer-review acceptance, clinical reliability, definitive evidence |

Never merge these signals into one undifferentiated “evidence” field.

## Provenance ledger

For every retrieved or cited item, preserve a row with these fields (JSON, CSV,
or Markdown table are acceptable):

```text
local_record_id
source_name and endpoint
query or lookup key
retrieval_timestamp_UTC
source_version / vocabulary version / API version
HTTP or interface status
PMID, PMCID, DOI, registry ID (only if source-verified)
title, authors, journal, year (verified / not reported)
source_access: metadata | abstract | full text | figure/table | registry
source_location: URL, section, page, figure, table, or response path
study_identity_link: standalone | linked report | uncertain
field_status: verified | inferred | user-supplied | unavailable
eligibility: include | exclude | unclear + reason
claim_supported: exact claim or null
notes on conflicts, retractions, corrections, or access limits
```

If a field is copied from a user-provided citation rather than checked, mark it
`user-supplied`. If a DOI/PMID/PMCID linkage is only guessed from a title, mark it
`uncertain` and do not use it as verified evidence. Keep retrieval date in UTC
where possible. Database contents and MeSH indexing change; a query is
reproducible only with its date, syntax, filters, and source version.

## PubMed and PMC boundaries

Use HTTPS endpoints or the database's documented interface. For NCBI
E-utilities, keep requests bounded by the documented rate limit; without an
NCBI API key, use no more than three requests per second and add a descriptive
email/tool identifier when the client supports it. An API key is optional for
higher limits, not a reason to disclose one. Store keys only in an environment
variable or approved secret manager; never put them in a query, shell history,
Markdown, JSON output, test fixture, or log.

Typical bounded operations include:

- `esearch` for IDs and count, saving the exact term and filters;
- `efetch` or `esummary` for records, retaining the returned IDs and response
  date;
- PMC full-text retrieval only for a verified PMCID and only when the response
  is actually received;
- MeSH lookup through the current controlled-vocabulary service when term
  mapping must be checked.

Use timeouts, retry only transient failures, and do not treat an empty response
as zero evidence until the HTTP status, response body, query, and pagination
state have been checked. Respect copyright, publisher terms, and access
controls; an abstract is not a license to reproduce an entire article.

## Registry and database boundaries

For ClinicalTrials.gov or another study registry, preserve the registry name,
API version/endpoint, query field, page size, next-page token behavior, and
record status as returned. Show all returned statuses when the user asks for a
landscape; do not silently omit terminated, withdrawn, completed, or unknown
records. Highlighting recruiting status is a display choice, not evidence of
benefit. Never infer efficacy or eligibility from status alone.

A secondary source (another registry, bibliographic index, citation graph,
preprint server, or commercial database) may improve recall, but it has a
coverage and version boundary. State whether it was used for discovery,
verification, or synthesis. If credentials, subscription access, or an
institutional endpoint is required, stop at the public boundary unless the user
has authorized that runtime.

## API and credential checklist

Before network access, record:

- allowed databases/endpoints and purpose;
- whether public access is sufficient;
- credential owner, authorization, expiry, and storage location if a credential
  is explicitly authorized (never print the secret);
- request rate, page/record limit, timeout, retry and stop condition;
- data-sensitivity review: do not send PHI, unpublished confidential data, or
  unnecessary identifiers to external services;
- output location and retention expectations.

Use HTTPS and validate response status/content type. Sanitize errors so they do
not disclose tokens, headers, internal paths, or private query payloads. Do not
bypass robots, paywalls, access controls, or rate limits. If the API is
unavailable, return the prepared query and a manual retrieval plan rather than
fabricating records or counts.

## Citation integrity ledger

Link every answer claim to one or more ledger rows. Use these support labels:

- **directly supported:** the inspected source explicitly reports the claim
  within the same relevant context;
- **partially supported:** only a component, narrower population, endpoint, or
  inference is supported;
- **weakly supported / overstated:** the source is relevant but wording exceeds
  design, findings, or validation;
- **unsupported by cited source:** the source does not justify the claim;
- **cannot verify:** required source content or identity is unavailable.

Add a boundary label when a claim changes:

```text
association | prediction | diagnostic accuracy | mechanism | causation |
clinical utility | implementation | validation
```

An evidence-strength note should identify design family, methodological
execution, validation depth, directness, and claim discipline. Do not replace
this with journal prestige, citation count, a single p-value, or an unexplained
numeric score.

## Retrieval versus inference status

Every output statement should be classifiable as one of:

- `observed`: directly returned or read, with source location;
- `derived`: deterministic normalization, deduplication, or calculation from
  observed fields, with method stated;
- `inferred`: an interpretation that remains bounded and labeled;
- `user-supplied`: provided by the requester but not independently checked;
- `unavailable`: required evidence could not be accessed;
- `contradicted`: a checked source conflicts with the statement.

“No evidence located” means the defined search did not retrieve eligible support;
it does not mean “evidence of no effect.” Keep inaccessible full texts and
unsearched databases visible as coverage limits.

## Minimal evidence bundle for handoff

```text
search_log:
  source, endpoint, query, filters, date_utc, version, count_observed
records:
  id, title, source_access, source_location, eligibility, design_family
claims:
  exact wording, supporting record IDs, support label, boundary label
map:
  population/context, exposure/intervention, comparator, outcome,
  finding, validation, limitation, evidence role
limits:
  unavailable sources, credential/API failures, coverage bias, conflicts
next_route: protocol-design | data-analysis | academic-writing
```

Do not include secrets, PHI, private full-text copies, or unreviewed prompt
content in this bundle.
