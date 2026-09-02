---
name: input_programming
description: Construct masked universal input programs for adversarial reprogramming of frozen neural networks.
---

# Input-Space Adversarial Program Construction

Use this skill when reproducing or testing adversarial reprogramming methods that embed a small task input into a larger target-model input and add a single reusable trainable program. Do not use it for per-example adversarial attacks where every input receives an independently optimized perturbation.

## Inputs
- `task_values`: task data values that occupy protected mask positions.
- `mask`: flat or nested binary mask with `1` for task pixels and `0` for program pixels.
- `program_values`: universal program values for non-task positions.

## Outputs
- A programmed input with task values preserved and program values inserted elsewhere.
- Metadata indicating task positions, program positions, and preservation status.

## Workflow
1. Validate the mask has at least one protected task position and one program position.
2. Flatten nested lists deterministically.
3. Copy task values into mask positions in order.
4. Copy program values into non-mask positions in order; a scalar program may be broadcast.
5. Verify task values were preserved exactly.

## Validation
Run `python tests/test_input_programming.py` or validate the whole skill tree with the Paper2Skills skill validator.

## Limitations
This script is a deterministic data-construction helper. Gradient updates for the program are handled by the program optimization skill.
