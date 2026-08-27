# Shared Workflows

This repository is organized around one shared search runner and three task
modes.

## Shared execution model

1. Choose a task with `get_task(name)`.
2. Pick a backend model and temperature.
3. Choose either the naive path or Tree of Thoughts BFS.
4. Run the bundled `scripts/run_tot.py` helper.
5. Inspect the JSON log under `./logs/` and the task-specific `test_output`
   result.

The BFS path in `tot.methods.bfs.solve` always repeats the same structure:

- generate candidates from a task prompt;
- score them with `value` or `vote` prompts;
- select a frontier with `greedy` or probabilistic sampling;
- repeat for the task's declared number of steps.

## Choosing the right route

- Use `game24` when the input is a small set of numbers and the output should
  be a step-by-step arithmetic derivation that ends in `Answer: ... = 24`.
- Use `text` when the input is a writing instruction and the output should be a
  multi-paragraph coherent passage with optional planning or voting.
- Use `crosswords` when the input is a 5x5 mini crossword clue grid and the
  output must be five rows of five letters.

## How to add a new task

The public package follows a simple extension pattern. When adding a new task
inside a checkout, keep the new task class and prompt family together:

1. Create a new subclass of `tot.tasks.base.Task`.
2. Add the prompt templates in a sibling `tot.prompts` module.
3. Register the task name in the package task factory.
4. Expose a `test_output` method so the runner can score the new task.
5. Decide whether the task should use `sample`, `propose`, `value`, or `vote`
   for generation and evaluation.

If the new task reuses the shared BFS runner, make sure its prompt wrappers and
output unwrappers are deterministic enough for the parser to consume.

## When to read this file

Read this file when a workflow spans multiple task modes, when a user asks how
ToT chooses between sampling and BFS, or when a new task needs to reuse the
shared runner architecture.
