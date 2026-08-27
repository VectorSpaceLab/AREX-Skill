# GOOD Workflows

1. Pick the dataset class that matches the benchmark family.
2. Choose the domain and shift from the dataset's allowed values.
3. Call the class-level `.load(...)` helper rather than manually constructing processed objects.
4. Use the returned split dictionary for training/evaluation routing.
5. Read `meta_info` to size the downstream model and determine the number of environments.

## Common Patterns

- Molecular OOD datasets usually use `scaffold` or `size` domains.
- Node-level datasets use `degree`, `word`, or `time` domains depending on the dataset class.
- `no_shift` typically omits `id_val` and `id_test`, while shifted settings include them.
