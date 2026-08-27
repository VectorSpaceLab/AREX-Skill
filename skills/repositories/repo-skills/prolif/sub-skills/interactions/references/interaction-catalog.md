# Interaction Catalog

Use exact class names in `Fingerprint(interactions=[...])` and `parameters={...}`. Names are case-sensitive.

## Default interactions

`prolif.Fingerprint()` uses these interactions:

| Name | Purpose | Main default thresholds/parameters |
| --- | --- | --- |
| `Hydrophobic` | Hydrophobic atom contact. | `distance=4.5`; hydrophobic SMARTS excludes charged atoms and carbons attached to N/O/F. |
| `HBDonor` | Ligand donor to protein acceptor H-bond. | Inverted `HBAcceptor`; uses explicit donor hydrogens. |
| `HBAcceptor` | Ligand acceptor to protein donor H-bond. | `distance=3.5`, `DHA_angle=(130, 180)`, acceptor/donor SMARTS. |
| `PiStacking` | Face-to-face plus edge-to-face aromatic stacking. | Wraps `FaceToFace` and `EdgeToFace` with their defaults. |
| `Anionic` | Ligand anion to protein cation ionic interaction. | Inverted `Cationic`; `distance=4.5`. |
| `Cationic` | Ligand cation to protein anion ionic interaction. | `distance=4.5`, cation/anion SMARTS. |
| `CationPi` | Ligand cation to protein aromatic ring. | `distance=4.5`, `angle=(0, 30)`, aromatic ring SMARTS. |
| `PiCation` | Ligand aromatic ring to protein cation. | Inverted `CationPi`. |
| `VdWContact` | Atom contact based on van der Waals radii. | `tolerance=0.0`, `preset="mdanalysis"`, optional `vdwradii`. |

## Available non-bridged names

Verified available names are:

- `Anionic`
- `CationPi`
- `Cationic`
- `EdgeToFace`
- `FaceToFace`
- `HBAcceptor`
- `HBDonor`
- `Hydrophobic`
- `ImplicitHBAcceptor`
- `ImplicitHBDonor`
- `MetalAcceptor`
- `MetalDonor`
- `PiCation`
- `PiStacking`
- `VdWContact`
- `XBAcceptor`
- `XBDonor`

`Fingerprint.list_available(show_bridged=True)` also includes bridged names such as `WaterBridge`.

## Regular interaction parameter guide

| Name | Constructor parameters | Notes |
| --- | --- | --- |
| `Hydrophobic` | `hydrophobic`, `distance=4.5` | SMARTS applies to both ligand and protein residues. |
| `HBAcceptor` | `acceptor`, `donor`, `distance=3.5`, `DHA_angle=(130, 180)` | Uses explicit hydrogens in donor SMARTS. Metadata maps angle to `DHA_angle`. |
| `HBDonor` | Same parameters as `HBAcceptor` | Inverted role; ligand is donor, protein is acceptor. |
| `XBAcceptor` | `acceptor`, `donor`, `distance=3.5`, `AXD_angle=(130, 180)`, `XAR_angle=(80, 140)` | Halogen bond where ligand is acceptor. |
| `XBDonor` | Same parameters as `XBAcceptor` | Inverted role; ligand is donor. |
| `Cationic` | `cation`, `anion`, `distance=4.5` | Ionic interaction where ligand is cation. |
| `Anionic` | Same parameters as `Cationic` | Inverted role; ligand is anion. |
| `CationPi` | `cation`, `pi_ring`, `distance=4.5`, `angle=(0, 30)` | Distance is between cation and ring centroid. |
| `PiCation` | Same parameters as `CationPi` | Inverted role; ligand is aromatic ring. |
| `FaceToFace` | `distance=5.5`, `plane_angle=(0, 35)`, `normal_to_centroid_angle=(0, 33)`, `pi_ring` | Ring centroid and plane geometry. |
| `EdgeToFace` | `distance=6.5`, `plane_angle=(50, 90)`, `normal_to_centroid_angle=(0, 30)`, `pi_ring`, `intersect_radius=1.5` | T-shaped stacking with ring-intersection constraint. |
| `PiStacking` | `ftf_kwargs=None`, `etf_kwargs=None` | Pass nested dictionaries for `FaceToFace` and `EdgeToFace`. |
| `MetalDonor` | `metal`, `ligand`, `distance=2.8` | Ligand is metal, protein is chelating ligand. |
| `MetalAcceptor` | Same parameters as `MetalDonor` | Inverted role; ligand is chelating group. |
| `VdWContact` | `tolerance=0.0`, `vdwradii=None`, `preset="mdanalysis"` | Presets are `mdanalysis`, `rdkit`, and `csd`; `tolerance` must be non-negative. |
| `ImplicitHBAcceptor` | `acceptor`, `donor`, `distance=3.5`, `include_water=False`, `tolerance_dev_daa=25`, `tolerance_dev_dpa=30`, `vina_potential_max=-0.425`, `vina_potential_min=0.565`, `ignore_geometry_checks=False` | Heavy-atom H-bond model with geometry checks and Vina-like score metadata. |
| `ImplicitHBDonor` | Same parameters as `ImplicitHBAcceptor` | Inverted role; use implicit names in `parameters` when `implicit_hydrogens=True`. |

