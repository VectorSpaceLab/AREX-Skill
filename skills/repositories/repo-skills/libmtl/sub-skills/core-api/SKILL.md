---
name: core-api
description: "Routes LibMTL's Trainer, shared configuration, and built-in API surface."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# core-api

Use this sub-skill when the task is about the shared LibMTL API rather than a
specific benchmark dataset.

## Covers

- `LibMTL.Trainer` construction and runtime behavior.
- `LibMTL.config.LibMTL_args` and `prepare_args`.
- Built-in losses, metrics, architectures, weightings, and backbone builders.
- The shared utility helpers in `LibMTL.utils`.
- Direct inspection of the API surface before writing a custom benchmark or a
  new method.

## Does not cover

- Dataset-specific file layouts or benchmark commands.
- New-task adaptation recipes; use `customization` for that.
- NYUv2/Cityscapes, Office-31/Office-Home, QM9, or PAWS-X details.

## When to use this sub-skill

Choose this route when the user asks things like:

- "How do I instantiate `Trainer` correctly?"
- "Which weighting and architecture names are supported?"
- "What does `prepare_args` return?"
- "How do the built-in backbones and utilities fit together?"
- "Why did a direct `Trainer` call fail even though the docs looked correct?"

## Read next

- `../../references/api-reference.md` for the verified signature and exported
  classes.
- `../../references/configuration.md` for shared CLI and method flags.
- `../../references/troubleshooting.md` for configuration and runtime failures.

## Workflow

1. Confirm whether the user is passing string names or class objects.
2. Confirm whether `prepare_args` is being used. If not, check that both
   `weight_args` and `arch_args` are supplied.
3. Confirm the runtime has CUDA. The trainer's default device is `cuda:0`.
4. Check the requested weighting and architecture names against the exported
   module lists.
5. If the request is to validate the install rather than solve a dataset task,
   run `scripts/check_core_api.py`.

## Common gotchas

- `Trainer` resolves weighting and architecture names internally. Pass strings
  such as `"EW"` and `"HPS"`.
- The supported optimizer/scheduler combinations in the current code are
  narrower than the parser help suggests; `adam`/`sgd` and `step` are the safe
  choices.
- `resnet18` and `resnet_dilated` return feature maps. They are not end-to-end
  classifiers.
- `MOML`, `FORUM`, and `AutoLambda` are treated as bilevel methods and use the
  trainer's special path.

## Exit criteria

Leave this sub-skill when you can answer, from the bundled files alone:

- which object to import,
- which string names to pass,
- which kwargs must be present,
- and what failures mean the configuration is wrong versus the environment is
  incomplete.
