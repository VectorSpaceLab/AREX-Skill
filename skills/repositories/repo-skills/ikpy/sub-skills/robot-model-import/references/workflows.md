# Import workflows and tiny fixtures

These examples are self-contained. They use only inline XML or the bundled
fixture generator; they do not depend on a robot asset, mesh, notebook, or
repository-relative path.

## Generate a temporary smoke set

From the directory containing this sub-skill:

```bash
python scripts/make_tiny_models.py
```

The command creates a temporary directory, writes `tiny.urdf`, `tiny.xml`, and
`tiny.json`, and prints the directory. It does not modify the current directory.
Use `--output-dir PATH` when a caller wants an isolated, caller-owned location.
Then inspect either XML file without writing output:

```bash
python scripts/inspect_model.py /tmp/<printed-dir>/tiny.urdf --fk
python scripts/inspect_model.py /tmp/<printed-dir>/tiny.xml --format mjcf --fk
```

The exact temporary path is intentionally not part of this skill. Capture the
printed path in the shell or pass a known temporary output directory.

## Minimal URDF import

This is the smallest useful flat-chain model. URDF `link` elements declare
frames; IKPy's imported chain entries come from the joints.

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from ikpy.chain import Chain

urdf = '''<robot name="arm">
  <link name="base_link"/>
  <link name="slider_link"/>
  <link name="tip_link"/>
  <joint name="slide" type="prismatic">
    <parent link="base_link"/><child link="slider_link"/>
    <origin xyz="0 0 0" rpy="0 0 0"/>
    <axis xyz="1 0 0"/><limit lower="-0.1" upper="0.1"/>
  </joint>
  <joint name="tip_fixed" type="fixed">
    <parent link="slider_link"/><child link="tip_link"/>
    <origin xyz="0 0 0.2" rpy="0 0 0"/>
  </joint>
</robot>'''

with TemporaryDirectory() as directory:
    path = Path(directory) / "arm.urdf"
    path.write_text(urdf, encoding="utf-8")
    chain = Chain.from_urdf_file(
        str(path),
        base_elements=["base_link", "slide", "slider_link", "tip_fixed", "tip_link"],
        active_links_mask=[False, True, False],
        symbolic=False,
    )
    print([(link.name, link.joint_type) for link in chain.links])
    print(chain.forward_kinematics([0.0] * len(chain.links)))
```

The explicit path is intentionally alternating. A shorter
`base_elements=["base_link"]` starts at the base and auto-follows the first
matching child at each step. If a base link has multiple child joints, use the
full path to avoid source-order selection.

The same path can begin at a joint:

```python
chain = Chain.from_urdf_file(
    "arm.urdf",
    base_elements=["slide", "slider_link", "tip_fixed", "tip_link"],
    base_element_type="joint",
    symbolic=False,
)
```

Do not confuse `base_element_type` with the joint type. It only tells the
traversal whether the first name is a link or a joint.

## URDF joint-list expansion

When a control configuration gives only joint names, expand it before passing it
to the parser:

```python
from ikpy.urdf import URDF
from ikpy.chain import Chain

