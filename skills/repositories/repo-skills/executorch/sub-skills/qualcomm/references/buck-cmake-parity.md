# QNN Buck/CMake Parity

Use this when QNN CI fails because Buck and CMake target definitions drifted, or after adding/removing QNN `.cpp`, `.h`, generated schema, builder, serializer, or test files.

## Parity Loop

1. Identify the changed files under the QNN backend.
2. Find the owning CMake target and Buck/TARGETS entry.
3. Ensure source lists, headers, generated files, compile definitions, include directories, and dependencies are represented in both systems.
4. Run the smallest local configure/build that can expose the drift. If Buck is unavailable locally, perform static source-list reconciliation and document the unrun check.
5. Keep the fix minimal; do not rewrite build structure while addressing parity.

## Common Drift Patterns

- New source added to CMake but not Buck.
- Include path added only to one build system.
- Generated serializer/schema files present in one target but not the other.
- Dependency target renamed in one system.
- Test-only file accidentally linked into production target.

