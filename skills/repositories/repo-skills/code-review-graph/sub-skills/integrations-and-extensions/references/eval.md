# Evaluation and Reproduction

## Purpose

Read this when you need to reproduce the package’s benchmark methodology or understand the evaluation harness.

## What the eval surface covers

CRG ships an evaluation framework for benchmark-style reporting and reproduction. The public docs describe:

- scorer utilities,
- report generation,
- pinned benchmark configs,
- and reproduction guidance for the published results.

## Practical guidance

- Treat full benchmark reproduction as a maintainer/advanced task.
- Prefer unit-level eval tests before any expensive clone or benchmark run.
- Install the eval extra only when the user explicitly wants benchmark utilities or reproduction.

## What to verify first

When working with eval support, first confirm:

1. the package imports,
2. the selected benchmark config is available,
3. and the current repo state matches the expected snapshot/commit assumptions.

## When to stop

Stop and ask for clarification if the task requires:
- network access to clone benchmark repositories,
- a specific pinned upstream SHA,
- or a comparison against a benchmark result that is not present in the current checkout.
