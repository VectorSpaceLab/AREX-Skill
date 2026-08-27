# Workflows

## Local dataset loading

1. Ask whether the path should resolve to a package-relative dataset directory.
2. Use `detikzify.dataset.load_dataset(...)` so package-local datasets can be loaded without hardcoding the repo path.
3. Confirm the expected splits and feature names before using the dataset in training or evaluation.

## Paper2Fig and SciCap

1. Inspect the dataset feature layout.
2. Confirm the builder output matches the fields expected by the downstream training or evaluation workflow.
3. Treat these builders as dataset-preparation helpers, not as model-training helpers.

## Generic MCTS

1. Create a root `Node` for the current state.
2. Assign a `child_finder` that adds children for a given node.
3. Assign a `node_evaluator` that returns a terminal score when the node is finished.
4. Call `simulate(...)` and then choose between `make_choice()` and `make_exploratory_choice()`.

## When to debug instead of proceed

- If the dataset loads locally but not remotely, check the remote dataset identifier and credentials.
- If `print_tree` output is confusing, make sure the search state can be compared and rendered like a string.
- If `simulate` never expands, inspect `child_finder` before blaming the scoring logic.
