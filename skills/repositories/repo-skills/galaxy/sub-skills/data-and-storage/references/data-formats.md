# Data Formats

Galaxy datatypes connect a history dataset to a format, extension, metadata contract, preview behavior, upload auto-detection, converters, and downstream tool compatibility. Changes here affect production upload, metadata-setting, and large-file behavior, so keep implementations bounded and tests concrete.

## Decision Checklist

1. Decide whether the format needs a real subclass or only a restricted extension that reuses an existing class via `subclass="True"` in datatype registration.
2. Choose the closest existing base class: text/tabular/sequence/image/binary/composite formats already provide metadata, peek, and provider behavior.
3. Set a lowercase extension using only letters, digits, `_`, `-`, and `.`; keep `file_ext` and registration extension aligned.
4. Add metadata only when tools will consume it; do not use metadata as a full viewer or parser substitute.
5. Add a sniffer only when auto-detection is useful and the format has a rigid, cheap signature.
6. Add unit coverage for positive and negative sniffing plus any metadata/peek behavior that tools rely on.

## Registration Pattern

Datatype registration is loaded from `datatypes_conf.xml` at startup and maps extensions to datatype classes. A normal entry declares an extension and a Python class path, optionally with a mimetype and upload display flag. A subtype-only entry can reuse an existing datatype class with `subclass="True"` when no new Python behavior is needed.

Sniffer order is separate from type registration. Rigid binary or signature-based formats should be placed before broad text/tabular formats; ambiguous catch-all sniffers belong later. When a new sniffer starts matching existing files, add explicit negative tests for nearby datatypes.

## Implementation Pattern

- Define the class near similar datatypes, usually under the module that owns the base behavior.
- Set `file_ext` on the class and call the superclass implementations from `__init__`, `init_meta`, `set_meta`, or `set_peek` when extending existing behavior.
- Use `MetadataElement` for values that tools will filter, display, or validate; set defaults and `no_value` consistently with existing datatype families.
- For composite datatypes, choose `composite_type = "basic"` when a primary file is supplied and `"auto_primary_file"` when Galaxy generates the primary index/HTML file. Register component files with explicit names and binary/optional flags.
- Avoid allowing arbitrary datatype changes for composite formats whose component filenames depend on metadata; otherwise users can lose the metadata needed to reconstruct component paths.

## Sniffer Safety

Galaxy’s production checklist forbids sniffers that read a whole file or use unbounded memory. Sniffers run during upload and can be invoked against very large user files, so they should return quickly from bounded evidence.

Safe patterns:

- Read a fixed number of bytes or lines.
- Use Galaxy helper functions that bound headers or sample lines.
- Validate rigid magic bytes, first-line markers, short headers, archive member names, or a bounded structured prefix.
- Return `False` on parse errors without logging noisy tracebacks for normal non-matches.

Risky patterns:

- `open(filename).read()` without a size.
- `for line in open(filename)` in `sniff` with no explicit count or early upper bound.
- Loading complete JSON/XML/archive/tabular files to decide whether the format matches.
- Scanning to EOF in `set_peek` or `set_meta` unless the metadata value genuinely requires it and the implementation is streaming, justified, and tested.

Use `scripts/check_datatype_sniffer.py` as a first-pass review aid, then manually verify context; it is conservative and pattern-based, not a proof of safety.

## Test Guidance

Prefer focused tests near existing datatype tests. Good tests cover:

- Positive sniff for a minimal valid sample.
- Negative sniff for empty, truncated, wrong-extension, and nearby-format samples.
- Bounded behavior by using a large synthetic file whose signature is absent after the prefix.
- Metadata values populated by `set_meta` and user-visible `set_peek` output.
- Registration behavior when the change adds a new extension or changes sniffer order.

Useful native candidate families include datatype registry tests, sniffer tests, sequence/tabular/image/VCF/BAM datatype tests, and docs’ production datatype checklist. Treat those as evidence and adaptation targets; do not require future agents to open the source repository to use this skill.
