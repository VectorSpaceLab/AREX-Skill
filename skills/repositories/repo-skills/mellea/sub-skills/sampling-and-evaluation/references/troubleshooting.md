# Troubleshooting and failure triage

Classify the failure before increasing a retry budget. A retry only addresses
stochastic generation or a repairable prompt; it does not fix malformed data,
missing dependencies, an incompatible backend, or a faulty verifier.

## Fast triage table

| Symptom | Likely cause | Deterministic next check | Safe response |
|---|---|---|---|
| `loop_budget`/`concurrency_budget` error | Non-positive budget | Inspect constructor values and hook overrides | Set each to at least 1; do not hide the error |
| `success=False` with a selected output | All attempts failed requirements | Iterate `sample_validations`; print requirement descriptions/reasons | Fix the validator/prompt or choose an explicit fallback policy |
| Repair text is absent | Action is a `CBlock`/MOT, or no reason was returned | Check action type and `ValidationResult.reason` | Use an `Instruction`/`ChatContext` strategy or improve reasons |
| Multi-turn assertion | Context is not `ChatContext` | Check session/context construction | Use `ChatContext` only when conversation repair is intended |
| More requests than expected | Concurrency or MBRD multiplier | Compute budget bounds from `strategies.md` | Lower concurrency/sample count; inspect provider limits |
| Same failure repeats in SOFAI | No improvement or poor feedback | Compare failed requirement/reason/score tuples | Escalate, change feedback mode, or fix the verifier |
| Budget forcing assertion | Backend is not Ollama or tool calls enabled | Inspect backend class and `tool_calls` | Use standard sampling or the documented Ollama-only route |
| Budget forcing `usage=None` | Backend lacks per-call token counts | Inspect `generation.usage` | Disable budget forcing or use a backend exposing usage |
| MBRD import failure | Optional comparison dependency unavailable | Import the selected strategy in the target environment | Install the needed package or use deterministic custom voting |
| Python validator passes static code unexpectedly | Static tier does not execute | Inspect `PythonExecutionReq` tier | Treat static as syntax/import inspection; select a policy tier for execution |
| Forbidden import bypass | Dynamic import or code execution path | Remember AST allowlist scope | Use a Docker capability policy; never treat allowlist as sandbox |
| Empty `examples` error | Dataset schema violation | Validate object fields and list length | Fix dataset before model calls |
| Test inputs disappear | Example has no user role | Inspect role values and filtering | Add a user message; preserve aligned targets/IDs |
| Judge says `score` but parse returns none | Not parseable as JSON/recognized text | Run `parse_judge_output` on raw text | Constrain judge prompt/output or retain as failed evidence |
| Judge pass rate changes between runs | Model, seed, temperature, or judge drift | Record all backend/model/options and raw verdicts | Label qualitative; do not call it a regression without controls |
| `m eval` writes no useful results | Files failed load or all tests errored | Run dataset parsing and a single test first | Use `--continue-on-error` deliberately and report skipped errors |
| CLI `threshold` has no effect | Native CLI has no threshold option | Check `m eval run --help` | Apply threshold in post-processing or Python, not a guessed flag |

## Requirement debugging

1. Run the validator directly on a fixed `ModelOutputThunk`/`Context` when
   possible. This separates verifier bugs from model behavior.
2. Assert the return type is `ValidationResult`; use `as_bool()` or `bool()`.
   Do not use the nonexistent `.result` property in runtime code.
3. Include a concise, actionable `reason` on failure. The reason is fed into
   repair strategies and may contain generated data; redact secrets.
4. Test empty output and malformed output explicitly. `simple_validate` can
   receive an empty string when no usable output is present.
5. Compose deterministic requirements before judges so cheap failures stop
   downstream calls and produce clear diagnosis.

For LLM-as-a-judge, capture a `GenerateLog` or raw judge output when available.
Distinguish three failures: the candidate violates the requirement, the judge
misclassified it, or the verdict parser rejected the judge format. Change one
of prompt, validator, judge model, or parser contract at a time.

## Evaluation dataset debugging

`TestData` requires a non-empty `examples` list. Check that every message has a
string `role` and `content`, that at least one input message uses role `user`,
and that target messages intended as references use role `assistant`. The
loader skips no-user examples rather than raising, so compare source-example
counts with loaded input counts.

Before a live run:

- parse all files with `TestBasedEval.from_json_file()`;
- check every test ID/name is stable and unique enough for your report;
- check targets are aligned to inputs after filtering;
- run `m eval run --help` and validate the configuration script;
- use one small case and a known backend before a benchmark batch.

## Generated-code failure handling

Never “fix” a failing generated-code gate by switching to `local_unsafe` or
removing import limits without recording the risk decision. Start with static
checks. For execution, use a capability policy, bounded timeout/output, and
Docker where code is not trusted. Keep generated code out of logs when it may
contain secrets or personal data. A validator must not write files, invoke a
shell, contact a network service, or mutate production state merely to decide
whether a config is valid.

## Metrics interpretation

Pass rate is `passed_inputs / total_count` for the records that reached result
construction. An empty result set has pass rate `0.0`. Do not average per-test
rates when test sizes differ; use aggregate counts. Sampling and requirement
telemetry counters are operational counts and may include validation attempts
that did not become final results. Cost metrics may be absent for local/private
models without pricing data. Missing metrics are not zero quality.

## Escalation boundary

If the issue is backend construction, credentials, model serving, command
installation, or general server lifecycle, hand off to `serving-and-cli` or
`backends-and-models`. If it is hooks, exporters, OpenTelemetry configuration,
or custom extensions, hand off to `observability-and-extensions`. Keep this
route focused on sampling/evaluation semantics and evidence.
