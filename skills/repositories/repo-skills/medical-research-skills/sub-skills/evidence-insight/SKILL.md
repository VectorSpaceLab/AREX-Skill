---
name: evidence-insight
description: "Routes medical-research requests involving literature discovery,
  PubMed/PMC and database signals, PICO search design, evidence mapping, gap
  auditing, evidence ranking, and citation integrity while separating retrieval,
  synthesis, and provenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Evidence Insight

Use this route when the user needs an evidence-grounded view of medical or
biomedical literature: find records, design a reproducible search, inspect
PubMed/PMC or registry signals, screen and map evidence, identify defensible
gaps, rank evidence, or verify that a claim is supported by its cited source.

This is a **router and evidence-control skill**, not a replacement for a
protocol writer, statistical analyst, or manuscript writer. Keep all claims
bounded by the records and source passages actually available. Never invent a
citation, identifier, result, trial status, or database response.

## Route by the requested deliverable

| User need | Route here | Next route when the deliverable changes |
|---|---|---|
| Clarify a clinical/research question; build PICO/PICOS or PECO concepts | Define scope and search blocks | `protocol-design` for a study protocol or endpoints |
| Find biomedical literature or build a PubMed/PMC strategy | Search and retrieval workflow | `academic-writing` only for prose built from verified results |
| Find trials, studies, or database records | Registry/database signal workflow | `protocol-design` for trial design or eligibility planning |
| Screen records or organize evidence | Screening and evidence-map workflow | `data-analysis` for quantitative synthesis or modeling |
| Compare evidence strength or resolve contradictory findings | Evidence ranking and conflict workflow | `protocol-design` for a study that resolves the gap |
| Test whether a paper supports a claim or citation | Claim-source verification workflow | `academic-writing` for citation-safe manuscript wording |
| Identify a real, topic-specific research gap | Retrieval-first gap audit | `protocol-design` for a study-ready design |
| Fit models, calculate power, analyze clinical/omics data | Do not execute here | `data-analysis` |
| Draft a review, paper section, abstract, or submission package | Do not execute here | `academic-writing` |

When a request spans routes, finish the evidence-insight handoff first and
state which evidence is verified, provisional, or missing. Do not silently
perform the sibling deliverable.

## Operating sequence

1. **Normalize the question.** Record the population/problem, exposure or
   intervention, comparator, outcome, study design, setting, date/language,
   evidence layer, and intended use. Mark unknowns instead of filling them in.
2. **Choose sources deliberately.** Use PubMed/MEDLINE as the biomedical
   anchor when applicable; use PMC for accessible full text; use a trial or
   study registry for registry signals; add other databases only with their
   exact coverage and access recorded.
3. **Build a reproducible search.** Make concept blocks from PICO/PICOS or
   PECO. Combine synonyms with `OR`, concepts with `AND`, and use MeSH plus
   title/abstract terms. Keep a sensitive search and a precision refinement
   separate. Record the exact query, database, vocabulary version or search
   date, filters, and result handling.
4. **Retrieve and screen.** Normalize PMID/PMCID/DOI and registry identifiers,
   deduplicate conservatively, and separate title/abstract screening from
   full-text verification. Automated scores are triage signals; a human must
   resolve ambiguous inclusion or exclusion decisions.
5. **Map evidence before synthesizing.** For each included item capture design
   family, population, exposure/intervention, comparator, endpoint, direction
   and magnitude only when verified, limitations, validation, and evidence
   role. Distinguish direct-topic evidence from adjacent evidence.
6. **Audit claims and gaps.** Decompose claims, trace each citation to the
   source actually checked, and keep association, prediction, mechanism,
   causation, and clinical utility distinct. A gap is formal only after the
   retrieval and evidence audit; reject generic requests for “more studies” or
   “more validation” without a topic-specific unresolved question.
7. **Handoff or stop.** Return a compact result with scope, search record,
   evidence map, provenance, uncertainty, and recommended sibling route. Stop
   when a required source, credential, full text, or verification gate is
   unavailable rather than fabricating a conclusion.

Use the bundled references progressively:

- [workflows.md](references/workflows.md) for PICO/search, retrieval,
  screening, mapping, gap, citation, and routing procedures.
- [data-and-provenance.md](references/data-and-provenance.md) for PubMed/PMC,
  registry/database signals, API and credential boundaries, citation ledgers,
  and evidence-status rules.
- [troubleshooting.md](references/troubleshooting.md) for bounded recovery,
  partial results, contradictions, and route failures.

## Required output shape

Unless the user requests a compatible structured format, return:

1. **Question and scope** — normalized PICO/PICOS or PECO, evidence layer,
   filters, and assumptions.
2. **Sources and search record** — databases/endpoints, exact queries or
   search logic, dates, access limitations, and counts only if observed.
3. **Evidence result** — records or an evidence map with study design, directness,
   limitations, and evidence role.
4. **Integrity and provenance** — identifiers, source locations, retrieval
   dates, verified versus inferred fields, exclusions, and unresolved items.
5. **Routing** — why the next action belongs here, `protocol-design`,
   `data-analysis`, or `academic-writing`; include a handoff payload.

A claim without a source location is not a verified finding. A missing count is
preferable to an invented count. If only metadata or an abstract was checked,
say so explicitly.

## Hard boundaries

- Do not give patient-specific diagnosis, treatment, dosing, enrollment, or
  urgent-care advice. Redirect clinical decisions to qualified clinicians and
  appropriate guidance.
- Do not treat PubMed indexing, PMC availability, citation count, journal
  prestige, trial registration, or trial status as proof of efficacy or quality.
- Do not turn an abstract, title, review paraphrase, or registry record into a
  stronger claim than it supports. Separate primary from secondary evidence.
- Do not use an API key, institutional credential, or private full text unless
  the user has explicitly supplied an authorized runtime and the secret remains
  outside prompts, files, logs, and output. Prefer public access and ask for
  missing authorization.
- Do not execute statistical fitting, power calculations, protocol drafting,
  or manuscript composition in this route. Provide an evidence handoff and
  route to the sibling skill.
- Do not claim a research gap without a recorded retrieval and evidence audit.
- Do not expose PHI or place sensitive patient data in external queries.

## Minimal handoff

When routing onward, pass only what the next skill needs:

```text
question: <normalized question>
scope: <PICO/PICOS or PECO plus filters>
evidence_goal: <design, mechanism, prognosis, diagnosis, treatment, etc.>
sources_checked: <database, endpoint, date, query id>
verified_records: <PMID/PMCID/DOI/registry IDs with source status>
key_findings: <source-bounded findings and locations>
uncertainties: <missing full text, unresolved conflicts, inaccessible data>
requested_next_route: protocol-design | data-analysis | academic-writing
```

The handoff is not permission to infer beyond the evidence ledger.
