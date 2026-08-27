# Safety and privacy gates

Apply these gates before accepting a ClawBio run, replay, benchmark, action,
or integration result. They are operating constraints derived from the
repository's local-first architecture, runner allow-list, bot security helper,
and security audit. A domain skill may impose stricter controls.

## Local-first and clinical boundaries

- Process patient or user genetic data locally by default. Do not upload raw
  genotypes, VCFs, sample identifiers, report contents, or credentials to a
  remote API, chat service, mock server, or benchmark collector.
- Network access is conditional, not implied: the architecture documents
  optional public literature/structure lookups and package installation, while
  explicit consent is required before data leaves the machine. Follow the
  selected skill's methodology and consent contract; no external lookup is a
  prerequisite for a local-only PASS.
- A loopback mock API with fixture data is an offline contract test, not a live
  service and not a license to point a patient's input at a remote endpoint.
- Keep input and output paths scoped to the intended working area. If a service
  or bot accepts arbitrary paths, add a path containment check, size/type limit,
  and filename sanitization before exposing it to an untrusted sender.
- Every user-facing scientific report must include the exact disclaimer from
  [validation-contracts.md](validation-contracts.md): ClawBio is a research and
  educational tool, not a medical device, and does not provide clinical
  diagnoses. A benchmark, score, or automated report cannot replace a clinician.
- Report missing genotype, unknown phenotype, unsupported build, low coverage,
  failed subprocess, and uncomputed metric as `NOT_TESTED`, `indeterminate`,
  `NaN`/missing, `FAILED`, or an explicit skip according to the owning skill—not
  as normal, zero risk, or a fabricated estimate. Follow the source
  methodology's exact terminology.

## Runner and flag filtering

The runner's `run_skill` builds a subprocess command as an argument list and
uses `subprocess.run(..., timeout=..., cwd=...)`; it does not invoke a shell for
skill execution. Keep that property intact.

`extra_args` are filtered against the selected skill's `allowed_extra_flags`
(and, for flags without a value, an explicit no-value set). The core flags
`--input`, `--output`, and `--demo` are always blocked from this pass-through.
For nf-core wrappers, underscore and hyphen spellings are canonicalized before
allow-list matching; this is compatibility normalization, not a permission
expansion. An unlisted flag must be rejected or omitted with a visible reason,
never forwarded as an arbitrary command fragment. A value is forwarded only in
the context of an allowed flag.

Do not infer that an allowed pipeline flag authorizes remote input, cloud
execution, credentials, or data export. Apply the skill's explicit consent and
preflight gates, and classify unavailable optional resources as SKIP. Never
circumvent the whitelist by adding shell syntax, alternate flag spellings, or
`--input`/`--output` inside an extra-argument value.

The nightly demo sweep is not a safe generic subprocess wrapper: its source
implementation uses `shell=True`, runs catalog commands in sequence, and may
encounter network-heavy or credentialed skills. Do not copy it into a runtime
skill or run it against an untrusted catalog. Prefer the bundled static
validator or a reviewed list-form command with a timeout and no external side
effects.

## Subprocess, audit, and bot controls

- If a subprocess is required, pass a list of executable and arguments, set a
  timeout, capture bounded diagnostics, and check exit status and required
  output files. A warning after a failed required command is not success.
- `tool_call` also uses list-form subprocess execution, but its command tokens
  and attributes are written to the local audit span. Scrub paths, sample IDs,
  raw data, and secrets before logging; do not treat an audit record as a safe
  place for patient data.
- The audit writer is best-effort and may suppress `OSError`. Missing audit
  evidence must therefore remain a limitation, not be silently upgraded to a
  clean audit.
- Bot sender authorization fails closed: WhatsApp signatures require a
  configured secret and constant-time HMAC match; missing or malformed input is
  rejected. `is_sender_allowed` denies empty identities unless an explicit
  configured admin, allow-list entry, or operator-selected public mode applies.
- `scoped_get` returns only the exact authenticated user's entry and has no
  first/any fallback. Never use a global uploaded-file slot for genomic data.
- Do not echo absolute server paths, filenames containing identifiers, raw
  genotypes, request payloads, or credentials into Telegram, Discord, reports,
  alerts, or chat summaries. Contract-alert normalisation clamps and redacts
  common secrets and home paths, but callers remain responsible for input
  minimisation.

## Validation of generated operating skills

The bundled `scripts/validate_runtime.py` is a read-only, standard-library
check for the generated skill tree. It verifies:

- each root or sub-skill `SKILL.md` has the required exact frontmatter shape,
  including a double-quoted description, matching `name`,
  `disable-model-invocation: true`, and `metadata.disco-role: operating`;
- relative Markdown links resolve inside the generated root skill tree (or are
  reported as missing during an intentionally incomplete draft); and
- obvious absolute checkout paths, local environment markers, credential-like
  assignments, and raw secret tokens are absent from runtime files.

This helper does not run a native test, demo, benchmark, subprocess, network
request, or import. It is a static gate only. A strict link PASS requires the
whole root graph to be present, including sibling routes such as
[core-runner](../../core-runner/SKILL.md) and
[skill-authoring](../../skill-authoring/SKILL.md).

## Evidence and action safety

A validation record should name the exact input class, skill version or method,
required backend/resource, output artifacts, and status. It should distinguish:

- **completed and checked** from **completed but not independently checked**;
- **optional unavailable** from **required unavailable**; and
- **stale/expired action rejected safely** from **analysis failed**.

Contract alerts describe route/state/policy discrepancies, not findings. Keep
raw values out of `evidence`, use a stable alert kind, and provide only
non-executed remedies. `blocking` is not a permission grant and a remedy is not
an instruction to shell out.
