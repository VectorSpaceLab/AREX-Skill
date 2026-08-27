---
name: selections-topology
description: "Use and debug MDAnalysis atom selections, topology attributes,
  groups, fragments, topology guessing, and selection exporters."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MDAnalysis Selections and Topology

Use this sub-skill when a task involves `select_atoms()`, `AtomGroup`/`ResidueGroup`/`SegmentGroup`, topology attributes, `group` or updating selections, bonds/fragments, topology guessing, or exporting selections for another molecular tool.

## Read First

- Start with [Selection Language](references/selection-language.md) for selection grammar, keyword behavior, sorting, dynamic selections, selection groups, geometry, SMARTS, and exporters.
- Use [Topology and Groups](references/topology-groups.md) for group operations, topology attribute access, custom attributes, fragments/bonds, and topology guessing.
- Use [Troubleshooting](references/troubleshooting.md) when selections are empty, reordered, slow, dependency-sensitive, or raise `SelectionError`, `NoDataError`, `ValueError`, or optional RDKit-related errors.
- Run `python scripts/selection_probe.py` from this sub-skill directory to confirm the installed MDAnalysis selection/topology basics with only synthetic data.

## Common Task Routes

- **Selection text**: Prefer `u.select_atoms("...")` or `ag.select_atoms("...")`; remember keywords and string values are case-sensitive and selections are unique/sorted by topology index unless `sorted=False` is passed.
- **Preserve order**: For manually ordered groups such as `ag[[5, 1, 0]]`, pass `sorted=False` to `select_atoms()` or use group concatenation/slicing when duplicates must be preserved.
- **Dynamic selections**: Pass `updating=True` for an `UpdatingAtomGroup` that lazily re-evaluates after trajectory frame changes; avoid it for static topology-only selections in tight loops.
- **Topology attributes**: Add built-in attributes with `u.add_TopologyAttr("masses", values)` or custom `TopologyAttr` subclasses; selectable custom attributes need supported `dtype` values (`bool`, integer, float, string/object).
- **Cross-skill routing**: Send file loading/writing format decisions to `../universe-io/SKILL.md`, converter interoperability to `../formats-converters/SKILL.md`, and numerical distance/analysis algorithms to `../analysis-workflows/SKILL.md`.
