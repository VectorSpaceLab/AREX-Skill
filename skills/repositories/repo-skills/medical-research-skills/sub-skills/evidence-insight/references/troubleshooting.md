# Troubleshooting and bounded recovery

Use this reference to recover from incomplete retrieval or ambiguous evidence
without silently lowering the evidence standard.

## Missing or underspecified question

**Signal:** no identifiable population/problem, exposure/intervention, outcome,
intent, or evidence layer.

**Action:** ask only for the blocking fields. Offer a minimal PICO/PICOS or PECO
form. Do not launch a broad query and later present its results as answering an
unscoped question. If the user only wants topic orientation, label the result
as exploratory discovery rather than a systematic evidence search.

## MeSH or synonym uncertainty

**Signal:** a term is absent, newly renamed, ambiguous, gene/protein alias is
shared, or a known anchor is missed.

**Action:** retain the plain-language term, check the current controlled
vocabulary, add title/abstract variants, inspect mapped terms, and run a
sensitivity query before applying filters. Record the vocabulary date and
whether explosion/no-explosion or major-topic restriction was used. Never claim
that a query is comprehensive from syntax alone.

## Empty, partial, or unstable API response

**Signal:** timeout, HTTP 429/5xx, malformed payload, empty page, pagination
stops unexpectedly, or count differs between interface and endpoint.

**Action:** verify HTTPS endpoint, status code, content type, query encoding,
page token, date, and rate limit. Retry transient errors with bounded
exponential backoff; stop after the declared retry budget. Use a smaller page,
cache observed records, and preserve the failed request metadata without
secrets. If the service remains unavailable, return the exact prepared query,
last verified records, and a manual retrieval plan. Never convert a failed call
to “zero studies.”

## Credential, paywall, or institutional boundary

**Signal:** API key required, subscription-only database, private repository,
restricted full text, or unauthorized endpoint.

**Action:** stop at the public boundary. Ask for an authorized runtime only when
it changes the requested verification. Never ask the user to paste a token into
chat or write it to a skill artifact. Continue with public metadata or an
abstract if sufficient, but downgrade source access and state what cannot be
verified. Do not infer full-text findings from a title or abstract.

## Duplicate records and linked publications

**Signal:** same study appears under multiple PMIDs, DOI variants, registry and
publication records, conference abstract and full article, or updated analysis.

**Action:** verify identifiers, link reports to a study identity, and count the
study once for evidence mapping unless the reports answer distinct endpoints.
Preserve each report's source location and publication role. If linkage is
uncertain, keep both with an uncertainty flag rather than deleting one.

## Abstract-only or metadata-only evidence

**Signal:** full text, supplement, figure, or methods are unavailable.

**Action:** limit claims to what the abstract or metadata explicitly says. Mark
source access and avoid detailed sample, bias, validation, or effect claims not
reported there. Set support to `cannot verify` when the requested judgment
requires missing material.

## Contradictory findings

**Signal:** studies report opposing directions, null versus positive findings,
or different conclusions for apparently similar questions.

**Action:** create a side-by-side matrix of population, disease stage, exposure or
intervention, comparator, assay, endpoint, timing, design, sample size, missing
data, adjustment, and validation. Check whether the estimand differs before
calling the field inconsistent. Report genuine unresolved conflict with each
source's support and limitations. Do not average or choose a winner without an
approved synthesis method; route quantitative synthesis to `data-analysis`.

## Citation drift or overclaim

**Signal:** a review, slide, or repeated statement is stronger than the cited
paper; association is called causation; exploratory performance is called
clinical utility; animal/in-vitro evidence is stated as human evidence.

**Action:** decompose the claim, trace to the primary source, inspect the actual
source access available, classify support, name the mismatch, and write only a
narrowed citation-safe version. If the primary source cannot be accessed, mark
it unresolved rather than repairing from memory. Route wording and manuscript
integration to `academic-writing` after the claim ledger is complete.

## Screening disagreements or low confidence

**Signal:** unclear abstract, borderline population, ambiguous intervention,
missing outcome, or automated classifier conflict.

**Action:** keep `unclear`, record the exact criterion and evidence passage
needed, and send to human/full-text review. Lowering the threshold to force a
binary decision is not recovery. For a review workflow, retain counts for
identified, screened, excluded, full-text pending, and included records.

## Gap-analysis failure modes

**Signal:** a proposed gap is “more samples,” “add omics,” “validate clinically,”
“study another population,” or “no one has done this” without an evidence map.

**Action:** return to retrieval and document direct-topic coverage, adjacent
coverage, design distribution, conflicts, and missing evidence. Reject generic
upgrades unless they answer a specific unresolved question with a rationale and
feasible study family. Distinguish thin retrieval from a genuine absence of
evidence. Route a surviving gap to `protocol-design` only with medium/high
confidence and explicit feasibility limits.

## Rate-limit and data-safety incident

**Signal:** repeated throttling, accidental PHI in a query, secret in a command
or log, or response includes sensitive data.

**Action:** stop network activity, redact output and logs, rotate the exposed
credential through the authorized owner, and record the incident without the
secret or PHI. Resume only with a sanitized query and approved rate. If the
incident cannot be contained, return an unverified/blocked handoff.

## Route mismatch

**Signal:** request asks for a sample-size calculation, statistical model,
complete protocol, manuscript section, or clinical decision.

**Action:** do not begin that task. Return the evidence material already
verified, identify the exact next route, and provide a structured handoff. For
`data-analysis`, include data schema and analysis question; for
`protocol-design`, include the evidence-backed question/gap and design
constraints; for `academic-writing`, include citation-safe claims and source
locations.

## Stop conditions

Stop and report `blocked` or `unverified` when:

- the source identity cannot be established for a claim-critical item;
- required full text or registry fields are inaccessible;
- API failures exhaust the declared retry/stop budget;
- a credential or data-safety boundary would be crossed;
- conflicting evidence cannot be reconciled with available context;
- the user asks for fabricated or unverified citations;
- a formal gap is requested without retrieval and an evidence audit.

A useful partial result lists completed checks, retained records, exact failure
point, impact on interpretation, and the smallest next action needed.
