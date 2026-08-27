# Native Test Selection

| Changed surface | First focused tests | Broaden when |
| --- | --- | --- |
| Mainline skill catalog or group dependencies | `tests/test_skill_groups.py`, `tests/test_skill_picker.py` | A new skill, group, dependency edge, or picker UI changed. |
| Claude installer | `tests/test_install_aris_selective.py`, `tests/test_install_aris_replace_link.py`, `tests/test_install_aris_tools_symlink.py` | Manifest, migration, or platform behavior changed. |
| Codex installer/mirror | `tests/test_codex_install_update.py`, `tests/test_codex_skill_mirror.py` | Overlay generation or update semantics changed. |
| Copilot installer | `tests/test_copilot_install.py`, `tests/test_copilot_native_evidence.py` | `.github/skills` or native evidence changed. |
| Research Wiki/helper resolution | `tests/test_research_wiki_helper_resolution.py` plus targeted `test_research_wiki_*` files | Schema, encoding, fetch fallback, graph, or artifact formats changed. |
| Watchdog | `tests/test_watchdog.py`, `tests/test_watchdog_loop.py` | Session, GPU, download, alert, or daemon loop logic changed. |
| Provenance/review acceptance | `tests/test_provenance.py`, `tests/test_reviewer_pins.py` | Model family, verdict, sidecar, or reviewer route changed. |
| Generic/MiniMax/manual/Feishu MCP | matching `test_*server.py` and integration test | JSON-RPC, config, retry, local HTTP, or mocked provider behavior changed. |
| Paper/audit helpers | `tests/test_verify_paper_audits.py`, audit-specific tests | Verdict schema or submission gate changed. |

## Safe Execution Rules

- Use the smallest deterministic test file first.
- Prefer temporary fixtures and mocks.
- Do not run network-backed tests, GPU jobs, or credentialed MCP flows by default.
- Record optional-backend skips explicitly rather than calling them passes.
- When a test is a final ground-truth candidate, run it only after the generated repo skill has been integrated.
