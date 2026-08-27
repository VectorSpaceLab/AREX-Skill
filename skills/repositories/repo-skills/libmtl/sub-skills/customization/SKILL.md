---
name: customization
description: "Routes LibMTL dataset adaptation, custom methods, and extension workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# customization

Use this sub-skill when the task is to adapt LibMTL to a new dataset or extend
its method set with custom losses, metrics, architectures, or weighting
strategies.

## Covers

- Building a new `task_dict`.
- Defining new losses and metrics from `AbsLoss` and `AbsMetric`.
- Defining new architectures from `AbsArchitecture`.
- Defining new weighting strategies from `AbsWeighting`.
- Writing a custom encoder/decoder pair and, when needed, a `Trainer`
  subclass.
- Choosing between single-input and multi-input task layouts.

## Does not cover

- The benchmark-specific file layouts and commands for NYUv2, Office-31,
  Office-Home, QM9, or PAWS-X.
- Package installation or API signature lookup; use `core-api` for that.

## When to use this sub-skill

Choose this route when the user asks things like:

- "How do I port LibMTL to a new dataset?"
- "How do I write a custom metric or loss?"
- "How do I add a new weighting strategy?"
- "How should I subclass `Trainer` or `AbsArchitecture`?"
- "What shape should my dataloaders return?"

## Read next

- `../../references/api-reference.md` for the base classes and verified
  signatures.
- `../../references/configuration.md` for shared flags and method-specific
  options.
- `references/workflows.md` for the adaptation recipe.
- `references/troubleshooting.md` for common extension errors.

## Workflow

1. Decide whether the task is single-input or multi-input.
2. Define the task dictionary first.
3. Confirm the encoder output shape and the decoder head shapes.
4. Only then wire the trainer and check the CUDA runtime.
5. If the request is about a new weighting or architecture, start from the
   relevant abstract base class and preserve the expected gradient plumbing.

## Critical constraints

- `MTAN` expects a ResNet-based encoder with a `resnet_network` attribute.
- `PLE` only supports `multi_input=False`.
- `CGC`, `PLE`, `MMoE`, and `DSelect_k` need `img_size` and expert counts.
- `Trainer` still expects string method names and `weight_args` / `arch_args`
  dictionaries.

## Exit criteria

Leave this sub-skill when the new dataset or method can be described as a
repeatable recipe with explicit task format, encoder/decoder contract,
configuration knobs, and failure modes.
