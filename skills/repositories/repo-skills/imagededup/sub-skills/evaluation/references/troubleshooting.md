# Evaluation and plotting troubleshooting

## `Please ensure that ground truth and retrieved map have the same keys!`

- The maps describe different filename sets.
- Fix: make the key sets identical before calling `evaluate`.

## Symmetry validation failures

- A filename points to a duplicate that does not point back.
- Fix: add the reverse relationship to both maps.

## `Please provide a valid filename present as a key in the duplicate_map!`

- `plot_duplicates` was given a filename that is not a key in the duplicate map.
- Fix: use a key from the map.

## `Provided filename has no duplicates!`

- The chosen image exists in the map, but its duplicate list is empty.
- Fix: choose a different key or populate the duplicate map first.

## Headless plotting problems

- Interactive display backends can block or fail in a terminal-only environment.
- Fix: use a noninteractive backend such as Agg before calling `plot_duplicates`.

## Small synthetic metric warnings

- Tiny toy examples can trigger sklearn warnings about undefined precision.
- Fix: treat the warning as expected for undersized test fixtures, or use a richer example.

## When results look odd

- Remember that IR metrics treat each key as a separate query.
- Remember that classification metrics collapse symmetric pairs into unique unordered pairs.
- That difference means the same duplicate miss can contribute differently across metric families.

## When to escalate

- If you still need encodings or duplicate search, switch to the hashing or CNN sub-skill.
- If you need help understanding the data layout used by the source images, inspect the shared image-handling helpers from the other sub-skills.