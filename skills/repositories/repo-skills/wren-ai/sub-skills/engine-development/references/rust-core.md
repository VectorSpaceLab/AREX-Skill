# Rust Semantic Core

## When to read

Read this for changes to MDL semantics, DataFusion planning, manifest types,
optimizer behavior, or Rust test selection.

## Module map

| Module | Responsibility |
| --- | --- |
| `wren-core` | MDL analysis, semantic SQL expansion, DataFusion analyzer/optimizer rules, SQL generation |
| `wren-core-base` | Shared manifest types and builders used by core and PyO3 binding |
| `wren-core-py` | PyO3 bridge exposing semantic-core APIs to Python |

The core uses upstream DataFusion v53. Important areas include MDL processing,
logical-plan analyzer rules (models, views, relationships, access controls), and
optimizer passes such as type coercion/timestamp simplification.

## Manifest and builders

Shared types include Manifest, Model, Column, Relationship, View, Cube,
Measure, and access-control objects. `ManifestBuilder` and related builders are
useful for focused Rust tests. A model primary key may be a single name or a
composite list; preserve backward-compatible serialization when changing it.

## Commands

```bash
cargo check --all-targets
RUST_MIN_STACK=8388608 cargo test --lib --tests --bins
cargo fmt --all
cargo clippy --all-targets --all-features -- -D warnings
```

Use sqllogictest files for end-to-end SQL behavior and snapshot review only when
a tested semantic output is intentionally changing.

## Known limitation

The model analyzer cannot resolve outer column references in some correlated
subqueries because the subquery scope does not retain the outer column scope.
Do not describe a workaround as a behavior fix without a reproducing test.
