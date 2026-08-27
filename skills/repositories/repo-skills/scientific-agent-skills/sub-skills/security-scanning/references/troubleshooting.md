# Security Scan Troubleshooting

## Missing API key

**Symptom:** The PR scanner says `SKILL_SCANNER_LLM_API_KEY` is unavailable and writes a skipped comment.

**Meaning:** This is expected in fork PRs and local no-key runs. It is not a scan finding and does not imply the changed skill is safe or unsafe.

**Next step:** If a maintainer wants LLM-backed scanning, re-run from a trusted context with the key set. Do not print or commit the key.

## Env-var exfiltration finding

**Common false-positive class:** A skill reads its own service API key and sends requests to that same service. That is service authentication, not automatically exfiltration.

**Verification:** Check the variable names and destination hosts in the cited script/reference. If the destination is unexpected or configurable without host/scheme guard, investigate as real risk.

## `eval` or `exec` finding

**Common false-positive class:** Static/LLM rules match substrings inside ordinary identifiers such as `retrieval`, `evaluate`, `executor`, or PyTorch `model.eval()`.

**Verification:** Use an AST or direct source read to confirm whether `eval()`, `exec()`, `compile()`, `os.system()`, `os.popen()`, `shell=True`, or unsafe environment forwarding actually exists.

## Confabulated files

**Symptom:** The report cites Python or shell files in a skill that ships only Markdown.

**Verification:** Run a filesystem inventory for the skill. If the cited files do not exist, record the finding as invalid rather than editing unrelated content.

## Markdown subprocess or HTTP snippets

Scanner rules may flag documented `subprocess` or HTTP examples. Verify whether the example is a safe argument-list form, bounded service call, or a real instruction to execute untrusted input. Fix only the real unsafe instruction.

## Real finding workflow

When a finding is verified:

1. Preserve the skill's legitimate documented behavior when possible.
2. Remove or gate unsafe actions.
3. Add explicit authorization, host allowlists, dry-run defaults, path quoting, or bounded input validation as appropriate.
4. Add or update tests when bundled scripts changed.
5. Record the real issue and fix in triage notes so future scans are interpretable.
