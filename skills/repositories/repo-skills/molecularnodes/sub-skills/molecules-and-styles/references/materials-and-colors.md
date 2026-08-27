# Materials and colors

This reference covers the material and color contracts used by the static
molecule/style path. Material datablocks, Geometry Nodes assets, mesh
attributes, and evaluated geometry are Blender data; inspect them in a Blender
5.2 host with the MolecularNodes assets available. A Python color-array probe
is useful for shape and range checks, but it cannot prove that a material or
node tree is connected.

## Material inputs and ownership

`Molecule.add_style()` accepts a Blender `Material`, a MolecularNodes
`PresetMaterial`, a `nodebpy` `MaterialBuilder`, a string, or `None`. A preset
or builder is converted to its `.material` datablock before the style node is
created. A string is treated as the name of a MolecularNodes material to append
from the bundled asset library; it is not a general-purpose lookup of an
arbitrary existing material. The default in the current `add_style()` method
is `"MN Default"`.

A preset constructor creates a new, independent Blender material datablock.
The preset instance retains the builder and node handles, exposes the
underlying datablock as `.material`, and exposes its editable node tree as
`.tree`. The `PresetMaterial.node()` helper creates a Geometry Nodes `Material`
node for the preset's datablock. Assigning the same `mat.material` to several
style nodes deliberately shares one datablock; create separate preset
instances when changes must remain independent.

The supported preset constructors and their current parameters are:

```python
mn.material.Default(
    roughness=0.264,
    ao_distance=0.5,
    ao_exponent=1.0,
    *,
    name=None,
)

mn.material.AmbientOcclusion(
    distance=1.0,
    exponent=2.0,
    *,
    name=None,
)

mn.material.Flat(
    outline=True,
    threshold=0.8,
    thickness=0.15,
    *,
    name=None,
)

mn.material.Squishy(
    subsurface_scale=0.2,
    roughness=1.0,
    *,
    name=None,
)

mn.material.TransparentOutline(
    alpha=0.7,
    outline=True,
    outline_color=(0.0, 0.0, 0.0, 1.0),
    threshold=0.2,
    thickness=0.15,
    *,
    name=None,
)
```

The parameters remain writable on the instance where the preset exposes them:
`Default.roughness`, `Default.ao_distance`, `Default.ao_exponent`,
`AmbientOcclusion.distance`, `AmbientOcclusion.exponent`, `Flat.outline`,
`Flat.threshold`, `Flat.thickness`, `Squishy.subsurface_scale`,
`Squishy.roughness`, and the corresponding `TransparentOutline` properties.
Do not substitute constructor or property names from an older asset version.
`TransparentOutline` also sets its material's Blender 5.2
`surface_render_method` to `"BLENDED"`.

For a custom shader, use `nodebpy.shader` inside its material builder and use
`molecularnodes.nodes.shader.MNColor()` when the shader should consume the
molecule color field. `MNColor` has no inputs and exposes `color` and `alpha`
outputs. After building the material, assign `custom.material` to the style's
`Material` socket. The material datablock is the object that owns the shader
node tree; the style node only holds a material value or link.

## Python color helpers

The helpers in `mn.color` have distinct value conventions:

| Helper | Contract |
|---|---|
| `random_rgb(seed=None)` | Returns an RGBA NumPy array in the nominal 0–1 range; when a seed is supplied it resets Python's module-level random generator. |
| `plddt(b_factor)` | Accepts a NumPy array and returns an `(n, 4)` float array using the `>90`, `>70`, `>50`, and fallback bins. |
| `color_from_atomic_number(atomic_number)` | Returns an RGBA NumPy array using 8-bit RGB and alpha `255`. |
| `color_from_element(element)` | Same 8-bit RGBA convention, keyed by an element symbol. |
| `colors_from_elements(atomic_numbers)` | Maps atomic numbers to an array in the same 8-bit convention. |
| `equidistant_colors(values)` | Returns a mapping from each unique value to an 8-bit RGBA tuple. |
| `color_chains_equidistant(chain_ids)` | Returns per-chain 8-bit RGBA rows. |
| `color_chains(atomic_numbers, chain_ids)` | Keeps element colors for non-carbon atoms, replaces carbon colors by chain colors, and returns normalized RGBA floats. |

The molecule's default `Color` attribute is produced by
`color_chains(...)` (with an element-only fallback when chain IDs are not
available), so it is already normalized. Do not store the output of
`color_from_element()` or `colors_from_elements()` directly as a Blender float
color without converting the RGB and alpha values from 0–255 to 0–1. Confirm
shape, length, and finite values before storing any custom array.

## The named `Color` field

Object creation computes a per-atom `Color` mesh attribute. The current
MolecularNodes storage path explicitly writes it as
`databpy.AttributeTypes.FLOAT_COLOR`, not as a generic four-component vector.
The attribute is point-domain data aligned with the molecule's atom order. Its
usual shape is `(number_of_atoms, 4)` and its intended range is normalized RGBA.
The attribute can be consumed in Geometry Nodes with the exact `nodebpy`
helper:

