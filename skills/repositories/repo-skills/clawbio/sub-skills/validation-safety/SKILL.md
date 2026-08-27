---
name: validation-safety
description: "Validate ClawBio runs, benchmarks, reproducibility records, action
  contracts, and privacy or security boundaries without overstating skipped or
  unsupported work."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Validation and safety

Use this route when a ClawBio result needs a truthful scientific status,
replay/checksum review, benchmark interpretation, contract-alert handling, or a
privacy and subprocess safety check. It is a validation route, not a source of
new biomedical claims: interpret results only against the selected skill's
methodology and documented evidence.

## Route

1. Establish the run scope and required evidence using
   [validation-contracts.md](references/validation-contracts.md). Separate
   completed, failed, and deliberately skipped work before reading metrics.
2. Apply the local-first, clinical-disclaimer, data-minimisation, and flag or
   subprocess gates in [safety-and-privacy.md](references/safety-and-privacy.md).
3. Check reports, structured results, replay commands, checksums, audit records,
   and benchmark outputs. Treat missing evidence as unknown or failure of the
   claimed gate, never as a normal result.
4. For structured follow-ups, validate lifecycle, state identity, request
   schema, and sanitised contract alerts. A stale request may be safely handled
   with an expired state, but it is not a successful scientific analysis.
5. Recover from the nearest procedure in
   [troubleshooting.md](references/troubleshooting.md), then hand off the
   exact PASS, SKIP, or FAIL classification and unresolved limits.

## Boundaries and links

- Use [core-runner](../core-runner/SKILL.md) for invocation, output-directory,
  profile, and runner behavior; return here for the validation gate.
- Use [skill-authoring](../skill-authoring/SKILL.md) when a missing disclaimer,
  result field, test, flag declaration, or catalog contract requires a source
  skill change.
- The root route is [clawbio](../../SKILL.md); do not bypass it when a case
  crosses runner, routing, integration, or authoring boundaries.
- The bundled [static validator](scripts/validate_runtime.py) checks generated
  skill frontmatter, internal links, and obvious privacy/path leaks without
  running demos, native tests, network calls, or benchmark jobs.

## Non-goals

Do not download benchmark-scale data, use external credentials, send patient or
raw genetic data to a service, execute destructive actions, or turn an optional
GPU/network skip into a pass. Do not infer clinical diagnosis, treatment, or
risk from a benchmark score.
