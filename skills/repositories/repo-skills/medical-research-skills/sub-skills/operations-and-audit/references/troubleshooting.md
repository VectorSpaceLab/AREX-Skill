# Troubleshooting Reference

Use bounded recovery. Report what was checked, what failed, what remains
unverified, and the minimum next action. Never hide a partial result or widen a
command's privileges to make it pass.

## Routing and catalog lookup

| Symptom | Likely cause | Safe recovery |
|---|---|---|
| No catalog match | Query uses prose, alias, or an unsupported capability | Normalize to task, input format, category, or canonical id; return zero-match status and ask one disambiguating question. Do not invent a skill. |
| Too many matches | Broad term such as “medical analysis” or “PDF” | Filter by collection, category, data format, local/API mode, privacy needs, or deterministic requirement; show the stable top candidates and differences. |
| Duplicate/ambiguous id | Similar names across collections or stale metadata | Report collection and category; inspect generated index metadata; stop if index integrity is uncertain. |
| Match but unavailable tool | Optional package, R/Node binary, GPU, model, API, or credential missing | Separate routing from readiness. Provide a dependency-aware plan or sibling route; do not claim execution. |
| Query helper errors | Missing index, malformed JSON, unsafe input, or path issue | Validate the generated index and bounded arguments; use a read-only fallback or report the blocker. Do not run arbitrary source scripts. |

## PHI, privacy, and clinical boundaries

| Symptom | Safe recovery |
|---|---|
| User pasted a patient-shaped note, image, row, or identifier | Do not echo or summarize it. Name only the detected category, request redaction or synthetic-data attestation, and offer a generic/template path. |
| A requested database/file read may return PHI | Do not execute. Offer schema-only inspection, an identifier-free projection, aggregate query, row count, or a locally-run command whose output is de-identified before sharing. |
| De-identification completed but release is requested | Mark as unverified until manual QA, contextual re-identification review, burned-in pixel/metadata review, and institutional approval are complete. |
| User asks for diagnosis, prescription, dose order, or treatment decision | Stop the utility route. Provide only bounded calculation/context if appropriate, state the clinical disclaimer, and route to qualified clinician/institutional review. |
| Clinical disclaimer would be misleadingly broad | Tailor it to the operation: calculation/screening, privacy/release, document processing, audit, or lab safety. Do not imply legal or clinical certification. |

## Deterministic calculator and lab utility failures

| Symptom | Likely cause | Safe recovery |
|---|---|---|
| Missing or nonnumeric input | Required parameter absent, malformed, non-finite, or wrong unit | Name only the missing/invalid field; request the minimum correction. Do not fill it with a default that changes meaning. |
| Unsupported unit pair or formula | Catalog skill does not implement requested conversion/method | List supported pairs or methods and stop; provide a manual formula only when documented. |
| Implausible height, weight, volume, concentration, or age | Unit confusion or data-entry error | Reconfirm units and bounds; do not reinterpret silently. |
| Dose or dilution result differs | Formula, units, rounding, purity, or final-volume convention differs | Show normalized inputs and formula; independently recalculate and require pharmacist/qualified reviewer for safety-critical use. |
| Reproducibility concern | Random method, hidden precision, changing reference range, or unstable dependency | Pin method/version where possible, expose rounding and seed, rerun identical fixtures, and mark unresolved nondeterminism. |
| Script unavailable or crashes | Optional dependency, malformed path, or source-specific assumption | Run only a safe parser/help check if authorized; report exact failure and give a documented manual fallback. Never claim a result. |

## Document, figure, and lab operations

| Symptom | Likely cause | Safe recovery |
|---|---|---|
| PDF text/table extraction is empty or distorted | Scanned pages, complex layout, unsupported encoding, or no OCR | Label extraction partial; use approved local OCR or manual review, preserve page references, and do not infer missing values. |
| Word/slide output renders differently | Missing Node/Python package, font, template, or renderer | Validate dependencies and output metadata; use a stable template or export preview locally; do not overwrite the source without approval. |
| Figure labels/legend or slide titles are inconsistent | Source data and manuscript/deck versions drifted | Route to figure/academic-writing sibling checks, compare identifiers/units/order, and keep the inconsistency visible. |
| OCR or image workflow may contain PHI | Image contents are not known to be de-identified | Stop model-context processing; request redaction or local processing and require pixel-level/manual QA. |
| Lab protocol lacks equipment or hazard constraints | Inputs are incomplete or SOP-specific | Ask for the minimum missing parameters and route hazardous steps to institutional SOP/EHS review. |
| Output path would overwrite or escape the workspace | Collision, traversal, or unclear destination | Stop, canonicalize and validate the explicit target, and request permission before replacement. |

## Installation and export

| Symptom | Safe recovery |
|---|---|
| Remote installer or Git clone fails | Report network/Git failure; do not substitute an untrusted mirror or execute a different command. Retry only with authorization. |
| Destination already exists | Preserve it and report a collision. Use dry-run or ask for explicit per-target replacement; never silently merge. |
| User requests “install all” without a target | Ask for target agent, destination, revision, scope, and collision policy; offer an inventory-only dry run. |
| Files copied but agent does not see them | Verify destination layout, frontmatter, permissions, and agent refresh/restart separately. Do not report runtime readiness from file presence alone. |
| Export contains source links or artifacts | Remove checkout-dependent links, logs, caches, and test reports; replace with bundled self-contained references or mark the capability unavailable. |

## Escalation template

```text
STATUS       : PASS / PARTIAL / BLOCKED
Operation    : <bounded task>
Inputs       : <validated fields and privacy status>
Checked      : <static, parser/help, local execution, or manual checks>
Blocked by   : <exact error or missing authorization>
Safe result  : <verified result, plan, or no result>
Residual risk: <privacy, clinical, dependency, rendering, or side-effect risk>
Next check   : <minimum safe recovery action and owner>
```