path = URDF.get_chain_from_joints("arm.urdf", ["slide", "tip_fixed"])
# Example: ["base_link", "slide", "slider_link", "tip_fixed"]
chain = Chain.from_urdf_file("arm.urdf", base_elements=path)
```

The helper returns parent-link/joint alternation and intentionally omits the
terminal child link. Add that child yourself when you want to pin the whole
path, or let traversal auto-follow after the supplied names are consumed.

## JSON metadata round trip

An IKPy JSON metadata file is a small wrapper around a URDF path, not a second
robot-description format:

```json
{
  "urdf_file": "arm.urdf",
  "elements": ["base_link", "slide", "slider_link", "tip_fixed", "tip_link"],
  "active_links_mask": [false, true, false],
  "last_link_vector": "",
  "name": "arm",
  "version": "v1"
}
```

Place that JSON beside `arm.urdf`, then load it with:

```python
from ikpy.chain import Chain
chain = Chain.from_json_file("arm.json")
```

The loader resolves `urdf_file` relative to the JSON file. It converts empty
strings for `elements`, `active_links_mask`, and `last_link_vector` to `None`.
It does not preserve `base_element_type` or `symbolic`; use explicit URDF
loading when those settings are needed.

## Minimal MJCF import

MJCF names nested bodies and puts joints inside those bodies. The path below is
body-only; `hinge` becomes an IKPy revolute joint and `slide` becomes prismatic.

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from ikpy.chain import Chain

mjcf = '''<mujoco model="arm">
  <compiler angle="degree" eulerseq="zyx"/>
  <default class="arm_defaults">
    <joint axis="0 0 1"/>
  </default>
  <worldbody>
    <body name="base" pos="0 0 0">
      <body name="slider" pos="0 0 0.1" childclass="arm_defaults">
        <joint name="slide" type="slide" axis="1 0 0" range="-0.2 0.2"/>
        <body name="wrist" pos="0.2 0 0" euler="0 0 90">
          <joint name="turn" type="hinge" range="-90 90"/>
        </body>
      </body>
    </body>
  </worldbody>
</mujoco>'''

with TemporaryDirectory() as directory:
    path = Path(directory) / "arm.xml"
    path.write_text(mjcf, encoding="utf-8")
    chain = Chain.from_mjcf_file(
        str(path),
        # In IKPy 4.0.0 use one starting body; this unbranched model then
        # follows its first child bodies automatically.
        base_elements=["base"],
        last_link_vector=[0.1, 0.0, 0.0],
        symbolic=False,
    )
    print([(link.name, link.joint_type, link.bounds) for link in chain.links])
    print(chain.forward_kinematics([0.0] * len(chain.links)).shape)
```

With `angle="degree"`, the explicit slide range remains in linear model
units, the explicit hinge range is converted to radians, and the body Euler
angle is converted before it becomes IKPy RPY. The default class supplies the
wrist axis. This IKPy version copies a hinge range inherited from a default
class as provided rather than converting that default range; make critical
ranges explicit or verify `link.bounds` after import. The `eulerseq` setting is
used when converting body `euler` attributes to the RPY representation
consumed by IKPy.

If `base_elements` is omitted, the parser starts at the first body under
`worldbody` and follows the first child body at each level. In this IKPy
version, only the first MJCF `base_elements` name is safely usable: a list of
multiple body names can return an origin-only chain because of the traversal
implementation. Use a one-name start on an unbranched model, inspect the
resulting chain, and do not assume a multi-name body path selected its tip. To
list names before choosing a path:

```python
from ikpy.mjcf import MJCF
print(MJCF.get_body_names("arm.xml"))
print(MJCF.get_joint_names("arm.xml"))
```

`MJCF.get_mjcf_parameters` returns `URDFLink` objects directly when a caller
needs to inspect the parser output without constructing a `Chain`.

## Model inspection and FK smoke check

The bundled inspector is deliberately read-only and uses zero values for every
chain entry when `--fk` is requested:

```bash
python scripts/inspect_model.py arm.urdf --base-elements base_link slide slider_link --fk
python scripts/inspect_model.py arm.xml --format mjcf --base-elements base --no-symbolic --fk
```

It prints the detected format, source links/bodies/joints, chain entry names and
types, active-mask length, and the FK matrix shape. It never renders a graph or
writes a report. A nonzero exit status means the file could not be parsed or
the requested path/settings could not build a chain.

## Optional URDF tree inspection

For an installed Graphviz extra, inspect a URDF's structure without using it as
a kinematic loader:

```python
from ikpy.urdf.utils import get_urdf_tree

dot, tree = get_urdf_tree("arm.urdf", root_element="base_link", legend=True)
print(tree.name, list(tree.children_links))
# Only if an isolated output path was explicitly requested:
# dot, tree = get_urdf_tree("arm.urdf", "base_link", out_image_path="/tmp/arm-tree")
```

Graphviz is optional and rendering needs both the Python package and the
`dot` executable. Route rendering/layout questions to `visualization-geometry`.
