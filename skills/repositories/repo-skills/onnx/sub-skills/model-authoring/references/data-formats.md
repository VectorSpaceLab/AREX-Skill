# ONNX Model and Tensor Data Formats

## Core objects

- `ModelProto` carries model metadata, imported operator-set versions, one main `GraphProto`, optional training information, local functions, and device configuration metadata.
- `GraphProto` contains topologically ordered nodes, graph inputs/outputs, initializers, and intermediate `value_info`.
- `NodeProto` names an operator, its input/output value names, domain, and constant attributes.
- `TensorProto` stores element type, dimensions, and either typed fields/raw data or external-data metadata.
- `ValueInfoProto` describes a graph value's name, type, and shape. `TypeProto` can represent tensors, sequences, maps, optionals, sparse tensors, or opaque values.

## Naming and graph invariants

- Node outputs must satisfy single static assignment within a graph.
- Node inputs must refer to graph inputs, initializers, or earlier node outputs.
- Nodes must be topologically ordered and graph outputs must be defined.
- Optional static inputs/outputs can be omitted with trailing omission or an empty string. Dynamic optional values use the `Optional`/`OptionalGetElement` family and are not the same as a missing static input.
- An initializer with the same name as a graph input is a default value that a runtime may allow the caller to override; an initializer without a matching graph input is a constant.

## Serialization formats

| Format | Typical extensions | Notes |
| --- | --- | --- |
| `protobuf` | `.onnx`, `.pb` | Default binary format; use for normal model interchange. |
| `textproto` | `.txtpb`, `.textproto`, `.prototxt`, `.pbtxt` | Google protobuf text representation, not ONNX's compact text grammar. |
| `json` | `.json`, `.onnxjson` | Protobuf JSON field names are preserved by ONNX's serializer. |
| `onnxtxt` | `.onnxtxt`, `.onnxtext` | Experimental compact ONNX model/graph/function/node syntax; use validation after parsing. |

## External tensor data

A tensor with `data_location=EXTERNAL` carries key/value entries. `location` is required and is relative to the model directory; `offset`, `length`, `checksum`, and a runtime-added `basepath` may also appear. External data files use the same little-endian raw-byte representation as `raw_data`.

When data is external, do not assume a loaded `ModelProto` contains usable `raw_data`; decide whether to load external data eagerly, inspect graph structure without loading it, or use `ModelContainer` for in-memory large initializers.

## Shape semantics

A missing tensor shape means unknown rank. A present empty shape means scalar rank zero. A dimension can have a fixed `dim_value`, a symbolic `dim_param`, or neither for an anonymous unknown dimension. Shape inference can propagate rank/types without fully resolving dynamic arithmetic; it is not a runtime shape evaluator.
