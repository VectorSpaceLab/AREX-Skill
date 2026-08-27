# Audit and Safety Reference

This reference turns the catalog's audit and privacy conventions into an
operating checklist. It is a safety and routing aid, not a legal, clinical, or
regulatory certification.

## 1. Two Audit Gates

Use the audit workflow when a user asks to evaluate, score, improve, publish, or
quality-check a skill. Keep the gates separate and do not trade a high static
score for a veto failure.

### Structural/skill veto

Any failure is a deployment blocker:

- **Operational stability:** repeated calls must not show an unacceptable
  failure rate, random crashes, or infinite loops; unresolved dependency
  conflicts are a failure, not a user burden to hide.
- **Structural consistency:** required frontmatter, documented fields, return
  types, and schemas must agree. A plausible paragraph cannot repair a broken
  contract.
- **Result determinism:** identical bounded inputs should produce stable
  numerical results and stable field names. Seed random operations when they
  exist, state nondeterministic dependencies, and preserve formulas and units.
- **System security:** reject raw-string code execution, unfiltered path or
  command construction, prompt-injection avenues, credential leakage, and
  unauthorized filesystem or network actions.

A structural failure means **do not deploy**. Report the failed dimension,
observable evidence, and the smallest corrective change.

### Research/scientific veto

Apply this second gate to Evidence Insight, Protocol Design, Data Analysis, and
Academic Writing outputs. The general/Other category is exempt from this
specific gate, but it is not exempt from honesty, privacy, security, or clinical
boundaries.

- **Scientific integrity:** never fabricate citations, identifiers, trial
  results, sample sizes, p-values, efficacy, or other unverifiable findings.
- **Practice boundaries:** do not diagnose, prescribe, or present a research
  utility as clinical authorization. Flag unapproved or experimental
  interventions and require qualified review.
- **Methodological baseline:** warn about confounding, correlation/causation
  errors, invalid models, leakage, missing ethics approval, and unsupported
  generalization.
- **Code usability:** generated analysis code must be syntactically runnable or
  explicitly marked partial with its dependencies and unverified portions.

A research-veto failure blocks publication or deployment of the audited skill.
The audit may still produce a corrective report; never conceal the veto.

### Static and dynamic review cues

After veto checks, review functional suitability, reliability, performance and
context, agent/human usability, security, maintainability, and agent-specific
properties such as trigger precision, progressive disclosure, composability,
idempotency, and escape hatches. For dynamic review, test canonical, variant,
edge, stress, scope-boundary, and adversarial cases in proportion to complexity.
Assertions should cover format, truthfulness, scope, safety, and completeness.

Do not claim an audit ran merely because a `SKILL.md` looks polished. Distinguish
static inspection, parser/help checks, synthetic tests, native examples,
credentialed/API tests, and human review in the report.

## 2. PHI and Privacy Gate

Assume an unknown environment may contain production PHI. The 18 Safe Harbor
identifier classes include names; sub-state geography; individual-related dates;
phone/fax; email; Social Security, medical-record, health-plan, account,
license, vehicle, device, web/IP, and biometric identifiers; full-face images;
and other unique identifying numbers or codes. Treat accession, specimen,
barcode, and similar research keys as sensitive. Ages over 89 and combinations
that make a rare individual identifiable require additional caution.

Apply these rules before reading, transforming, querying, or displaying data:

1. **Schema is safer than data.** Column names, table definitions, file headers,
   types, row counts, and schema-only errors are usually acceptable; row values,
   clinical narratives, screenshots, and chart-shaped documents are not assumed
   safe.
2. **Do not echo detected PHI.** Identify the category without repeating the
   value or a single-person derivative (for example, an age computed from a
   date of birth). Ask for redaction and the minimum fields needed, or for a
   clear synthetic/test attestation where appropriate.
3. **Generate, do not execute.** For a database, dump, or file-read action that
   could stream PHI into model context, provide a safer schema-only, aggregate,
   or identifier-free projection for the user to run locally. Do not execute it
   and do not paste the original PHI-bearing command back.
4. **De-identification is not a release decision.** Text pattern matching can
   miss contextual identifiers; DICOM metadata removal does not guarantee that
   burned-in annotations or pixel content are safe. Preserve a redaction or
   anonymization audit log, review uncertain detections, and require institutional
   privacy/release approval.
