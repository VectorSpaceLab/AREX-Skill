# RWKV-7 context parallelism

## Purpose

Read this when you need to understand the chunk-state composition used by the
repository's RWKV-7 context parallelism demo.

## High-level idea

The demo splits a prompt into equal chunks, runs the recurrent state update on
those chunks, and records per-chunk transition summaries. The key claim is that
merging the chunk summaries should reproduce the same final recurrent state as a
single full-sequence pass.

The script reports three checks per layer:

- direct one-pass state equals the direct accumulated `rnnC`
- direct one-pass state equals the chunk-run state
- direct one-pass state equals the merged chunk-summary state

## Why the identity matters

If the identity fails, the issue is usually one of:

- incorrect chunk length or prompt slicing
- a bad checkpoint family or tensor mismatch
- an implementation difference in the recurrence math
- a compiler/runtime issue in the accelerated path

## Reading the demo output

The demo prints:

- probe text and token ids
- chunk lengths
- layer count
- state shapes for the recurrent tensor
- per-layer max/mean absolute differences

A correct implementation shows tiny differences and `ok=True` for the merged
summary check.

## What not to infer

Do not assume that a successful chunk merge implies that a fast CUDA extension is
installed or that a long-generation workload is verified. The demo validates the
state-composition identity only.
