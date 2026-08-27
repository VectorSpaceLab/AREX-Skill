# Interaction API Reference

This reference covers interaction definition and inspection. It does not cover full trajectory execution or export; use `../fingerprints/` for `run`, `run_from_iterable`, `generate`, `to_dataframe`, vectors, or pickle workflows.

## `prolif.Fingerprint` interaction setup

```python
import prolif

fp = prolif.Fingerprint(
    interactions=None,          # None, "all", or a sequence of class-name strings
    parameters=None,            # {"InteractionName": {"constructor_arg": value}}
    count=False,                # first match only unless True
    vicinity_cutoff=6.0,
    use_segid=None,
    implicit_hydrogens=False,
    ignore=prolif.residue.ignore_self_interactions,
)
```

Key behavior:

- `interactions=None` uses ProLIF defaults: `Hydrophobic`, `HBDonor`, `HBAcceptor`, `PiStacking`, `Anionic`, `Cationic`, `CationPi`, `PiCation`, and `VdWContact`.
- `interactions="all"` includes registered non-bridged interactions except implicit H-bond variants unless `implicit_hydrogens=True` remaps explicit H-bonds.
- `parameters` is validated by interaction name. Unknown keys raise `NameError` even if the interaction is not selected.
- `count=False` binds direct interaction methods to first-match behavior (`any`); `count=True` binds them to all-match behavior (`all`).
- `ignore` is a predicate receiving two `prolif.residue.Residue` objects; returning `True` skips that residue pair.
- `vicinity_cutoff` and `use_segid` affect which residue pairs are searched during generation/execution, but they are not interaction definitions.

## Discovering names

```python
from prolif import Fingerprint

Fingerprint.list_available()
Fingerprint.list_available(show_hidden=True)
Fingerprint.list_available(show_bridged=True)
```

- `show_hidden=False` hides abstract/base classes such as `Distance`, `SingleAngle`, and `DoubleAngle`.
- `show_bridged=False` hides bridged classes; set `show_bridged=True` to include `WaterBridge`.
- Names are class names and are case-sensitive in `interactions` and `parameters`.

The bundled helper can perform the same inspection without mutating data:

```bash
python scripts/list_interactions.py --include-bridged --format json
python scripts/list_interactions.py --details Hydrophobic VdWContact WaterBridge --include-bridged
```

## Direct residue interaction methods

After constructing a fingerprint, every selected regular interaction is attached to the fingerprint object using the lowercase class name:

```python
fp = prolif.Fingerprint(["HBDonor", "HBAcceptor", "Hydrophobic"], count=True)

# `lig_res` and `prot_res` are ProLIF Residue objects.
all_hb = fp.hbdonor.all(lig_res, prot_res, metadata=True)
first_hba = fp.hbacceptor.any(lig_res, prot_res, metadata=True)
best_hydrophobic = fp.hydrophobic.best(lig_res, prot_res)
metadata = fp.metadata(lig_res, prot_res)
```

Direct methods are useful for diagnosing interaction definitions on one residue pair before running a larger fingerprint. They require prepared `prolif.Molecule`/`Residue` objects; route input preparation questions to `../molecules-and-io/`.

Regular interaction methods:

- `interaction.any(lig_res, prot_res, metadata=False)`: first match or `None`.
- `interaction.all(lig_res, prot_res, metadata=False)`: tuple of all matches.
- `interaction.best(lig_res, prot_res)`: metadata for the match with the smallest interaction-specific `distance`, or `None`.
- `Fingerprint.metadata(res1, res2)`: sparse dict `{interaction_name: (metadata_dict, ...)}` for selected non-bridged interactions.

## Metadata shape

Interaction metadata dictionaries include atom indices and any measured geometry values:

```python
{
    "indices": {"ligand": (...,), "protein": (...,)},
    "parent_indices": {"ligand": (...,), "protein": (...,)},
    "distance": 3.2,
    # optional interaction-specific values such as DHA_angle, AXD_angle, angle,
    # plane/atom angle deviations, vina_hbond_potential, water_residues, order...
}
```

- `indices` are indices within the residue fragments.
- `parent_indices` map back to the parent ProLIF molecule via atom `mapindex`.
- Hydrogen bonds use renamed angle keys such as `DHA_angle` for explicit H-bonds.
- Implicit H-bonds can add `ideal_*_angle`, `*_atom_angles`, `*_atom_angle_deviation`, `*_plane_angle`, and `vina_hbond_potential` when geometry checks run.
- `WaterBridge` metadata adds water-specific entries documented below.

## Parameter overrides

Use `parameters` to pass constructor arguments to interaction classes:

