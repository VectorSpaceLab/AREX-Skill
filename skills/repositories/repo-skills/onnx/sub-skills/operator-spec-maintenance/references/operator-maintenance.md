# ONNX Operator Maintenance Reference

## What belongs here

This reference is for changes that affect the ONNX standard itself: operator schemas, operator-set registrations, type/shape inference in C++, function bodies, reference implementations, backend node tests, version-converter adapters, and generated docs/coverage/proto outputs.

## Typical file map

| Change | Primary files |
| --- | --- |
| New operator or updated operator behavior | `onnx/defs/<domain>/defs.cc`, `onnx/defs/operator_sets.h`, corresponding reference op, backend node test, and tests |
| Older version preserved for compatibility | `onnx/defs/<domain>/old.cc` and shared helpers in the domain's `utils.h`/`utils.cc` |
| Type/shape inference | Named helper in the relevant `defs.cc` file, plus `tests/python/shape_inference_test.py` |
| Function body | `FunctionBody(R"ONNX(... )ONNX")` using compact ONNX text syntax |
| Version conversion | `onnx/version_converter/adapters/*` plus upgrade/downgrade tests |
| Generated docs and coverage | `python onnx/defs/gen_doc.py` and `python onnx/backend/test/stat_coverage.py` |
| Protobuf outputs | `.in.proto` sources, then `python onnx/gen_proto.py` |

## Decision points

- If a behavior change can be decomposed into other ONNX operators without losing clarity, consider a function before introducing a new primitive operator.
- If an existing operator's signature or semantics change, preserve the old version and add the new version explicitly.
- If only the C++ checker/shape inference behavior changes, still update Python-facing tests that expose the same public behavior.
- If the change affects generated docs or coverage, regenerate them only after source edits settle.

## Review checklist

1. Does the schema description clearly state inputs, outputs, attributes, allowed types, and corner cases?
2. Is shape inference named, readable, and guarded against missing shapes/dimensions?
3. Does the reference implementation cover the expected behavior and edge cases?
4. Are backend node tests and shape-inference tests aligned with the new behavior?
5. Do docs/proto/generated artifacts match the source-of-truth files?
6. Did any compatibility or adapter change require a version-converter update?
