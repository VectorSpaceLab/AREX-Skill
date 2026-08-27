# Configuration troubleshooting

## Unknown key during a file or tree merge

**Signal:** `KeyError: Non-existent config key: ...`.

Find the nearest node where the key is introduced. Add the key to the strict
base schema, or construct only the intended extension node with
`new_allowed=True`. Remember that this flag is local: an ancestor's setting
does not make an existing strict child permissive. If the key is intentionally
retired, register its exact dotted path as deprecated or renamed before the
merge.

## Unknown key during a list override

**Signal:** `AssertionError` for a non-existent path or key.

`merge_from_list` traverses existing path components and requires the final
key to exist. It does not use `new_allowed` to create CLI keys. Add the field
through a schema/tree merge first, then apply the list override.

## Type mismatch

**Signal:** `ValueError: Type mismatch (...)`.

Compare the original leaf type with the decoded replacement type. Only
list/tuple and tuple/list conversions are supported. A string such as `0.1`
becomes a float when decoded; an unquoted token that is not a Python literal
stays a string. Use quotes inside the override value when a textual value would
otherwise decode as a number, boolean, list, tuple, dictionary, or `None`.
Do not expect integer/float or boolean/integer coercion.

## Invalid leaf type

**Signal:** `AssertionError` naming a key and an unsupported type.

Replace `None` or an arbitrary object with one of the exact supported leaf
classes: tuple, list, str, int, float, or bool. Convert nested dictionaries
to `CfgNode` by constructing the parent from a dictionary or by assigning a
`CfgNode` attribute; do not assign a raw dictionary as a leaf attribute.

## Frozen assignment fails

**Signal:** `AttributeError` saying the node is immutable.

This is expected for direct attribute assignment after `freeze()`. Do not
mutate the production/base node. Clone it, call `defrost()` on the clone,
apply changes or merges, validate it, and freeze it again. Because the merge
methods use dictionary writes internally, do not rely on a failed attribute
write as proof that a subsequent merge is blocked; establish the desired
policy with the explicit clone/defrost/re-freeze sequence.

## Deprecated key appears to do nothing

**Signal:** a warning about a deprecated config key and no resulting field.

This is the designed behavior: deprecated entries are ignored. Confirm the
full dotted path registered at the root matches the incoming key exactly. If
the old spelling should be corrected rather than ignored, register it as
renamed instead and update the source configuration after reading the
`KeyError` replacement message.

## Renamed key raises

**Signal:** `KeyError: Key ... was renamed to ...`.

Update the input to use the replacement key. If a custom message was registered,
read its migration note after the replacement. Registration is exact; a parent
path or differently cased spelling does not match.

## Python config file is rejected

**Signal:** unsupported filetype, missing `cfg`, or invalid `cfg` type.

Use a `.py` filename with `merge_from_file`. The module must export a variable
named `cfg` whose exact type is `dict` or `CfgNode`. A Python file passed through
`load_cfg` as a string is interpreted as YAML text, not executed. Avoid relying
on imports or ambient working-directory state in a generated config file.

## YAML load or round-trip surprises

**Signal:** a YAML string fails or a loaded value changes container type.

`load_cfg` accepts YAML text, not a path string, and uses safe YAML loading.
Give file objects a supported extension. `dump()` emits YAML data, while
`str()` and `repr()` are diagnostic formats and should not be fed back to the
loader. A tuple may come back from YAML as a list; merge it into a schema whose
original value is a tuple to use the supported coercion.

## Odd override list

**Signal:** `AssertionError` stating that the override list has odd length.

Build the list as key/value pairs and verify `len(opts) % 2 == 0` before
calling `merge_from_list`. Keep each value as one list item; shell quoting is
the caller's responsibility.
