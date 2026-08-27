# ONNX Operator Maintenance Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `defs.cc` change compiles but docs still show the old behavior | Generated docs were not regenerated from the updated schema | Regenerate operator docs and backend coverage after the source-of-truth change settles. |
| `old.cc` and `defs.cc` both contain nearly identical copies of the same schema | Compatibility refactor was not split into helpers | Extract shared doc strings, type constraints, or inference helpers into a header or utility file. |
| Shape inference crashes on missing shapes or dimensions | Helper code accessed shape data without checking availability | Guard shape access with `hasNInputShapes`, `hasInputShape`, and `has_dim_value`. |
| Function-body parser rejects an otherwise obvious graph | The compact ONNX syntax is stricter than Python graph helpers | Re-check attribute placement, variable names, and subgraph syntax in the ONNX text reference. |
| Version-converter tests fail after an operator change | The adapter set or upgrade/downgrade tests were not updated | Add or adjust the adapter and keep both upgrade and downgrade coverage in sync. |
| Backend node test snippets no longer match the reference docs | Test case and operator documentation diverged | Rebuild the test case, verify the reference implementation, and regenerate docs from the source schemas. |
| `lintrunner` or `pixi` gates fail after the change | Style, generated outputs, or build prerequisites are inconsistent | Fix the source-of-truth files, regenerate artifacts, and rerun the focused gate before broadening the test scope. |
| C++ gtest output mentions `unk__*` free dimensions | Shape inference materialized unknown dims in the test harness | Allow either unset dims or `unk__*` placeholders in the assertion helper. |
