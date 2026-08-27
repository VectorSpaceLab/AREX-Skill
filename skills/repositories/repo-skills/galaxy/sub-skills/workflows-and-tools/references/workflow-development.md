# Workflow Development

## Workflow Framework Scope

Galaxy workflow framework tests exercise workflow import, scheduling, execution, output collection handling, and output verification. Use them when a task is about Format2 workflow YAML behavior, workflow inputs/outputs, mapping over collections, workflow defaults, inline user-defined tools, or expected workflow failures.

Route API-only execution of an existing workflow to `../api-automation/SKILL.md`. Stay here when the user needs to author or repair workflow YAML and test definitions.

## File Pair Convention

A workflow framework case uses two YAML files with matching basenames:

- `name.gxwf.yml`: Galaxy Format2 workflow definition.
- `name.gxwf-tests.yml`: list of test cases for that workflow.

A minimal Format2 workflow shape is:

```yaml
class: GalaxyWorkflow
inputs:
  input_int:
    type: int
    default: 1
outputs:
  out:
    outputSource: my_tool/out_file1
steps:
  my_tool:
    tool_id: some_tool
    in:
      param1:
        source: input_int
```

A matching test file shape is:

```yaml
- doc: |
    Test with default value
  job: {}
  outputs:
    out:
      class: File
      asserts:
      - that: has_text
        text: "expected content"
```

Use `expect_failure: true` when the expected behavior is a workflow run failure, such as explicit `null` or an invalid input shape that should not be replaced by a default.

## Authoring Checklist

- Set `class: GalaxyWorkflow` in workflow files.
- Give every workflow input a stable key; include `type` and `default` only when the workflow semantics require them.
- Define workflow outputs with `outputSource: step_name/output_name`.
- Connect steps with either short `in: input_name: source_name` syntax or explicit `source:` mappings.
- Keep tool IDs aligned with installed sample tools or target Galaxy tools.
- Place assertions under the workflow output name, not the step output name, unless they are identical.
- For collection outputs, use `class: Collection`, `elements`, and collection-type assertions compatible with Galaxy's test model.
- Keep test job data paths relative to the workflow test directory or supply them through the framework's test data mechanism.

## Inline User-Defined Tools

Format2 workflows can embed a `GalaxyUserTool` step under `run:`. This is useful when the workflow behavior depends on a small tool that should travel with the workflow definition.

```yaml
steps:
  udt_cat:
    run:
      class: GalaxyUserTool
      id: cat_user_defined
      version: "0.1"
      name: cat_user_defined
      shell_command: cat '$(inputs.input1.path)' > output.txt
      inputs:
        - name: input1
          type: data
          format: txt
      outputs:
        - name: output1
          type: data
          format: txt
          from_work_dir: output.txt
    in:
      input1: input1
```

Use inline tools for compact workflow-specific behavior. If the tool is reusable outside this workflow, author a normal Galaxy tool wrapper instead.

## Running Workflow Framework Tests

In a Galaxy checkout with test dependencies, workflow framework tests are normally selected through the framework workflow test target. For targeted pytest runs, use the workflow framework test module available in that checkout and select cases by pytest node or `-k` expression when the environment is already prepared:

```bash
pytest <workflow-framework-test-module> -k default_values
```

These commands start or use Galaxy test infrastructure and should be treated as native verification, not as lightweight static checks. Avoid hard-coding source checkout paths into reusable skill content; resolve the project-local test target at the time of use.

## CWL Conversion Surfaces

Galaxy carries CWL support and conformance conversion helpers, but the repository update helper downloads upstream CWL conformance archives and rewrites generated test cases. Treat that update path as networked and repository-mutating. For ordinary agent work:

- inspect or repair existing CWL wrapper/workflow behavior locally;
- avoid regenerating conformance suites unless the user explicitly requests it;
- explain that conversion errors may arise from unsupported CWL features, secondary files, directories, scatter, nested subworkflows, or input binding/loadContents behavior;
- prefer a small isolated CWL case before attempting broad conformance updates.

## Validation Limits

`validate-test-format` can validate the structure of YAML test definitions, but it does not prove that a workflow input, tool input, or output name exists. Workflow correctness requires import/execution in Galaxy's workflow framework or API-backed automation.
