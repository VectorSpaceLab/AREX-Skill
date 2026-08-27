# Troubleshooting

## Dataset issues

- `load_dataset(path, ...)` only uses the package-local fallback when the named directory exists under the package's dataset folder.
- If a dataset builder fails, check the feature names and split expectations before assuming the hub download is broken.
- Keep the expected `caption`, `mention`, `ocr`, `paragraph`, and `image` fields straight; the builders are not interchangeable.

## MCTS issues

- An empty child list usually means the child-finder failed or the state was terminal.
- If `make_choice()` fails, the tree was probably never expanded enough to populate child visits.
- If the search score looks wrong, verify the `player_number` and `policy_value` settings.
- If debug-tree output breaks, make sure the state object supports the helper's string-style rendering assumptions.
