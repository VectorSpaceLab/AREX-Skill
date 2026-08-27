# Troubleshooting

## Invalid Tool XML

Symptoms:

- XML parser reports mismatched tags, invalid tokens, undefined entities, or line/column errors.
- Galaxy fails to load a tool or the tool disappears from the panel.
- `galaxy-tool-format --diff` returns unchanged content because XML parsing failed.

Recovery:

1. Parse the XML first with `python scripts/inspect_tool_util.py --tool-xml path/to/tool.xml`.
2. Fix well-formedness before schema or runtime checks.
3. Run `python -m galaxy.tool_util.format --diff path/to/tool.xml` to see indentation-only changes.
4. Check upgrade advice with `python -m galaxy.tool_util.upgrade.script path/to/tool.xml --profile-version VERSION`.
5. If Galaxy still fails to load the tool, inspect `id`, duplicate tool IDs, profile compatibility, macros, requirement declarations, and tool panel configuration.

Do not treat formatter success as semantic validation. A formatted XML file can still refer to missing inputs, outputs, data tables, macros, or dependencies.

## Invalid Test Format

Symptoms:

- YAML validation raises model errors.
- A test file is a mapping when Galaxy expects a list of test cases.
- Assertions use the wrong nesting, such as `asserts` outside an output block.
- A workflow test references a job field that does not match the workflow input.

Recovery:

```bash
python -m galaxy.tool_util.validate_test_format path/to/tests.yml
python scripts/inspect_tool_util.py --test-file path/to/tests.yml
```

Then check:

- top-level YAML should usually be a list of test cases;
- each test should have `job`/`inputs` and `outputs` in the expected shape;
- assertions should be lists with `that: has_text`, `that: has_line`, or another supported assertion;
- `expect_failure: true` belongs at the test-case level;
- structural validation does not prove names match the tool/workflow.

## Tool Assertion Failures

Symptoms:

- `galaxy-tool-test` reports failed, errored, skipped, or missing output tests.
- Output text assertions fail even though the job completes.
- Metadata or collection assertions do not match API responses.

Recovery:

1. Re-run one test index rather than the full suite: `galaxy-tool-test --tool-id TOOL_ID --test-index N ...`.
2. Use `--output-json` and `--output` to capture metadata and downloaded outputs.
3. Confirm command determinism, quoting, locale-sensitive output, and file ordering.
4. Prefer robust assertions (`has_text`, `has_line`, metadata checks) over brittle full-file equality when harmless whitespace or ordering can vary.
5. For collections, verify element identifiers and collection type (`list`, `paired`, nested shapes) before output contents.

## Missing Requirements And Runtime Dependencies

Symptoms:

- Job fails with command not found.
- Tool works locally but not in Galaxy jobs.
- Container or conda resolver cannot satisfy `<requirements>`.
- Mulled image name does not match expectations.

Recovery:

- Add or correct `<requirements><requirement type="package" version="...">name</requirement></requirements>`.
- Use `mulled-hash 'pkg=version,pkg2=version'` for deterministic image-name reasoning.
- Treat conda solving, container pulls/builds, mulled search/list/build, and BioContainers checks as external dependency management requiring network/runtime approval.
- For tests that intentionally exercise external dependency managers, document the opt-in path and skip them in normal local runs.

## External Dependency Management Marker

Galaxy separates tests that touch Conda, container registries, or BioContainers using an `external_dependency_management` marker. When a failure mentions skipped external dependency management or missing marker behavior, decide whether the current task is a normal local check or a deliberate external dependency check.

Normal path:

```bash
pytest <tool-util-tests> -m 'not external_dependency_management'
```

Deliberate opt-in path:

```bash
pytest -m external_dependency_management <tool-util-tests>
```

Resolve `<tool-util-tests>` in the active Galaxy checkout instead of baking source paths into public skill content. Explain that the opt-in path may require network access, conda/container tools, registry availability, and longer runtimes.

## CWL And Workflow Conversion Errors

Symptoms:

- CWL import or conversion fails.
- Workflow tests fail during import before execution.
- Format2 workflow syntax loads but output wiring is wrong.
- Secondary files, directories, scatter, nested subworkflows, or `loadContents` cases behave differently than expected.

Recovery:

1. Reduce to the smallest workflow or CWL case that still fails.
2. For Format2 workflows, check `class: GalaxyWorkflow`, `inputs`, `steps`, `in`, and `outputs.outputSource` first.
3. Confirm each workflow test has a matching `.gxwf-tests.yml` basename and top-level list of cases.
4. Use `expect_failure: true` only for intended workflow failures.
5. Avoid broad CWL conformance regeneration unless explicitly requested; that path downloads upstream archives and rewrites generated cases.

## Tool Panel Load Errors

Symptoms:

- A valid tool XML does not appear in the panel.
- A section or label is missing or ordered incorrectly.
- A workflow appears in a tool panel location unexpectedly.

Recovery:

- Check the tool panel configuration entry, section nesting, labels, and duplicate IDs.
- Confirm the tool file is included in the active tool configuration and that Galaxy has been restarted or reloaded after XML/config changes.
- Check whether the item is a normal tool, workflow panel item, label, or section.
- For data managers, remember they are admin-only special tools and do not appear in the standard tool panel.
- Route repository publishing or installed Tool Shed repository visibility issues to `../tool-shed-operations/SKILL.md`.

## Data Manager Confusion

Symptoms:

- A data manager wrapper runs but no data table entry appears.
- Output is not recognized as `data_manager_json`.
- Non-admin users cannot access the manager.

Recovery:

- Confirm the wrapper uses `tool_type="manage_data"` and writes a JSON description as its primary output.
- Confirm the data manager configuration loads the manager tool.
- Confirm the table schema and `.loc` behavior with `../data-and-storage/SKILL.md`.
- Do not debug Tool Shed distribution here; route publishing and install repository issues to `../tool-shed-operations/SKILL.md`.
