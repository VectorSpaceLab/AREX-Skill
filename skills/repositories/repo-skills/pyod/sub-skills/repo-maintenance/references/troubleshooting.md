# Repo Maintenance Troubleshooting

Read this when a focused maintainer check fails or a requested maintenance
workflow crosses optional dependency, packaged skill, CLI, docs rendering, or
release boundaries.

## Packaged skill drift

| Symptom | Likely cause | Recovery |
|---|---|---|
| `scripts/regen_skill.py --check` prints files that would regenerate | KB-derived blocks are stale after a knowledge-base or generator change | Run `python scripts/regen_skill.py`, review the diff, and confirm only marked KB-derived blocks changed. Then run the packaged skill test stack. |
| A Markdown line "looks like a KB-DERIVED marker" but marker tests fail | Marker typo, wrong spacing, nested marker, unmatched section name, or prose accidentally resembling a marker | Use exact `<!-- BEGIN KB-DERIVED: section-name -->` and matching `<!-- END KB-DERIVED: section-name -->` lines. Do not nest generated blocks. |
| Unknown detector-like backtick token in skill prose | Typo in detector name, removed/renamed KB entry, or a non-detector symbol that looks like a detector | Prefer fixing the token or removing backticks for free prose. Add an allowlist entry only for legitimate non-detector symbols, never for a live KB detector. |
| Stale detector-count claim | Hand-written count outside KB-derived blocks no longer matches live buildable KB | Update the count claim or make it generated. Planned detectors should not inflate buildable totals. |
| `test_skill_api_refs.py` reports bad `state.X` or `engine.X` | Skill prose names an invented or stale ADEngine/state field, nested key, method, or keyword argument | Fix the prose to the live API. If the API truly changed, update the API-reference test's ground-truth collection with focused evidence. |

## Generator failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Unknown KB-derived section name | Markdown contains a section marker not present in the generator's renderer map | Add a renderer for the new section or rename the marker to a supported section. |
| Raw dependency token appears as `pyod[torch_geometric]` instead of `pyod[graph]` | `_REQUIRES_TO_EXTRA` mapping is stale | Update the mapping to the public extra exposed by package metadata and run `test_regen_skill.py`. |
| Generated body shows raw dict repr such as `{'time': ...}` | Complexity or paper formatter is broken for the current KB schema | Fix formatter helpers and run the generator tests before regenerating skill files. |
| Hand-written prose changed after regeneration | Marker regex matched too broadly or markers are malformed | Revert unintended prose changes, fix marker syntax or generator regex, then re-run `--check`. |

## CLI and installer regressions

| Symptom | Likely cause | Recovery |
|---|---|---|
| `pyod --help` lacks expected subcommands | `pyod.cli` parser wiring or entry-point target changed | Run `python -m pytest pyod/test/test_cli.py::test_pyod_cli_help -q` and inspect `pyod.cli:main`. |
| `pyod info` exits non-zero in a base install | CLI imported optional MCP server/runtime too eagerly or detector-count code raised | Probe optional modules via `importlib.util.find_spec` without importing server code; run `test_pyod_info_does_not_exit_without_mcp`. |
| `pyod install skill --project` prints Claude-only activation text | Project-local install message regressed from agent-neutral wording | Run `test_install_skill_project_message_is_agent_neutral` and update shared installer output. |
| Installed `od-expert` lacks `references/` | Installer copied only `SKILL.md` or package data omitted references | Ensure `shutil.copytree` copies the tree and package data includes `references/*.md`; run `test_pyod_install_skill_copies_references_tree`. |
| `--skill od_expert` installs or prints underscore form | Normalization or install-dir mapping broke | Keep `_INSTALL_DIRNAME_MAP` synchronized and run canonical-name installer tests. |

## MCP optional dependency behavior

| Symptom | Likely cause | Recovery |
|---|---|---|
| `import pyod.mcp_server` exits when `mcp` is absent | Module-level optional dependency check calls `sys.exit` or imports missing parent unsafely | Keep import side-effect free; `main()` may return non-zero when runtime extra is absent. Run `test_mcp_server_imports_without_mcp_extra`. |
| `_check_mcp()` raises `ModuleNotFoundError` when `mcp` parent is missing | Probing nested module directly without checking parent package | First probe `mcp`, then `mcp.server.fastmcp`, and catch `ModuleNotFoundError`. |
| Positive MCP tool registration fails | Fake-MCP registration order or tool list changed | Run `test_main_registers_all_ten_tools_in_order`; update tests only when the public tool contract intentionally changes. |

## Optional-extra tests fail in a base environment

Do not immediately install every extra. First classify the failure:

- If the edited area does not require the extra, mark the optional-backend test
  skipped or run the corresponding base import-safety test.
- If the edited area is the optional backend, install only that extra and its
  hardware/runtime prerequisites after confirming the user authorizes the
  environment change.
- If an external service, model download, browser, credential, or GPU is needed,
  ask before proceeding and record the limitation if not authorized.

## Docs rendering helper fails

| Symptom | Likely cause | Recovery |
|---|---|---|
| `render_agentic_demo.py` reports Playwright missing | Browser rendering dependencies are not installed | Ask whether to install `playwright` and Chromium. Do not install browsers by default. |
| Screenshot output changed unexpectedly | HTML demo, CSS, viewport, device scale, or browser version changed | Review the visual diff intentionally; this is a docs artifact update, not a code test. |
| Running the helper writes docs figures when not expected | The helper is mutating by design | Only run it when updating the agentic demo figure. For routine checks, use focused docs/API tests instead. |

## Packaging metadata issues

| Symptom | Likely cause | Recovery |
|---|---|---|
| New skill cannot be installed | Missing package-data entry, missing data-only subpackage marker, or missing installer map | Add package data for `*.md` and `references/*.md`, update `_INSTALL_DIRNAME_MAP`, and run installer tests. |
| New optional detector extra renders wrong install hint | PyOD extra name and KB `requires` token are out of sync | Update `pyproject.toml` extras, KB metadata, and generator mapping together. |
| Tests pass from checkout but installed package lacks JSON/skill files | Package-data or manifest omission | Verify package-data rules for `pyod.utils.model_analysis_jsons`, `pyod.utils.knowledge`, and packaged skills. |

## Release/publishing boundary

If the user asks to publish, upload to PyPI, push tags, delete artifacts, or use
credentials, stop and request explicit maintainer approval with the exact target
and command. Safe pre-release checks, metadata inspection, and local focused
tests can proceed; external publication cannot.
