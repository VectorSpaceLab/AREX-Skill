# Data and MCTS Reference

## Dataset helpers

- `detikzify.dataset.load_dataset(path, *args, **kwargs)`
  - Checks whether `path` exists under the package's dataset directory.
  - Uses `trust_remote_code=True` for local package datasets.
  - Falls back to `datasets.load_dataset(...)` otherwise.
- `Paper2Fig`
  - Builder for the Paper2Fig100k figure dataset.
  - Produces `caption`, `mention`, `ocr`, and `image` fields.
- `SciCap`
  - Builder for the SciCap dataset in DeTikZify's expected unified format.
  - Produces `caption`, `mention`, `paragraph`, `ocr`, and `image` fields.

## Generic MCTS engine

- `detikzify.mcts.node.Node(state)` stores win value, visits, policy value, parent, children, and search metadata.
- `detikzify.mcts.montecarlo.MonteCarlo(root_node, mins_timeout=None)` manages expansion, rollout, and choice selection.
- `simulate(expansion_count=1)` runs repeated expansions until the count or timeout is reached.
- `expand(node)` adds children, scores them, and triggers rollout when needed.
- `random_rollout(node)` follows one child recursively until a terminal evaluation is available.
- `make_choice()` returns the most visited child.
- `make_exploratory_choice()` samples a child based on visitation probabilities.

## Tree-search notes

- `policy_value` affects exploration pressure.
- `player_number` changes how win value is interpreted in the score function.
- `discovery_factor` adjusts exploration vs exploitation.
- `is_scorable()` is true when the node already has visits or a policy value.