```python
fp = prolif.Fingerprint(
    ["Hydrophobic", "VdWContact"],
    parameters={
        "Hydrophobic": {"distance": 4.0},
        "VdWContact": {"preset": "rdkit", "tolerance": 0.1},
    },
)
```

Rules:

- Use the exact class name as the top-level key.
- Use constructor parameter names, not documentation prose names from older versions.
- A key in `parameters` for an unknown interaction raises `NameError`.
- For `implicit_hydrogens=True`, parameterize the implicit class names (`ImplicitHBDonor`, `ImplicitHBAcceptor`), not explicit `HBDonor`/`HBAcceptor` keys.

## Implicit-hydrogen H-bonds

Two equivalent setup styles are available:

```python
# Automatic remapping: HBDonor -> ImplicitHBDonor, HBAcceptor -> ImplicitHBAcceptor
fp = prolif.Fingerprint(
    ["HBDonor", "HBAcceptor"],
    implicit_hydrogens=True,
    count=True,
    parameters={
        "ImplicitHBAcceptor": {"ignore_geometry_checks": False},
        "ImplicitHBDonor": {"ignore_geometry_checks": False},
    },
)

# Explicit class names
fp = prolif.Fingerprint(
    ["ImplicitHBAcceptor", "ImplicitHBDonor"],
    count=True,
    parameters={"ImplicitHBAcceptor": {"tolerance_dev_daa": 30}},
)
```

Important constructor knobs:

- `acceptor`, `donor`: SMARTS patterns.
- `distance=3.5`: donor-acceptor distance cutoff.
- `include_water=False`: whether water residues may participate.
- `tolerance_dev_daa=25`, `tolerance_dev_dpa=30`: donor atom and donor plane deviation tolerances.
- `vina_potential_max=-0.425`, `vina_potential_min=0.565`: piecewise Vina-like hydrogen-bond score thresholds.
- `ignore_geometry_checks=False`: skip geometric filtering when necessary, at the cost of more false positives.

`ImplicitHBDonor` is generated by inverting `ImplicitHBAcceptor`, so the same constructor parameter names apply with ligand/protein roles swapped.

## `WaterBridge`

`WaterBridge` is a bridged interaction and must be configured through `parameters`:

```python
fp = prolif.Fingerprint(
    ["HBDonor", "WaterBridge"],
    parameters={
        "WaterBridge": {
            "water": water_selection_or_water_molecule,
            "order": 1,
            "min_order": 1,
            "hbdonor": {"distance": 3.5},
            "hbacceptor": {"distance": 3.5},
        }
    },
    count=True,
)
```

Constructor parameters:

- `water`: MDAnalysis `AtomGroup` or iterable/`Molecule` containing water molecules; required.
- `order=1`: maximum number of waters in a bridge.
- `min_order=1`: minimum number of waters to report.
- `hbdonor=None`, `hbacceptor=None`: parameter dictionaries for the internal `HBDonor` and `HBAcceptor` fingerprints.
- `atomgroup_converter_kwargs=None`: optional MDAnalysis RDKit converter kwargs for water AtomGroups.
- `count=False`: passed automatically from `Fingerprint(count=...)` when not explicitly set.

Water-bridge runtime metadata includes:

- `water_residues`: ordered water residue identifiers involved in the bridge.
- `order`: number of water molecules in the bridge.
- `ligand_role` and `protein_role`: H-bond roles at both ends of the bridge.
- `distance`: total bridge distance.
- Per-edge keys such as `distance_<water>_protein`, `DHA_angle_<water>_protein`, or water-water edge suffixes for higher-order bridges.

## Custom interaction classes

ProLIF registers subclasses of `prolif.interactions.Interaction` by class name. A custom interaction must implement `detect(self, lig_res, prot_res)` and yield metadata dictionaries using `self.metadata(...)`:

```python
from prolif.interactions import Interaction

class CloseContact(Interaction):
    def detect(self, lig_res, prot_res):
        # Find atom pairs and yield metadata for accepted matches.
        yield self.metadata(lig_res, prot_res, (lig_idx,), (prot_idx,), distance=dist)

fp = prolif.Fingerprint(["CloseContact"])
```

Subclassing existing interactions can be simpler when only SMARTS or cutoffs change:

```python
import prolif as plf

class CHOAcceptor(plf.interactions.HBAcceptor):
    def __init__(self, distance=3.5):
        super().__init__(donor="[C]-[H]", distance=distance)
```

Keep custom class definitions importable in the active Python process before constructing `Fingerprint`; pickle portability for custom classes depends on the class still being importable when unpickling.
