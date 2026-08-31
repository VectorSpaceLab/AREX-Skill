# Publication checklist

- [x] Runtime root `skills/huggingface-hub/SKILL.md` exists and is router-like.
- [x] Five sub-skills have canonical lowercase-hyphen IDs matching directory and frontmatter names.
- [x] Every runtime SKILL.md has double-quoted description, `license: Apache-2.0`, `disable-model-invocation: true`, and `metadata.disco-role: operating`.
- [x] Runtime references and scripts are self-contained and linked from nearby routers.
- [x] No runtime link points to original source docs, tests, scripts, examples, checkout paths, or private environment paths.
- [x] `references/repo-provenance.md` records commit/tag/version and relative evidence paths without local environment details.
- [x] `references/repo-routing-metadata.json` is minimal v2 and matches the external routing decision.
- [x] GitHub CLI license lookup is recorded in `reports/license-resolution.json`; six runtime files use the resolved value.
- [x] Integration maps exist for coverage/depth, native candidates/backend plan, source scripts, troubleshooting, long-tail gaps, and difficult cases.
- [x] 15 usability case directories are outside runtime; each has a copyable prompt, reviewer README, and assertions.
- [x] Self-refine iteration and static verification reports exist under `reports/`.
- [x] Bundled helper `--help`/mock/local checks pass; no credentialed or destructive helper is included.
- [x] Selected safe native unit/mocked tests pass; unsafe/network/privilege-specific outcomes are explicitly reported, not counted as passes.
- [x] No required backend is blocked; optional CUDA smoke passed and no GPU claim is made.
- [x] No managed import was performed, honoring the user's “not import” instruction.
- [ ] Optional future action: if import is later requested, re-check the current source commit and digest, then run the dedicated locked importer with `skills/disco/routing_decision/classification.json`.
