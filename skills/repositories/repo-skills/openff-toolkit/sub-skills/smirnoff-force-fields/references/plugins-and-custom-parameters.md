# Plugins and Custom SMIRNOFF Parameters

OpenFF Toolkit can load custom SMIRNOFF `ParameterHandler` subclasses through Python package entry points. Use this when an OFFXML file contains a non-built-in handler tag such as a custom nonbonded functional form.

## When Plugins Are Needed

A plugin is needed when a force field contains a top-level SMIRNOFF tag that is not one of the built-in handler tags known to the toolkit. Without the handler class, loading or accessing that tag fails because `ForceField` cannot map the tag to a `ParameterHandler` implementation.

Built-in tags include `Bonds`, `Angles`, `ProperTorsions`, `ImproperTorsions`, `vdW`, `Electrostatics`, `LibraryCharges`, `ToolkitAM1BCC`, `NAGLCharges`, `ChargeIncrementModel`, `GBSA`, `Constraints`, and `VirtualSites`.

## Minimal Custom Handler Shape

A custom handler subclasses `ParameterHandler`. A nonbonded custom handler often subclasses `_NonbondedHandler` and declares a nested `ParameterType` with validated `ParameterAttribute` fields.

```python
from openff.toolkit import unit
from openff.toolkit.typing.engines.smirnoff import ParameterHandler
from openff.toolkit.typing.engines.smirnoff.parameters import ParameterAttribute, ParameterType, _NonbondedHandler

class CustomHandler(ParameterHandler):
    _TAGNAME = "CustomHandler"

class FOOBuckinghamHandler(_NonbondedHandler):
    class FOOBuckinghamType(ParameterType):
        _ELEMENT_NAME = "Atom"
        a = ParameterAttribute(default=None, unit=unit.kilojoule_per_mole)
        b = ParameterAttribute(default=None, unit="nanometer**-1")
        c = ParameterAttribute(default=None, unit=unit.kilojoule_per_mole * unit.nanometer**6)

    _TAGNAME = "FOOBuckingham"
    _INFOTYPE = FOOBuckinghamType
```

`_TAGNAME` must match the OFFXML section tag. `_INFOTYPE` tells the handler which parameter object represents each child element. `_ELEMENT_NAME` should match the child XML element, such as `Atom`.

## Entry Point Registration

A package registers handler plugins with the `openff.toolkit.plugins.handlers` entry point group:

```python
setup(
    name="my-openff-handler-plugin",
    packages=["my_handlers"],
    entry_points={
        "openff.toolkit.plugins.handlers": [
            "FOOBuckinghamHandler = my_handlers.smirnoff:FOOBuckinghamHandler",
        ]
    },
)
```

Only classes that inherit from `ParameterHandler` are accepted. Invalid entry points are skipped during plugin discovery.

## Loading Plugins

```python
from openff.toolkit import ForceField

force_field = ForceField("custom-force-field.offxml", load_plugins=True)
handler = force_field.get_parameter_handler("FOOBuckingham")
print(handler.parameters)
```

`load_plugins=False` is the default. If a custom handler exists in the current Python process but is not installed as an entry point, pass it explicitly:

```python
force_field = ForceField(
    "custom-force-field.offxml",
    parameter_handler_classes=[FOOBuckinghamHandler],
)
```

When passing `parameter_handler_classes`, include all handler classes the force field needs if you are replacing the default discovery behavior. For normal installed plugin use, prefer `load_plugins=True`.

## Manual Handler Registration

```python
from openff.toolkit import ForceField
from openff.toolkit.typing.engines.smirnoff.parameters import BondHandler

force_field = ForceField()
bond_handler = BondHandler(version="0.3")
force_field.register_parameter_handler(bond_handler)
assert force_field.get_parameter_handler("Bonds") is bond_handler
force_field.deregister_parameter_handler("Bonds")
```

Registration fails if another handler is already registered for the same tag. Deregistration accepts a tag name or handler instance; attempting to deregister a missing tag raises a key error.

## Safe Caveats for Agents

- Do not set `disable_version_check=True` merely to load a plugin; version compatibility and handler availability are separate issues.
- Do not edit an OFFXML custom tag into a built-in tag name unless the parameter attributes and functional form truly match that built-in handler.
- If a plugin import fails, report the package/entry point problem and preserve the source OFFXML unchanged.
- If plugin discovery silently skips a class, confirm it subclasses `ParameterHandler`.
- Custom handler support lets the toolkit parse and label custom sections, but downstream Interchange/OpenMM export may still fail unless the custom handler is implemented by the export stack.
- Keep plugin installation and environment repair decisions in the backend/dependency sub-skill; this sub-skill only explains the OpenFF Toolkit loading pattern.
