# Evidence-insight workflows

This reference is the execution detail behind the router. Use only the
workflow needed for the requested output, and retain its audit trail.

## 1. Scope and PICO/search strategy

Start with a one-sentence question and expand it into explicit concept blocks.
Use PICO for intervention questions; PICOS when study design matters; PECO for
exposure/etiology questions; and a diagnostic or prognostic variant when the
question is about tests or prediction.

| Block | Capture | Search behavior |
|---|---|---|
| P: population/problem | disease, phenotype, age, setting, severity, tissue | MeSH/controlled terms plus spelling, acronym, phenotype and setting synonyms |
| I/E: intervention/exposure | treatment, biomarker, gene, pathway, exposure | class terms, named agents, aliases, assay/platform terms as needed |
| C: comparator | usual care, placebo, reference test, unexposed group | include only when it improves discrimination; do not force a comparator into every retrieval |
| O: outcome | clinical endpoint, diagnostic measure, prognosis, mechanism | use outcome terms when precision is needed; omit them in a broad discovery pass if they risk false negatives |
| S: study/design | RCT, cohort, diagnostic, review, registry, model | use validated publication-type or text filters cautiously and report exclusions |

### Search construction

1. Write the concepts in plain language before choosing controlled terms.
2. Map each concept to current MeSH or the database's controlled vocabulary;
   record the vocabulary date/version and whether a term is exploded or
   restricted. Never assume a familiar synonym is a current preferred term.
3. Add title/abstract synonyms, spelling variants, acronyms, older names, and
   gene/protein aliases. Quote multiword phrases only when appropriate.
4. Join synonyms with `OR`, concept blocks with `AND`, and place every block in
   parentheses. Use `NOT` sparingly and state what it may remove.
5. Run a sensitivity-oriented query first. Then produce a precision-oriented
   variant using major-topic, design, date, species, language, or setting
   limits. Never report the narrow query as exhaustive.
6. Test the query against known relevant anchor records when available. If an
   anchor is missed, inspect indexing, synonym, date, and full-text terms before
   narrowing further.
7. Save the copy-paste query and the database search URL or request parameters.
   Record search date/time, filters, result count as observed, and any manual
   additions or citation chasing.

Example shape (terms are placeholders, not verified vocabulary):

```text
((P_mesh OR P_synonym[Title/Abstract]) AND
 (I_or_E_mesh OR I_or_E_synonym[Title/Abstract]) AND
 (O_mesh OR O_synonym[Title/Abstract]))
 AND humans[MeSH Terms]
```

Do not present a result count from a prior run as current. A database query is a
retrieval instrument, not evidence of the findings.

## 2. PubMed/PMC and database discovery

Use PubMed/MEDLINE first for biomedical bibliographic discovery. PubMed can
provide indexed metadata, abstracts, MeSH terms, publication types, dates, and
identifiers; those fields do not substitute for methods or results. Use PMC only
when the full text is actually available and record the section, table, figure,
or supplement inspected. For a trial or study-status question, query the
appropriate registry separately and preserve the registry's status/date.

For each database, state:

- why it is included and what it covers;
- exact endpoint/API or interface used;
- query and filters;
- retrieval date and pagination/limit;
- records returned and records retained, if observed;
- failures, access restrictions, and possible coverage bias.

Use citation chasing only as a labeled supplement: backward references,
forward citations, related-record suggestions, author or registry searches. A
record found by chasing is not automatically eligible and must pass the same
criteria.

## 3. Screening and deduplication

Create eligibility rules before screening. Include population, intervention or
exposure, comparator, outcomes, study design, date/language, setting, and
minimum evidence requirement. Define exclusions and the reason vocabulary.

Screen in stages:

1. **Identity normalization:** retain the source ID and a normalized title;
   link PMID, PMCID, DOI, and registry IDs only when the linkage is verified.
2. **Title/abstract triage:** assign include, exclude, or unclear with a reason.
   A confidence score may prioritize review but cannot make a final decision.
3. **Full-text check:** verify the exact population, methods, endpoint, and
   evidence role. Record inaccessible full text as unresolved, not excluded for
   convenience.
4. **Deduplication:** use a verified DOI/PMID/registry ID first, then cautious
   title/author/year matching. Preserve reports of the same study as linked
   reports rather than counting them as independent evidence.
