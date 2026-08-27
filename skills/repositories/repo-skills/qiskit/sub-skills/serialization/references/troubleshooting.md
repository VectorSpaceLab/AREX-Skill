# Serialization troubleshooting

## `qasm3.load()` or `qasm3.loads()` cannot import

**Symptom**: the error references `qiskit_qasm3_import` or a missing optional dependency.

**Cause**: the compatibility importer is optional.

**Fix**: install `qiskit[qasm3-import]`, or use the experimental native parser if its feature coverage is enough for the program.

## QASM2 parse errors

**Symptom**: `QASM2ParseError` reports an unexpected token or end of file.

**Cause**: the program does not follow the accepted OpenQASM 2 grammar or relies on extensions that were not declared.

**Fix**: add the required include path, custom instructions, or strict-mode choice explicitly. For custom gates, verify parameter and qubit counts match the declaration.

## QASM export fails

**Symptom**: `QASM2ExportError` or `QASM3ExporterError` appears.

**Cause**: the circuit uses operations, annotations, or control-flow features that the target text format cannot represent.

**Fix**: simplify the circuit, choose OpenQASM 3 instead of 2 when possible, or use QPY when exact Qiskit structure must survive.

## QPY version errors

**Symptom**: `UnsupportedFeatureForVersion` or a QPY load failure for an older archive.

**Cause**: the requested QPY output version cannot represent the circuit, or the loading environment is older than the archive.

**Fix**: use the default current QPY version unless a target consumer requires older output. For old `use_symengine=True` archives, use a compatible environment to load and re-export with `use_symengine=False`.

## File mode mistakes

**Symptom**: QPY operations fail with stream or bytes/text errors.

**Cause**: QPY needs binary streams, while QASM uses text.

**Fix**: open QPY files as `rb`/`wb` and QASM files as text.
