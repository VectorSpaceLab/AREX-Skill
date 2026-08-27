# Prompt contract

This page distills the prompt style used by the AirSim sample.

## Response roles

The repository evidence shows a compact role system:

- `Question` — ask a clarification question when the scene is ambiguous.
- `Code` — provide the drone command or Python code needed for the task.
- `Reason` — explain why the code or action was chosen.

Some example files also express the same idea with prose labels, but the core intent is the same: ask when the task is ambiguous, provide code when it is actionable, and explain after the code.

## Core instructions the prompt must preserve

- Use only the helper functions the sample defines.
- Do not invent hypothetical functions.
- Use exact object names when the scene contains named landmarks or objects.
- Ask a clarification question if there are multiple objects of the same type and the user did not specify which one.
- Keep motion descriptions aligned with the prompt's axis convention.

## Typical prompt inputs

The sample prompt and its system prompt give the assistant:

- a fixed set of helper functions;
- a fixed set of object names;
- a clarification rule for duplicates;
- a human-facing axis convention;
- a reminder to prefer the wrapper helpers instead of lower-level movement primitives.

## What the assistant should do

- Ask a clarification question when the task mentions a duplicate object class and does not identify which instance should be used.
- Return code that only calls the allowed helper functions.
- Keep explanations short and tied to the motion or object selection.
- Preserve the sample's logic of moving, inspecting, or orienting the drone in a simulator-safe way.

## What the assistant should not do

- Invent new AirSim primitives.
- Assume the wrong turbine, tower, or object instance.
- Replace the sample's helper functions with lower-level AirSim calls.
- Omit the explanation when the prompt expects a reason.

## When to read this file

Read this file when a user asks how the sample prompt should behave, how clarification is handled, or why a response should be code-first instead of prose-first.
