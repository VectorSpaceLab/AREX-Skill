# Benchmark Integration Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| Benchmark task lookup fails | Name/alias is misspelled, package discovery hit a circular import, or an optional task module failed while being scanned | First import `roboverse_pack.benchmark` directly and call `list_benchmark_task_specs()`; normalize with `get_benchmark_task_spec`; preserve the `KeyError` available-list message. If MetaSim discovery logs a partially initialized `roboverse_pack.tasks.benchmark`, treat it as a package/task import defect and isolate the direct metadata path rather than claiming global registration passed. |
| Default/selected robot is rejected | Robot is not in `supported_robots` or lacks a teleop profile | Inspect the task spec; choose a supported robot or add a complete profile with control joint count, slices, and body names. |
| Converter loses episodes or keys | Format version, empty-trajectory policy, or episode boundary is implicit | Run a tiny fixture with empty/malformed cases; require explicit schema/version metadata and compare episode counts and first/last steps. |
| Replay runs but success is wrong | Native checker, task semantics, control rate, object pose, or reward translation differs | Compare native and RoboVerse success inputs; report checker/backend separately; do not equate visual similarity with success parity. |
| Native package import fails | Optional benchmark dependency or simulator extra is absent/incompatible | Install the exact integration variant in isolation; record version and assets. Keep metadata/conversion checks on CPU. |
| Asset locator/download fails | Local assets, license data, cache, or network credentials unavailable | Use a local tiny fixture or inventory-only path; do not download in a generic smoke test or silently use a different asset. |
| Action shape/joint order mismatch | Robot profile, controller, gripper convention, or frame differs | Print expected and actual names/order/ranges; adapt through an explicit mapping and test round-trip conversion. |
| Render or native rollout hangs | Display/EGL/GPU or long external process | Run headless one-step first, add a timeout and bounded episode, classify unavailable hardware separately. |
| Passthrough test fails in vendored code | Native implementation intentionally differs or has a pinned parity contract | Preserve the boundary and upstream version; do not rewrite vendored code to force a local pass. |