```python
from nodebpy.nodes.geometry import NamedAttribute

stored_color = NamedAttribute.color("Color")
```

`MNColor()` in a shader is the asset-level color bridge and is different from a
standalone `NamedAttribute.color("Color")` node. `g.ColorElement()` and the
other `g.Color...` groups are color producers; they do not by themselves write
the mesh attribute. To change the field for a geometry branch, pass a color
field into `g.SetColor` and continue the geometry into the style:

```python
from molecularnodes.nodes import geometry as g

with mol.tree as tree:
    tree.atoms >> g.SetColor(color=g.ColorElement()) >> g.StyleCartoon() >> tree.join
```

`SetColor` has the constructor contract `SetColor(atoms=None,
selection=True, color=None)`, outputs the updated `atoms` geometry, and applies
the color only where its `selection` field is true. A branch that should use a
stored custom field without modifying it can use `NamedAttribute.color` as the
color input to `SetColor` or let the style/material consume the existing field.

## Geometry color-node contracts

The generated node wrappers are the source of the node constructor contract.
These current high-value wrappers are useful without relying on positional
socket order:

- `g.ColorElement(...)` provides per-element color sockets named by element
  symbols (`c`, `n`, `o`, and so on) and one `color` output.
- `g.ColorAtomicNumber(atomic_number=6, color=None)` maps an atomic-number
  field to a color field, with an optional fallback color input.
- `g.ColorRainbow(factor="Chain", color_space="HSV", offset=0.0,
  hsl_saturation=0.8, hsl_value=0.8, oklab_luminance=0.94,
  oklab_chroma=0.2)` outputs a color field. Valid factor menu values are
  `"Residue"`, `"Chain"`, and `"Structure"`; valid color spaces are `"HSV"`
  and `"OKLab"`.
- `g.ColorAttributeMap(color_space="Linear", name="b_factor", min=0.0,
  max=150.0, input_7=True, a=None, input_1=None, b=None)` reads a named
  numeric attribute and maps it between its color inputs. The generated names
  `input_7` and `input_1` are real wrapper names; inspect the node interface
  before depending on their UI labels.
- `g.ColorAttributeRandom(name="chain_id", colorspace="HSL", color_seed=0,
  hsl_saturation=0.6, hsl_lightness=0.6, oklab_luminance=0.9,
  oklab_chroma=0.2)` colors categories from a named attribute.
- `g.RandomColor(id=0, color_seed=0, colorspace="HSL", hsl_saturation=0.6,
  hsl_lightness=0.6, oklab_luminance=0.9, oklab_chroma=0.2)` returns a color
  field from an integer ID.
- `g.ColorResName()`, `g.ColorSecondaryStructure()`, `g.ColorBackbone()`,
  `g.ColorCommon()`, and `g.ColorPLDDT()` combine color inputs through their
  generated named sockets. Use `inspect.signature` or the generated wrapper
  and then validate the instantiated node's interface; do not invent friendly
  keyword names for sockets whose wrapper names are `socket_*` or `_50`.

All color producers must ultimately provide a `NodeSocketColor`-compatible
field to `SetColor` or a color-consuming style/material input. Use a node link
for a varying field; use a normalized four-tuple only for a constant color.

## Blender socket validation

Blender 5.2 exposes each instantiated group input through `node.inputs`. Do
not assume a generated Python parameter, a visible label, and the actual asset
interface are identical after an asset update. Validate by name and socket
type before assigning:

```python
def require_socket(node, name, bl_idname):
    socket = node.inputs.get(name)
    if socket is None:
        raise RuntimeError(f"Missing {name!r} on {node.name!r}")
    if socket.bl_idname != bl_idname:
        raise TypeError(
            f"{node.name}.{name} is {socket.bl_idname}, expected {bl_idname}"
        )
    return socket

material_socket = require_socket(style_node, "Material", "NodeSocketMaterial")
selection_socket = require_socket(style_node, "Selection", "NodeSocketBool")
```

For an interface-level check, inspect `style_node.node_tree.interface.items_tree`
and compare each input's `name`, `in_out == "INPUT"`, and `socket_type`. For an
ordinary node socket, `socket.type` should be `"MATERIAL"`, `"BOOLEAN"`, or
`"RGBA"`/the color socket's reported Blender type as appropriate. Check
`socket.is_linked` and `socket.links` before replacing a field link. A material
assignment should set `socket.default_value` to a `bpy.types.Material` (or use
the supported nodebpy link path); a color assignment should be a color field or
a normalized RGBA default, not an 8-bit helper array.

If a required socket is absent or has a different type, stop and report the
asset/package mismatch. Do not force an index-based assignment or rename the
socket in the runtime skill. Re-inspect the installed generated wrapper and
asset interface, then either use the current keyword/socket contract or route
the mismatch to installation repair.
