# GAIA Evaluation Troubleshooting

## Dataset is missing

**Symptom:** `metadata.jsonl` or `metadata.parquet` is not found, or validation
and test directories do not exist. **Recovery:** acquire the authorized GAIA
dataset into the configured private data directory, verify both split layouts,
and rerun `load`. Do not invent metadata or silently switch to a different
benchmark.

## Invalid split or level

**Symptom:** `ValueError` says `on` or `level` is invalid. Use only `valid` or
`test`, and levels 1, 2, 3, a valid list, or `all`. Check that list values are
integers before invoking a costly run.

## Attachment is skipped

**Symptom:** a task gets a zero result and log says the file was not found.
**Cause:** metadata `file_name` resolves below its split directory and does not
exist. Fix the dataset layout or metadata path. The benchmark intentionally
skips the task; it does not prove a model failure or success.

## No final answer or wrong format

**Symptom:** `extract_pattern` returns `None`, or numeric/list scoring is false.
**Recovery:** inspect the raw assistant answer, require the
`<final_answer>...</final_answer>` tag for GAIA mode, and make the inner text
match the requested scalar/list/string format. Do not add currency symbols or
percent signs unless the task expects them; the scorer strips some symbols but
format ambiguity still makes results hard to audit.

## Resume/result JSON problems

**Symptom:** existing result file cannot be loaded or completed task ids are not
skipped. Validate JSON syntax and permissions, use a new result path when the
old schema is unknown, and record the selected split/level/subset. Never delete
prior results as a first troubleshooting step.

## Model, network, or cost failure

**Symptom:** model construction, tool calls, downloads, or long loops fail.
**Recovery:** validate provider configuration, use a small subset, keep
`round_limit` bounded through the role-playing implementation, and separate
provider/network failures from data/scoring failures. Benchmark download and
model execution were not part of the package inspection gate and require
explicit credentials, network, and budget approval.