## Bridged interaction catalog

| Name | Constructor parameters | Notes |
| --- | --- | --- |
| `WaterBridge` | `water`, `order=1`, `min_order=1`, `hbdonor=None`, `hbacceptor=None`, `atomgroup_converter_kwargs=None`, `count=False` | Runs ligand-water, water-protein, and optional water-water H-bond fingerprints, then merges paths into `WaterBridge` metadata. |

`WaterBridge` is hidden from `Fingerprint.list_available()` unless `show_bridged=True` is supplied. It also raises a setup error if included without `parameters={"WaterBridge": {"water": ...}}`.

## Geometry and SMARTS families

- Distance-only classes (`Hydrophobic`, `Cationic`, `Anionic`, `MetalDonor`, `MetalAcceptor`) use the first atom in each SMARTS match and a cutoff distance.
- Single-angle classes (`HBAcceptor`, `HBDonor`) combine a distance threshold with one angle and store `DHA_angle` metadata.
- Double-angle classes (`XBAcceptor`, `XBDonor`) combine distance with `AXD_angle` and `XAR_angle` metadata.
- Pi classes compute ring centroids and normals; metadata includes `distance` and `angle`-like geometric values from the underlying class.
- `VdWContact` compares interatomic distance to the sum of VdW radii plus `tolerance`.
- Implicit H-bonds use heavy-atom SMARTS, VdW radii from the `csd` preset internally, optional water handling, atom/plane geometry checks, and `vina_hbond_potential` metadata.

## Selection decision table

| User intent | Prefer |
| --- | --- |
| Standard protein-ligand fingerprint | Default `Fingerprint()` interactions. |
| All built-in non-bridged definitions | `Fingerprint("all")`, then remove irrelevant high-cost names if needed. |
| Heavy-atom-only H-bonds or uncertain explicit hydrogens | `implicit_hydrogens=True` or `ImplicitHBAcceptor`/`ImplicitHBDonor`. |
| Water-mediated ligand-protein H-bonds | Add `WaterBridge` with a `water` selection/molecule and appropriate `order`. |
| Metal coordination | `MetalDonor`/`MetalAcceptor`, plus `VdWContact(preset="rdkit"|"csd")` if VdW radii are missing. |
| Halogen bonds | `XBDonor`/`XBAcceptor`. |
| Aromatic stacking diagnostics | `PiStacking` for combined detection; `FaceToFace`/`EdgeToFace` for separated modes. |
| Every atom-level contact, not just first hit | `count=True` and count-aware exports in `../fingerprints/`. |
