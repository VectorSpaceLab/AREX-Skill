# Interaction Workflows

These recipes choose and test interaction definitions. For trajectory execution, pose iteration, DataFrames, vectors, and pickles, hand off to `../fingerprints/` after constructing the fingerprint.

## Inspect available interactions safely

```bash
python scripts/list_interactions.py
python scripts/list_interactions.py --include-bridged --show-hidden
python scripts/list_interactions.py --details HBAcceptor ImplicitHBAcceptor WaterBridge --include-bridged
```

Use the helper when the agent needs live package facts from the current environment. It only imports ProLIF and introspects class names/signatures; it does not read or write molecular data.

## Tune a standard interaction

```python
import prolif

fp = prolif.Fingerprint(
    ["Hydrophobic", "HBAcceptor", "HBDonor"],
    parameters={
        "Hydrophobic": {"distance": 4.0},
        "HBAcceptor": {"distance": 3.3, "DHA_angle": (140, 180)},
        "HBDonor": {"distance": 3.3, "DHA_angle": (140, 180)},
    },
)
```

Checklist:

- Use exact class names in `parameters`.
- Keep SMARTS overrides local to the interaction being changed.
- Confirm the direct residue method still finds expected matches before running a long job.
- If the issue is residue selection or prepared hydrogens, route to `../molecules-and-io/` before changing cutoffs.

## Use count mode for all atom combinations

```python
fp = prolif.Fingerprint(["Hydrophobic", "HBAcceptor"], count=True)

# Direct residue check: returns all matches instead of first match.
matches = fp.hydrophobic.all(lig_res, prot_res, metadata=True)

# Later, after execution through the fingerprints sub-skill:
# df = fp.to_dataframe(count=True)
# count_vectors = fp.to_countvectors()
```

`count=False` is faster and records the first satisfying atom combination for each residue pair and interaction. Use `count=True` when the user asks for every hydrophobic contact, all H-bond geometries, or count fingerprints.

## Direct residue-level diagnosis

```python
fp = prolif.Fingerprint(["HBDonor", "HBAcceptor", "VdWContact"], count=True)

pair_metadata = fp.metadata(lig_mol[0], prot_mol["ASP129.A"])
hbd_first = fp.hbdonor.any(lig_mol[0], prot_mol["ASP129.A"], metadata=True)
hba_all = fp.hbacceptor.all(lig_mol[0], prot_mol["ASP129.A"], metadata=True)
vdw_best = fp.vdwcontact.best(lig_mol[0], prot_mol["ASP129.A"])
```

Use this when:

- A user believes one residue pair should interact but the full fingerprint is empty.
- A parameter override seems too strict or too permissive.
- Metadata keys are needed for atom indices, distances, and angles.

Do not use this as a substitute for full trajectory or iterable execution; it only checks prepared ProLIF residue objects.

## Configure implicit-hydrogen H-bonds

Use implicit H-bond modes when the structures have heavy atoms only or the explicit hydrogen placement is not meaningful for the analysis.

```python
fp = prolif.Fingerprint(
    ["HBDonor", "HBAcceptor"],
    implicit_hydrogens=True,
    count=True,
    parameters={
        "ImplicitHBDonor": {
            "distance": 3.5,
            "tolerance_dev_daa": 30,
            "tolerance_dev_dpa": 35,
            "ignore_geometry_checks": False,
        },
        "ImplicitHBAcceptor": {
            "distance": 3.5,
            "tolerance_dev_daa": 30,
            "tolerance_dev_dpa": 35,
            "ignore_geometry_checks": False,
        },
    },
)
```

Rules:

- If `implicit_hydrogens=True`, do not pass `parameters={"HBDonor": ...}` or `parameters={"HBAcceptor": ...}`; use implicit names.
- `include_water=True` allows water residues in implicit H-bond detection, but water handling and selections still belong to input preparation.
- `ignore_geometry_checks=True` can recover interactions when geometry metadata cannot be computed, but it may increase false positives.
- Inspect `vina_hbond_potential` and geometry deviation metadata when explaining why implicit and explicit H-bond counts differ.

## Mix `WaterBridge` with normal interactions

```python
fp = prolif.Fingerprint(
    ["HBDonor", "HBAcceptor", "WaterBridge"],
    parameters={
        "HBDonor": {"distance": 3.5},
        "HBAcceptor": {"distance": 3.5},
        "WaterBridge": {
            "water": water_selection,
            "order": 2,
            "min_order": 1,
            "hbdonor": {"distance": 3.5},
            "hbacceptor": {"distance": 3.5},
        },
    },
    count=True,
)
```

Checklist:

- Include `WaterBridge` only when a water AtomGroup/Molecule is already prepared.
- Always provide the nested `parameters["WaterBridge"]` dictionary; `water` is required.
- Use `order=1` for ligand-water-protein bridges, `order>1` for water networks, and `min_order` to filter out shorter bridges.
- For an updating MDAnalysis water selection, ProLIF handles converter defaults internally, but selection logic still belongs to `../molecules-and-io/`.
- After running, bridge records appear under interaction name `WaterBridge` with `water_residues`, `order`, `ligand_role`, `protein_role`, and total `distance` metadata.

## Customize VdW contact radii

```python
fp = prolif.Fingerprint(
    ["VdWContact"],
    parameters={
        "VdWContact": {
            "preset": "rdkit",
            "tolerance": 0.1,
            "vdwradii": {"Na": 2.5, "Co": 2.4},
        }
    },
)
```

Use this when `VdWContact` raises missing-radius errors for uncommon atoms or when a topology includes metals not covered by the default `mdanalysis` preset. `tolerance` must be zero or positive.

## Ignore selected residue pairs

```python
from prolif.residue import Residue


def ignore_sequence_neighbours(res1: Residue, res2: Residue) -> bool:
    same_chain = res1.resid.chain == res2.resid.chain
    close_number = abs(res1.resid.number - res2.resid.number) <= 1
    return same_chain and close_number

fp = prolif.Fingerprint(["HBAcceptor", "HBDonor"], ignore=ignore_sequence_neighbours)
```

Use `ignore` to prevent known-invalid residue pairs from being evaluated. The default skips self-interactions. Do not overuse `ignore` to hide molecule-preparation problems; if residue identifiers are wrong, route to `../molecules-and-io/`.

## Create a custom interaction

Prefer parameter overrides first. Create a custom class only when the detection logic is genuinely new.

```python
import prolif as plf
from rdkit import Geometry

class CloseContact(plf.interactions.Interaction):
    def __init__(self, cutoff=3.0):
        self.cutoff = cutoff

    def detect(self, lig_res, prot_res):
        for lig_atom in lig_res.GetAtoms():
            for prot_atom in prot_res.GetAtoms():
                lig_idx = lig_atom.GetIdx()
                prot_idx = prot_atom.GetIdx()
                lig_point = Geometry.Point3D(*lig_res.xyz[lig_idx])
                prot_point = Geometry.Point3D(*prot_res.xyz[prot_idx])
                distance = lig_point.Distance(prot_point)
                if distance <= self.cutoff:
                    yield self.metadata(
                        lig_res,
                        prot_res,
                        (lig_idx,),
                        (prot_idx,),
                        distance=distance,
                    )

fp = plf.Fingerprint(["CloseContact"], parameters={"CloseContact": {"cutoff": 2.8}})
```

Acceptance checks for custom interactions:

- The class is defined/imported before `Fingerprint(...)` is constructed.
- `detect` yields dictionaries from `self.metadata(...)` rather than bare booleans.
- Metadata includes enough values for future troubleshooting.
- The custom class name does not collide with a built-in unless intentionally replacing it.
