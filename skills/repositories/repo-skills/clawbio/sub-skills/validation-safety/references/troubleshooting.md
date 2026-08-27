# Validation and safety troubleshooting

Use the smallest recovery that preserves evidence. Record the original status,
what was retried, and whether the retry changed the classification.

## Report, replay, and checksums

**`report.md` or `result.json` is missing**

- Confirm the selected skill's documented output contract and the exact output
  directory first; do not search arbitrary directories for a plausible report.
- Inspect stderr, exit code, and the output-directory preflight result.
- If required output was not written, classify FAIL. If the skill explicitly
  supports summary-only output or an optional structured envelope, record that
  limitation rather than fabricating a result.

**Checksum verification fails**

- Recompute SHA-256 over the exact listed path and compare the full digest.
- Check whether the input, external tool version, or output directory changed;
  replay into a fresh directory when the skill permits it.
- Check that every expected file exists. The shared writer omits missing files,
  so `sha256sum -c` can validate a partial list without proving completeness.
- Preserve the mismatch and environment/input differences in the handoff; do
  not rewrite the checksum file merely to obtain a green check.

**Replay command points to an unavailable tool or checkout**

- Read `environment.yml` or lock metadata and install only the documented local
  dependency through an approved path.
- Restore the original input files or update the replay command for the new
  local location, then rerun in a clean output directory.
- If an external resource is optional or unavailable, classify that step SKIP;
  if required for the declared result, classify FAIL or verification-blocked.

**Audit JSONL is absent or incomplete**

- Check whether the writer encountered a permissions or filesystem error and
  whether the run supplied scrubbed attributes.
- Do not retry with raw patient paths or identifiers just to fill the log.
- Mark audit completeness unknown and continue only if audit is not a strict
  acceptance gate for the selected workflow.

## Benchmarks and demos

**Baseline report is absent, malformed, or missing a harness/pass rate**

- Stop the baseline claim. The baseline checker treats a missing report or
  malformed report/baseline as fatal and a missing expected harness as a
  regression.
- Re-run only the bounded, approved benchmark producer after confirming inputs
  and dependencies. Do not replace a missing report with an empty JSON object.

**Benchmark rate dropped or harness errors increased**

- Preserve the report, baseline, tolerance, per-harness errors, and changed
  method/dependency information.
- A no-regression result is not a clean-benchmark result when the baseline
  carries existing debt. Review an intentional baseline update in the same
  change rather than changing the checker to ignore the regression.

**AD scorer reports FAIL, unknown genes, or false positives**

- Preserve tier breakdown, unknown list, negative-set false positives, and all
  configured minimums. Check gene normalization and field extraction before
  changing scientific code.
- Unknown genes are tracked separately by this fixture and do not count as
  negative controls; do not reinterpret that fixture-specific rule as a general
  precision rule.
- A scorer PASS is a benchmark-fixture result only. Do not turn it into a
  clinical or patient-level statement.

**Fine-mapping method is skipped, errors, or no winner is produced**

- Keep the seed, method registry, requested method list, exception text, and
  valid-method results.
- A deliberately unrequested optional method is SKIP; an unknown requested
  method must remain visible as skipped/unsupported; a required method error or
  no valid winner is FAIL.
- Do not select a winner from an error entry or treat a lower-compute substitute
  as equivalent when the required backend or method was not run.

**Nightly sweep shows `passed: false` or skipped skills**

- Inspect exit code, timeout, stderr tail, catalog metadata, and the explicit
  CI skip list. A heavy/network/credentialed entry in the skip list is SKIP,
  not PASS.
- A local demo that was attempted and exited non-zero is FAIL. A timeout is
  FAIL unless the case was declared optional and never attempted.
- Use the sweep only as orchestration evidence; it does not excuse unsafe
  `shell=True` execution or prove live API behavior.

**Mock API test gets 404, port conflict, or unexpected response shape**

- Use the context manager on a loopback port selected for the test and check
  `/health` before endpoint assertions.
- Verify the path prefix and fixture identifier; a 404 is useful negative-path
  evidence, not a network outage to hide.
- Keep real credentials and user data out of the mock server. A mock PASS covers
  client request/response handling, not a live service or current database.

## Action contracts and alerts

**A follow-up is stale or expired**

- Recompute or reload the skill state, compare the request's `state_schema` and
  `state_id`, and ask for a fresh action from a new run.
- The safe expected outcome is `lifecycle: expired`, no unsafe action, a
  sanitized message, and normal process exit. Record it as handled stale
  rejection, not as a scientific PASS.

**A `waiting` or `disabled` state has no action**

- Check whether the missing file, confirmation, local resource, or policy
  decision belongs to the skill. Do not invent shell commands in the adapter.
- Keep waiting/disabled visible with a concrete remediation or manual decision.
  If the resource is required and cannot be prepared, verification remains
  blocked or FAIL.

**An alert disappears or is rejected by normalisation**

- Validate schema `clawbio.contract_alert.v1`, allowed severity and kind,
  non-empty message, and the one-of `skill`/`action` remedy rule.
- Remove raw secrets, home paths, genomic values, and oversized evidence, then
  re-emit a concise sanitised alert. Dropped invalid alerts are not proof that
  the discrepancy was resolved.

## Safety and runner failures

**A flag was ignored or blocked**

- Inspect the selected skill's `allowed_extra_flags` and no-value set. Keep
  `--input`, `--output`, and `--demo` on the runner-owned path.
- Do not bypass the allow-list with shell metacharacters, an alternate flag
  spelling, or a value that contains another command. If the flag is a valid
  safe capability, add it through the owning skill's authoring and test path.

**A subprocess returns a warning but no output**

- Treat a required non-zero exit or missing required artifact as FAIL; inspect
  bounded stderr and the command list, then retry only after fixing the
  declared dependency/input/preflight condition.
- For optional tools, emit an explicit SKIP with reason and alternate path. Do
  not create an empty placeholder that looks like a successful analysis.

**A bot could read another user's upload or accepts an unsigned request**

- Stop the path. Require exact identity scoping, fail-closed sender checks, and
  a valid HMAC signature where applicable.
- Remove first/any/global fallbacks, invalidate leaked temporary files, and
  review logs for raw data or absolute paths. This is a security FAIL, not a
  recoverable warning.

**A report lacks the clinical disclaimer or contains raw patient data**

- Do not publish or present it as complete. Route the fix to
  [skill-authoring](../../skill-authoring/SKILL.md), add a focused regression test,
  and regenerate the report locally after checking the skill methodology.
- Keep the exact disclaimer and replace raw identifiers with aggregate or
  redacted evidence only where the owning methodology permits it.

## Escalation links

- Runner/output/profile behavior: [core-runner](../../core-runner/SKILL.md).
- Missing descriptor, catalog, test, or report contract:
  [skill-authoring](../../skill-authoring/SKILL.md).
- Cross-route integration or unresolved required backend: [clawbio](../../../SKILL.md).