5. **Conflict log:** retain disagreements, changed decisions, and reasons.

For systematic-review screening, maintain a PRISMA-compatible flow ledger, but
do not claim PRISMA compliance merely because a spreadsheet exists. Automated
keyword or fuzzy matching is triage; ambiguous cases require human review.

## 4. Evidence mapping and ranking

Build one row per study or one row per linked study report. At minimum capture:

```text
record_id | source_ids | citation_status | design_family | population/context |
exposure/intervention | comparator | endpoint | evidence_role |
verified_finding | strength/uncertainty | validation | limitations |
source_location | retrieval_date | decision
```

Use evidence families rather than a single universal ladder:

- evidence synthesis: systematic review, meta-analysis, scoping or umbrella review;
- interventional: randomized, non-randomized, pragmatic, or experimental intervention;
- clinical observational: cohort, case-control, cross-sectional, registry, or RWE;
- diagnostic/prognostic/predictive: model development, test evaluation, validation;
- mechanism/experimental: cell, animal, perturbation, or pathway work;
- omics/computational discovery: transcriptomic, proteomic, single-cell, spatial,
  multi-omics, or in-silico discovery;
- validation/replication: external, orthogonal, prospective, or independent
  replication evidence.

Rank for the stated purpose, not by journal prestige, citation count, or design
label alone. Consider directness, allowable inference, execution quality,
validation depth, bias control, missing data, multiplicity, model burden,
reproducibility, and claim discipline. Label citation roles as anchor,
high-value support, context-setting, mechanistic support, or caution. If papers
answer different questions, give a role map instead of a false total order.

For conflicting results, align the studies by population, intervention/exposure,
assay, endpoint, timing, comparator, design, and analysis. A disagreement may
reflect context modification, different estimands, measurement error, bias,
underpowered studies, or genuine inconsistency. Do not resolve it by selecting
the most recent, most cited, or most positive paper.

## 5. Gap audit

A formal gap requires retrieval first. Then document:

1. what direct-topic studies cover;
2. which evidence families, populations, settings, stages, endpoints, or
   mechanisms are thin, inconsistent, or absent;
3. why the missing part matters to the question;
4. why it is not merely “add more samples,” “use multi-omics,” or another
   generic upgrade;
5. what study type could answer it and what feasibility limits apply;
6. confidence (medium/high only for priority recommendations).

Use gap labels such as knowledge, evidence, consistency, population, context,
method-resolution, validation, mechanism-to-translation, and implementation.
Reject a gap if it is only a future-direction sentence, lacks a mapped evidence
base, is already answered by an adequate study, or cannot be distinguished from
an inaccessible-search problem. Distinguish “no evidence located” from “evidence
of no effect.” Route surviving study opportunities to `protocol-design`.

## 6. Claim and citation integrity

For every substantive claim:

1. quote or restate the exact claim;
2. identify the cited item and whether it is primary or secondary;
3. inspect the source actually available (metadata, abstract, full text,
   figure/table, or methods/results excerpt);
4. record what it explicitly showed, what it only suggested, and what it did not
   address;
5. compare population, model, endpoint, exposure, assay, timing, and intended
   use;
6. classify support as directly supported, partially supported, weakly supported/
   overstated, unsupported, or unverifiable;
7. check association→causation, model performance→clinical utility,
   exploratory→validated, and animal/in-vitro→human transfers;
8. supply conservative citation-safe wording if requested.

A review can contextualize a claim but is not equivalent to its primary sources.
Trace backward when the cited review appears to be a downstream retelling, and
keep chain uncertainty explicit.

## 7. Routing handoffs

- **To `protocol-design`:** pass the normalized question, evidence map, gap
  audit, target population, plausible design families, known bias concerns,
  feasibility constraints, and unresolved evidence. Do not draft endpoints,
  sample size, or a complete protocol here.
- **To `data-analysis`:** pass a verified data/evidence schema, units and
  identifiers, outcome/exposure definitions, missingness or eligibility notes,
  and the analysis question. Do not fit or interpret a model here.
- **To `academic-writing`:** pass source-verified claims, citation ledger,
  evidence roles, supported wording, and unresolved citations. Do not write the
  manuscript section here.

A route handoff must state whether the next agent may use live retrieval, only
provided records, or an offline evidence bundle.
