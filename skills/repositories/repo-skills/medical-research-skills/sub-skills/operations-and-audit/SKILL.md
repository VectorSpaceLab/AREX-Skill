---
name: operations-and-audit
description: "Route general medical utilities, privacy-sensitive operations,
  document and laboratory work, quality audits, safe catalog queries, and
  installation/export questions with explicit safety boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Operations and Audit

Use this route for the operational layer around the medical-research skill
catalog: safe selection of general utilities, PHI/privacy handling, local
document/figure/lab operations, audit interpretation, deterministic
calculations, and installation or export planning. Keep this file as a router;
the detailed rules live in the bundled references.

## Triage Before Doing Work

1. **Protect data first.** Treat patient, specimen, accession, EHR, lab-report,
   DICOM, or chart-shaped content as potentially PHI. Do not echo it, read
   unknown clinical files into context, or execute a query that may return
   rows. Apply the minimum-necessary and de-identification rules in
   [audit-and-safety.md](references/audit-and-safety.md).
2. **Identify the operation.** Separate a deterministic local utility from a
   document/figure/lab workflow, a quality audit, a catalog lookup, or an
   installation/export request. Confirm inputs, output location, dependencies,
   overwrite policy, and whether external services are involved.
3. **Select the smallest catalog skill.** Query the generated catalog index by
   canonical skill id, collection, category, capability, or input format when
   a lookup helper is available. Do not invent a skill, capability, package,
   result, or compliance status. Use the routing table below for specialist
   work.
4. **Validate before execution.** Prefer deterministic, local, reversible
   operations. Use stable output fields, explicit units/formulas, bounded input
   ranges, and a validation summary. Stop on missing required inputs or an
   unsupported dependency rather than silently guessing.
5. **Apply clinical boundaries.** A calculator, converter, de-identification
   helper, document tool, or protocol utility is research support—not a
   diagnosis, prescription, treatment recommendation, legal certification, or
   release approval. Include an appropriate disclaimer and require qualified
   human review where the result could affect care, dosing, privacy, or release.

## Route Map

| User need | Route here | Hand off when |
|---|---|---|
| General calculator, unit conversion, date/gestational-age helper, buffer/dilution or other bounded utility | Use the relevant catalog skill after validating units, ranges, formula, and output contract | A study design decision is needed: [protocol-design](../protocol-design/SKILL.md); statistical/model execution: [data-analysis](../data-analysis/SKILL.md) |
| PHI prompt, clinical file/database access, text de-identification, DICOM metadata, privacy review | Apply the privacy gate and route to the relevant privacy skill; require manual QA | Evidence retrieval: [evidence-insight](../evidence-insight/SKILL.md); analysis of de-identified data: [data-analysis](../data-analysis/SKILL.md) |
| PDF, Word, spreadsheet, slide, image/figure, poster, OCR, figure assembly, lab inventory or preparation operation | Select the narrow local document/figure/lab skill and confirm dependencies and file targets | Manuscript prose, claims, citations, or submission adaptation: [academic-writing](../academic-writing/SKILL.md); analysis: [data-analysis](../data-analysis/SKILL.md) |
| Structural or research-quality audit of a skill | Apply the two veto gates and audit workflow in [audit-and-safety.md](references/audit-and-safety.md) | Specialist category scoring or scientific-content review may require the owning sibling route and human reviewer |
| Catalog discovery or task-to-skill selection | Use the root catalog index and its bundled safe query/check helpers, if present; return canonical id, collection, category, fit, requirements, and limits | Detailed execution belongs to the selected catalog skill, not this router |
| OpenClaw installation, compatible-agent export, or destination collision | Read [installation-and-export.md](references/installation-and-export.md); treat installation as an explicit, reference-only operation | Never install implicitly; ask for authorization and target details before side effects |

Use the sibling handoff only after stating what was learned, what remains
unverified, and which inputs the next route needs. Do not duplicate a sibling's
specialist workflow in this route.

## Compact Operating Contract

- **Inputs:** a task description, selected skill or operation, local files only
  when their privacy status is known, required parameters, and an explicit
  output target for writes.
- **Outputs:** a bounded plan or local result with objective, inputs and
  assumptions, selected path, validation status, risks/limits, and next checks.
- **Safe failure:** name the exact missing field, unsupported pair, unavailable
  dependency, collision, or privacy uncertainty; provide the minimum safe
  recovery step. Label partial work as `PARTIAL`.
- **No hidden side effects:** do not download data, call APIs, install packages,
  overwrite files, expose PHI, or restart gateways without explicit authority
  and a reviewed target.

For full rules, consult:

- [audit-and-safety.md](references/audit-and-safety.md) for veto gates, PHI,
  deterministic utilities, and clinical disclaimers.
- [installation-and-export.md](references/installation-and-export.md) for the
  OpenClaw reference contract and safe export planning.
- [troubleshooting.md](references/troubleshooting.md) for bounded recovery of
  install, dependency, input, CLI/API, document, figure, and lab failures.
