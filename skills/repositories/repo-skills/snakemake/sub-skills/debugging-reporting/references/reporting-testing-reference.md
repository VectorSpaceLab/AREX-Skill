# Reporting and testing reference

This reference covers Snakemake 9.23.1 report generation, report metadata/styles, notebooks, generated unit tests, and smoke-test patterns.

## HTML and ZIP reports

Generate a default self-contained HTML report after a successful run:

```bash
snakemake --report
snakemake --report report.html
```

Generate a ZIP archive for larger report payloads:

```bash
snakemake --report report.zip
```

Signals:

- `--report` without a path writes `report.html`.
- An `.html` path embeds report outputs into one self-contained HTML file and fits smaller reports.
- A `.zip` path creates a portable archive whose main entry point is `report.html` after unpacking.
- Report statistics and provenance are collected from `.snakemake` metadata at render time. If the workflow has not run successfully, expect missing runtime statistics or missing reported outputs.

Create a report immediately after a run only when the normal execution should also happen:

```bash
snakemake --cores 1 --report report.html --report-after-run
```

Create a partial report for selected targets:

```bash
snakemake results/plot.svg --report report-short.html
```

## Marking outputs for reports

Use the `report()` flag on outputs that should appear in the report:

```python
report: "report/workflow.rst"

rule plot:
    input: "data/table.tsv"
    output:
        report(
            "results/plot.svg",
            caption="report/plot.rst",
            category="Quality control",
            subcategory="{sample}",
            labels={"sample": "{sample}", "kind": "plot"},
        )
    shell: "plot-tool {input} > {output}"
```

Important details:

- A top-level `report: "path/to/description.rst"` defines the workflow description panel.
- Caption `.rst` paths are interpreted relative to the current Snakefile.
- Captions can use Jinja2 context such as `{{ snakemake.config }}` for workflow descriptions and script-like `snakemake` properties for output captions.
- `category`, `subcategory`, and `labels` can use wildcards or functions. Functions should return strings/numbers for category/subcategory or a dictionary of string keys to string/number values for labels.
- Labels make report menus less file-name centric and can render toggles when each category/subcategory has one result for every label combination.

Directory reports:

```python
rule collect:
    output:
        report(
            directory("results/qc"),
            caption="report/qc.rst",
            patterns=["{sample}.html", "{sample}.txt"],
            category="QC",
        )
    shell: "mkdir -p {output}; generate-qc {output}"
```

HTML hierarchy reports:

```python
rule web_output:
    output:
        report(directory("site"), caption="report/site.rst", htmlindex="index.html")
    shell: "build-site site"
```

## Report links and metadata

From captions, link to generated report sections with reStructuredText references such as `Rules_`, `Statistics_`, a category name like ``Quality control_``, or a reported basename such as `plot.svg_`.

From Python scripts that create reported HTML or tables, use `snakemake.report_href()`:

```python
with open(snakemake.output[0], "w") as handle:
    handle.write(
        f'<a href="{snakemake.report_href("results/table.html")}">table</a>'
    )
```

For files inside a reported directory, chain helpers:

```python
snakemake.report_href("site").child_path("details/page.html").url_args(sample="A").anchor("qc")
```

Customize styles and metadata:

```bash
snakemake --report report.html --report-stylesheet report/custom.css
snakemake --report report.html --report-metadata report/metadata.yaml
```

Metadata is a YTE YAML template. Keep it portable and avoid embedding private machine paths:

```yaml
Workflow name: Example workflow
Contributors:
  - Analysis Team
Dataset: ?snakemake.config.get("dataset", "not specified")
```

## Report failure checklist

When report generation fails after a successful run:

1. Confirm each `report()` output exists and was produced by the workflow metadata in `.snakemake`.
2. Check caption paths relative to the Snakefile, not the shell working directory.
3. Validate reStructuredText syntax in captions and workflow description.
4. Verify `category`, `subcategory`, and `labels` functions accept the right arguments and return strings/numbers or dictionaries.
5. For directory reports, confirm `patterns` match real child files, or use `htmlindex` for HTML hierarchies.
6. For CSS, prefer self-contained assets or data URIs; missing relative assets can make branding appear broken.
7. For ZIP reports, unpack and open the archive's contained `report.html`, not the ZIP file itself.

## Generated unit tests

Snakemake can generate pytest tests from a workflow that has already run successfully:

```bash
snakemake --cores 1 --notemp --show-failed-logs
snakemake --generate-unit-tests
pytest .tests/unit/
```

Specify a custom output directory:

```bash
snakemake --generate-unit-tests .tests/unit-small
pytest -q .tests/unit-small/
```

Signals:

- Default generated test directory is `.tests/unit`.
- One representative job per rule is converted into `test_<rulename>.py` when all required input files are present.
- Snakemake copies config files, job inputs, and expected outputs into the generated test tree.
- Rules that do not execute work can be skipped.
- If no job has all inputs present, rerun a small fixture workflow with `--notemp` before generating tests.
- Generated tests run one selected rule with `python -m snakemake`, `--show-failed-logs`, `-j1`, `--allowed-rules`, and output comparison.

Customize output comparisons in generated tests when byte-for-byte comparison is too strict:

```python
common.OutputChecker(data_path, expected_path, workdir).check(
    {
        ".txt": ["diff", "--ignore-matching-lines", "^#"],
        ".tsv": ["qsv", "diff"],
    }
)
```

Generated tests should be based on tiny fixture data and should finish in seconds. Store generated tests in version control only after reviewing copied data size and sensitivity.

## Notebook diagnostics

Notebook rules execute `.ipynb` notebooks through Snakemake and can store executed notebooks via a named `log:` entry:

```python
rule analyze:
    input: "data/input.tsv"
    output: "results/out.txt"
    log:
        notebook="logs/analyze.ipynb"
    conda: "envs/notebook.yaml"
    notebook: "notebooks/analyze.ipynb"
```

Typical environment dependencies include Jupyter and execution tooling such as papermill or nbconvert, depending on the notebook workflow.

Useful commands:

```bash
snakemake results/out.txt --cores 1 --printshellcmds --show-failed-logs
snakemake --draft-notebook results/out.txt
snakemake --edit-notebook results/out.txt --notebook-listen localhost:8888
```

Signals:

- Snakemake injects a preamble cell tagged `snakemake-job-properties` and removes/replaces it as needed.
- More than one preamble cell with that tag indicates a notebook cleanup problem.
- The `log: notebook="..."` entry stores the executed notebook for post-failure inspection.
- `--draft-notebook TARGET` creates a skeleton notebook for the rule that produces the target.
- `--edit-notebook TARGET` starts an editing server for the target's notebook; use only in interactive environments.

## CI smoke patterns

For syntax/topology/report-readiness without heavy execution:

```bash
mkdir -p diagnostics
snakemake --cores 1 --dry-run --printshellcmds > diagnostics/dry-run.txt 2>&1
snakemake --lint json > diagnostics/lint.json 2>&1 || true
snakemake --rulegraph > diagnostics/rulegraph.dot
snakemake --summary > diagnostics/summary.tsv || true
```

For a small fixture workflow that is safe to execute:

```bash
snakemake --cores 1 --notemp --show-failed-logs
snakemake --report diagnostics/report.html
snakemake --generate-unit-tests .tests/unit
pytest -q .tests/unit
```

If CI does not have notebook/report extras installed, keep the smoke job to dry-run, lint, and graph generation, and report the skipped checks explicitly.
