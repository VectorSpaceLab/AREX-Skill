# XML Formatting

Menagerie enforces a deterministic MJCF XML style with `format_xml.py` and a pre-commit hook. Use this reference for formatting or reviewing edited XML; route semantic modeling decisions to `model-editing` and compile/runtime failures to `model-loading`.

## Formatting rules

The formatter enforces the style described in the contributor guide and implemented by the repo formatter:

- 2-space indentation
- double-quoted attribute values
- self-closing empty elements as `<foo/>` with no space before `/>`
- wrap opening tags when they exceed 120 columns
- continuation attributes indented one level deeper than the element depth
- preserve user-authored blank lines between sibling elements
- preserve XML comments
- collapse multi-line attribute values to a single line, because XML parsing normalizes attribute whitespace

The formatter is the source of truth. Editor XML extensions can produce similar output but may not be byte-identical.

## Repo commands

From a Menagerie checkout root:

```bash
# Check formatting and fail if any file differs.
uv run format_xml.py --check path/to/file.xml path/to/other.xml

# Rewrite in place.
uv run format_xml.py --write path/to/file.xml path/to/other.xml

# Print formatted XML to stdout without changing the file.
uv run format_xml.py path/to/file.xml

# Let pre-commit run the hook on selected XMLs.
pre-commit run format-xml --files path/to/file.xml
```

For all tracked XML files, run:

```bash
make check
```

## Bundled helper

This sub-skill includes a portable copy of the formatter behavior:

```bash
python scripts/format_mjcf_xml.py --check path/to/file.xml
python scripts/format_mjcf_xml.py --write path/to/file.xml
python scripts/format_mjcf_xml.py path/to/file.xml > formatted.xml
```

The bundled helper accepts arbitrary file paths relative to the current working directory. It requires `lxml` only when formatting/checking; `--help` works without that dependency.

## Suggested edit workflow

1. Make MJCF edits in the model XML or scene XML.
2. Run formatter in write mode when writes are allowed:

   ```bash
   uv run format_xml.py --write model_dir/model.xml model_dir/scene.xml
   ```

3. Check the formatted diff:

   ```bash
   git diff -- model_dir/model.xml model_dir/scene.xml
   ```

4. Run formatting check mode for reproducibility:

   ```bash
   uv run format_xml.py --check model_dir/model.xml model_dir/scene.xml
   ```

5. Run structural checks and route compile/step smoke to `model-loading` for behavior validation.

## How wrapping works

For a tag whose one-line representation fits within 120 columns, the formatter keeps the tag on one line:

```xml
<geom name="foot" type="sphere" size="0.03" rgba="0.2 0.2 0.2 1"/>
```

When a tag exceeds 120 columns, attributes spill onto continuation lines indented by `(depth + 1) * 2` spaces:

```xml
<geom name="long_visual_name"
  type="mesh"
  mesh="long_mesh_asset_name"
  rgba="0.8 0.8 0.8 1"/>
```

Do not manually align columns or add a space before `/>`; the formatter will remove such style differences.

## Review checklist for XML-only changes

- Formatter check passes on all changed XML files.
- XML includes still use paths valid relative to the XML/model directory.
- `scene*.xml` remains present for standalone model directories unless the directory is intentionally exempt.
- Model XML remains model-only when the repository pattern expects a separate scene wrapper.
- If defaults/classes/assets/worldbody/actuators were reorganized, route semantic review to `model-editing`.
- If scene XML, includes, meshes, actuators, contacts, or keyframes changed, route a selected compile/step smoke to `model-loading`.

## Limitations and edge behavior

- Multi-line attribute values cannot be faithfully recovered after parsing; they are normalized to single-line values.
- XML parse errors must be fixed before formatting can proceed.
- The formatter preserves comments but does not preserve processing instructions or custom XML declarations as separate formatting constructs.
- Formatting success does not prove the MJCF compiles in MuJoCo; run loading validation separately.