5. **Minimum necessary.** Prefer synthetic fixtures, year-level dates,
   aggregate results with small-cell suppression, schema-only inspection, and
   local processing. Avoid copying sensitive inputs into durable logs or
   generated artifacts.

A literal synthetic-data attestation may permit a small, clearly test-shaped
fixture, but it is not a magic bypass for a prompt that still resembles a real
chart or operational dataset. When the context is ambiguous, ask for
confirmation or require redaction.

## 3. Deterministic Utilities

For calculators, converters, date helpers, lab-preparation arithmetic, and
other bounded utilities:

- Confirm the objective and every required input; reject missing, malformed,
  non-finite, or physiologically implausible values.
- Normalize units before computing and show the formula, factor, selected
  method, precision/rounding, and assumptions.
- Use documented ranges and supported pairs only. Never invent a conversion
  factor, reference range, formula, or result.
- Keep output fields and section order stable. Return machine-readable output
  only when its schema is actually implemented; otherwise use a predictable
  human-readable report.
- Separate a computed value from a reference range or interpretation. A range
  is context-dependent and is not a diagnosis.
- Independently double-check medication, chemotherapy, dilution, and other
  safety-critical arithmetic. Do not turn a dose calculation into a dosing
  order.
- On failure, report the exact blocker and a manual formula or safe fallback
  only if it is supported. Mark the result `PARTIAL` when validation or
  execution did not complete.

## 4. Documents, Figures, and Lab Operations

Select the narrowest local tool and validate the input/output paths before
execution. Confirm whether the source contains PHI, whether overwrite is
allowed, and whether the operation is reversible. For PDFs, Word files, slides,
spreadsheets, OCR, and figure assembly, inspect structure and metadata without
silently publishing or uploading content. Preserve source ordering, page/slide
counts, table dimensions, units, and output locations; note when OCR, table
extraction, rendering, external fonts, or optional converters are unavailable.

For laboratory preparation and inventory operations, require concentration,
volume, molecular weight/purity/density where relevant, equipment limits,
solvent, safety constraints, and the intended protocol scope. Check units,
non-negative volumes, dilution sanity (`V1 <= V2` where applicable), final
volume, pipetting feasibility, and whether a hazardous-material or institutional
SOP review is required. Generated steps are planning aids, not authorization to
handle chemicals or biological materials.

## 5. Clinical Disclaimer Boundary

Use a concise disclaimer when a result could be mistaken for care guidance:

> This is a research-support calculation or workflow aid, not a diagnosis,
> prescription, treatment order, privacy certification, or substitute for
> qualified clinical/institutional review. Verify inputs, methods, and outputs
> independently before clinical, dosing, data-release, or publication use.

Tailor it rather than appending irrelevant boilerplate. A pure file-format
operation may need only a privacy and validation warning; a BMI/BSA or lab-unit
utility needs screening/reference-range limits; a de-identification workflow
needs manual QA and governance review; audit output needs explicit evidence and
unverified-surface labels.

## 6. Safe Catalog Querying

Treat catalog lookup as metadata discovery, not execution. Query only the
bundled/generated index and return canonical id, collection, category, short
fit rationale, input/output signals, dependencies, network/credential or
hardware requirements, privacy notes, and known limits. Prefer exact canonical
matches, then normalized token matches; make collection and category explicit
when IDs collide or descriptions overlap.

Safe query behavior:

- Use bounded local reads against the generated index; do not crawl arbitrary
  paths or import source-repository modules.
- Never evaluate query text as code or interpolate it into shell commands.
- Emit no user data, credentials, file contents, or hidden metadata in results.
- Report zero, one, or multiple matches deterministically and show the next
  disambiguating field instead of guessing.
- Mark stale/missing index metadata as an integrity issue and route to the
  catalog maintainer rather than silently synthesizing an entry.
- A match is a route suggestion, not proof that a dependency is installed, an
  API is available, a skill was executed, or a result is clinically valid.

The parent/root skill owns the catalog query and metadata-check scripts. This
sub-skill intentionally does not create or duplicate those helpers.
