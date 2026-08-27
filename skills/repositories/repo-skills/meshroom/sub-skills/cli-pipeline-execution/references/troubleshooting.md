# CLI Pipeline Troubleshooting

- **No pipeline listed:** templates are not bundled in the framework checkout by default. Load the plugin/AliceVision template folder and call `initPipelines()`; inspect `meshroom_info pipelines`.
- **`--output` fails with no output node:** the template was loaded without output nodes or the graph is not an output-capable pipeline. Use a template with `OutputNode` instances or configure the graph explicitly.
- **Targeted output form rejected:** use exact instance/type names and only exposed attributes. `.` targets one instance; `:` targets every node of a type.
- **Input applied to the wrong node:** when multiple input nodes exist, use `NodeName=value` rather than a bare value. Use `--inputRecursive` only when directory recursion is intended.
- **`meshroom_compute --node` fails on dependencies:** use `--toNode` or compute dependencies first. A node-only run does not automatically compute upstream nodes.
- **Compute refuses a submitted/running node:** inspect status with `meshroom_status`, verify the external job, and only then use `--forceStatus`.
- **Scene helper returns missing parameters:** check the semicolon-separated request syntax, exact node names, nested attribute paths, and `--fail-on-missing-*` choices.
- **`meshroom_statistics --exportHtml` fails:** HTML plotting is optional; use text statistics first, then install the plotting dependencies required by the exporter if HTML is actually needed.
- **Photogrammetry CLI fails with executable-not-found:** the framework can parse/save a graph without AliceVision, but the selected external node requires its binary and resource environment. Verify `PATH`, `ALICEVISION_ROOT`, plugin paths, and the node's process environment.
