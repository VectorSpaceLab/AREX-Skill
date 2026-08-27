# Reaction SMARTS and Product Handling

RDKit reaction workflows are exposed mainly through `rdkit.Chem.rdChemReactions`; `rdkit.Chem.AllChem.ReactionFromSmarts` is a common convenience alias for the same construction pattern.

## Build and inspect a reaction

```python
from rdkit import Chem
from rdkit.Chem import rdChemReactions

rxn = rdChemReactions.ReactionFromSmarts("[C:1](=[O:2])-[OD1].[N!H0:3]>>[C:1](=[O:2])[N:3]")
warnings, errors = rxn.Validate()
if errors:
    raise ValueError(f"invalid reaction definition: {errors} errors, {warnings} warnings")
print(rxn.GetNumReactantTemplates(), rxn.GetNumProductTemplates())
```

Use `ReactionFromSmarts(smarts, replacements={}, useSmiles=False)` for reaction SMARTS. Set `useSmiles=True` only when the reaction string should be parsed as reaction SMILES, matching the documented `ReactionFromSmarts(..., useSmiles=True)` pattern.

## Run reactions safely

```python
acid = Chem.MolFromSmiles("CC(=O)O")
amine = Chem.MolFromSmiles("NC")
products = rxn.RunReactants((acid, amine))

sanitized = []
for product_set_index, product_set in enumerate(products):
    for product_index, product in enumerate(product_set):
        try:
            Chem.SanitizeMol(product)
        except Exception as exc:
            raise ValueError(
                f"reaction product {product_set_index}:{product_index} failed sanitization"
            ) from exc
        sanitized.append(Chem.MolToSmiles(product, isomericSmiles=True))
```

`RunReactants()` returns a tuple of product tuples. Reaction products can carry valence/aromaticity states that are not safe for descriptor calculation, substructure post-processing, or serialization until sanitized.

## SMARTS semantics that matter

- Mapped dummy atoms in a product template are replaced by the corresponding mapped reactant atom.
- Unmapped dummy atoms remain dummy atoms in the product.
- Product `~` bonds inherit the corresponding reactant bond order where mapping permits it.
- Intramolecular reactions can be represented by wrapping multiple reactant patterns in parentheses, for example `([C:1]=[C;H2].[C:2]=[C;H2])>>[*:1]=[*:2]`.
- Atom map numbers determine how atoms transfer from reactants to products; incomplete or duplicated mapping is a common source of surprising products.
- `Validate()` catches structural reaction definition problems, but it does not prove that products for every reactant will sanitize.

## Product selection pattern

1. Check that each reactant molecule is not `None` before calling `RunReactants()`.
2. Confirm `rxn.GetNumReactantTemplates()` matches the number of reactants supplied.
3. Run the reaction and handle the possibility of zero product sets.
4. Sanitize every candidate product before using it downstream.
5. Canonicalize products with `Chem.MolToSmiles(product, isomericSmiles=True)` for deduplication.
6. Record product set indices when debugging because many reactant matches can produce duplicate products.

## Reaction stereochemistry notes

RDKit reaction handling tries to preserve stereochemistry when enough atom mapping and local context are present:

- If no chiral information is specified in the reaction definition, mapped stereochemistry in reactants is generally preserved.
- If reactant and product templates specify the same mapped chirality, stereochemistry is retained.
- If a mapped center has opposite chirality in reactant and product templates, the product can invert stereochemistry.
- If chirality is present in the reactant template but omitted in the product template, the reaction can destroy that stereochemical specification.
- If chirality is specified only in the product template, the reaction can create a stereocenter, but the template must include enough local context to be meaningful.
- Preservation can fail when multiple bonds around a chiral center are formed or broken and atom mapping is insufficient.

After a stereochemistry-sensitive reaction, sanitize products, keep `isomericSmiles=True`, and assign or inspect CIP labels as described in `standardization-rgroups-stereo.md`.

## RXN and serialization surfaces

When a user has RXN blocks/files instead of reaction SMARTS, stay within `rdChemReactions` constructors and serializers such as reaction block/file readers and `ChemicalReactionToRxnBlock`/reaction SMARTS writers where available in the installed RDKit. Do not depend on source checkout examples at runtime; include tiny reaction strings or bundled fixtures in downstream projects.
