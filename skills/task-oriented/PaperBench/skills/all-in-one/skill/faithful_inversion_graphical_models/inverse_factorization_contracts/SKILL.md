---
name: inverse_factorization_contracts
description: Build and validate ordered inverse factorization contracts for amortized inference networks from generated inverse graph parents.
---

# Inverse Factorization Contracts

Use this skill after graph inversion has produced inverse parent sets and before building a recovery harness or inference-network parameterization. The skill turns graph edges into ordered factor contracts for `q(z | x)`.

## Inputs

- `inverse_parents`: mapping from latent variable to inverse parents.
- `latents` and `observed` variable lists.
- `elimination_order` from NaMI.
- Optional `families` mapping from variable to distribution family.
- Optional complete sample values for feature-vector construction.

## Outputs

- Ordered contracts with factor variable, parents, latent parents, observed parents, and family.
- A validation report with contract issues.
- Deterministic feature vectors for each factor when values are supplied.

## Workflow

1. Reverse the elimination order to obtain sampling order.
2. Build one factor contract for each latent variable.
3. Split parents into latent and observed parent lists.
4. Attach support-compatible families, defaulting to `gaussian`.
5. Validate that observations are only parents, never factor variables.
6. Use parent order from the contract when constructing feature vectors.

## Validation

Run:

```bash
python tests/test_contracts.py
```

The tests are standard-library only.

## Limitations

The contracts do not select hidden-layer sizes or neural architectures. They specify the structural interface that a neural, MADE-style, or reduced linear student must respect.
