# Tool Development

## When To Use Tool Framework Tests

Galaxy tool wrappers encode much of the public plugin interface: command templating, parameters, outputs, metadata, dependency hints, and tool-test assertions. When a change can be expressed as a tool wrapper plus test data, prefer a tool test over a lower-level test because the framework exercises loading, parameter conversion, execution, and output verification together.

Typical tool framework work includes:

- adding or repairing a `<tool>` XML wrapper;
- adding `<tests>` blocks to an XML wrapper;
- writing or validating YAML tool definitions and YAML tests;
- reproducing assertion failures from output checks;
- checking requirements, containers, `detect_errors`, `<stdio>`, and profile upgrade guidance;
- handling data-manager wrappers as special admin-only Galaxy tools.

## XML Wrapper Shape

A minimal XML wrapper usually contains:

```xml
<tool id="example_tool" name="Example Tool" version="1.0.0" profile="24.2">
    <requirements>
        <requirement type="package" version="1.17">samtools</requirement>
    </requirements>
    <command detect_errors="exit_code"><![CDATA[
        samtools --help > '$out_file'
    ]]></command>
    <inputs>
        <param name="input1" type="data" format="txt" />
    </inputs>
    <outputs>
        <data name="out_file" format="txt" />
    </outputs>
    <tests>
        <test>
            <param name="input1" value="input.txt" />
            <output name="out_file">
                <assert_contents>
                    <has_text text="Usage" />
                </assert_contents>
            </output>
        </test>
    </tests>
</tool>
```

Practical authoring rules:

- Use stable `id`, `name`, `version`, and a current `profile` where possible.
- Prefer `detect_errors="exit_code"` for command failure detection unless the tool has special stdout/stderr conventions.
- Quote Galaxy paths in `<command>` templates and keep command output deterministic for tests.
- Put package hints under `<requirements>` and container hints in the wrapper when they are required for normal execution.
- Add `<help>` and citations for user-facing tools, but keep tests independent of prose.
- Keep dynamic options, data tables, dbkeys, and datatypes aligned with data-storage guidance when they are the primary task.

## Tool Tests

XML tool tests live inside `<tests>` and usually contain `<param>` values plus expected `<output>` assertions. Common assertion patterns include:

```xml
<output name="out_file">
    <assert_contents>
        <has_line line="expected line" />
        <has_text text="expected substring" />
    </assert_contents>
</output>
```

YAML tool definitions use a `tests:` list with `inputs:` and `outputs:` blocks. A typical output assertion is:

```yaml
tests:
- inputs:
    input1:
      class: File
      path: input.txt
  outputs:
    out_file:
      asserts:
      - that: has_text
        text: expected substring
```

Use `validate-test-format` to check YAML test structure when the tests are separated from a wrapper or represented in Planemo-style YAML. This validation checks the test file shape, not whether the referenced tool inputs and outputs semantically exist.

## Safe Validation Ladder

Start with checks that do not require a running Galaxy server:

```bash
python -m galaxy.tool_util.format --diff path/to/tool.xml
python -m galaxy.tool_util.upgrade.script path/to/tool.xml --profile-version 24.2
python scripts/inspect_tool_util.py --tool-xml path/to/tool.xml
python -m galaxy.tool_util.validate_test_format path/to/tool-tests.yml
```

Escalate to runtime checks only after static checks pass and the user has a Galaxy target:

```bash
galaxy-tool-test --galaxy-url http://localhost:8080 --key "$GALAXY_API_KEY" --tool-id example_tool --test-index 0 --output-json tool-test.json
```

`galaxy-tool-test` talks to a running Galaxy and may upload test data, execute jobs, create histories, and require credentials. Do not run it without a user-approved target and key.

## Dependency Hints And Mulled Names

Tool dependency hints usually start in `<requirements>`:

```xml
<requirements>
    <requirement type="package" version="0.7.15">bwa</requirement>
</requirements>
```

For local reasoning, `mulled-hash` can compute the deterministic BioContainers-style image name for a package set without building or pulling images:

```bash
mulled-hash 'samtools=1.3.1,bedtools=2.26.0'
```

Treat `mulled-build`, `mulled-build-channel`, `mulled-build-files`, `mulled-build-tool`, `mulled-list`, `mulled-search`, and singularity update commands as external dependency management because they may need container engines, conda metadata, registries, or network access.

## Data Managers As Tools

Data managers are special Galaxy tools with `tool_type="manage_data"`. They are admin-only, do not appear in the standard tool panel, and normally write a JSON `data_manager_json` output describing entries to add to tool data tables. Keep wrapper and tool-test advice here, but route table schema, `.loc` content, persistent data paths, and data-table configuration to `../data-and-storage/SKILL.md`.

A data-manager wrapper often differs from a normal tool by:

- using `tool_type="manage_data"`;
- writing data-table entry JSON as the primary output;
- placing managed files under the output dataset extra-files path;
- depending on a data manager configuration file to load the manager in Galaxy;
- requiring admin access for execution.

## Native Evidence Candidates

Useful native patterns to adapt during verification include simple XML tools with inline `<tests>`, YAML tools with `tests:` lists, mulled requirement examples, data-manager wrappers, and parameter-focused wrappers. For runtime verification, prefer small deterministic tools and avoid tests that require external services, large datasets, credentials, or container registries unless the user explicitly opts in.
