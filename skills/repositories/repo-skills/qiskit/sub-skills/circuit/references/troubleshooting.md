# Circuit troubleshooting

## `CircuitError` from register or qubit mismatches

**Symptom**: a method complains about an invalid qubit, clbit, register size, or number of arguments.

**Cause**: the circuit operands do not match the instruction arity or the classical resources are not large enough.

**Fix**: check the circuit width first, then add the missing register or use the right operand order.

## `assign_parameters` or gate construction fails

**Symptom**: parameter binding fails, or a gate cannot be turned into a reusable instruction.

**Cause**: the parameter name/value map does not match the circuit, or the circuit contains unsupported instructions for the chosen conversion.

**Fix**: inspect `qc.parameters`, bind by exact parameter objects or exact names, and keep a parameterized and bound copy separate.

## Control-flow bodies reject a condition

**Symptom**: `if_test`, `while_loop`, `for_loop`, or `switch` builders raise an error about the condition or body.

**Cause**: the classical resource requirements of the condition do not match the inner body, or the loop parameter is not present in the body.

**Fix**: rebuild the body with the needed classical bits, or simplify the control-flow condition so it matches the current circuit layout.

## Measurements behave unexpectedly

**Symptom**: a measured circuit no longer works for operator/state analysis or a later transformation.

**Cause**: measurements are still present when you need the abstract unitary part of the circuit.

**Fix**: use `remove_final_measurements(inplace=False)` when you need the same circuit without terminal measurement instructions.

## Drawing output does not match expectations

**Symptom**: `draw()` does not produce the expected format or falls back to a text representation.

**Cause**: the task is really about visualization dependencies, output mode, or style settings rather than circuit construction.

**Fix**: route to the visualization sub-skill and confirm the required optional dependencies are installed.
