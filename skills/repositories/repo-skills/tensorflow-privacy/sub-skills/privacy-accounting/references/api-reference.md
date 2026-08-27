# Privacy accounting API reference

## Purpose

Read this for the verified privacy-budget functions and the CLI argument shapes they expect.

## Verified functions

### `compute_dp_sgd_privacy_statement`

Signature:

```python
compute_dp_sgd_privacy_statement(
    number_of_examples: int,
    batch_size: int,
    num_epochs: float,
    noise_multiplier: float,
    delta: float,
    used_microbatching: bool = True,
    max_examples_per_user: int | None = None,
    accountant_type: AccountantType = AccountantType.RDP,
) -> str
```

Use this when you want a human-readable statement rather than a raw epsilon number.

### `compute_noise`

Signature:

```python
compute_noise(n, batch_size, target_epsilon, epochs, delta, noise_lbd)
```

Use this when you know the target epsilon and want to search for a compatible noise multiplier.

### `AccountantType`

Verified enum values:

- `RDP`
- `PLD`

The enum exposes `get_accountant()` to create the underlying `dp_accounting` object.

### Tree aggregation helpers

Verified public functions:

- `compute_rdp_tree_restart(noise_multiplier, steps_list, orders)`
- `compute_rdp_single_tree(noise_multiplier, total_steps, max_participation, min_separation, orders)`
- `compute_zcdp_single_tree(noise_multiplier, total_steps, max_participation, min_separation)`

## CLI flag maps

### `compute_dp_sgd_privacy.py`

Required flags:

- `--N`
- `--batch_size`
- `--noise_multiplier`
- `--epochs`

Optional flags:

- `--delta`
- `--used_microbatching` / `--no-used_microbatching`
- `--max_examples_per_user`
- `--accountant_type {RDP,PLD}`

### `compute_noise_from_budget.py`

Required flags:

- `--N`
- `--batch_size`
- `--epsilon`
- `--epochs`

Optional flags:

- `--delta`
- `--min_noise`

## Decision points

- Use example-level accounting unless the user explicitly needs user-level guarantees.
- Use `RDP` for the default path and `PLD` only when the user asks or when the analysis requires it.
- Preserve the difference between training-time microbatching and the accounting assumptions.
