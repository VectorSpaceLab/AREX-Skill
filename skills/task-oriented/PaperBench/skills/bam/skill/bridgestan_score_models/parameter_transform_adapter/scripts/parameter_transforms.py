#!/usr/bin/env python3
import argparse, json, math
from pathlib import Path

def _bounds(contract):
    lower, upper = float(contract.get("lower")), float(contract.get("upper"))
    if not math.isfinite(lower) or not math.isfinite(upper) or lower >= upper: raise ValueError("finite ordered bounds required")
    return lower, upper

def constrain(unconstrained, contract):
    lower, upper = _bounds(contract)
    sigmoid = 1.0 / (1.0 + math.exp(-unconstrained)) if unconstrained >= 0 else math.exp(unconstrained) / (1.0 + math.exp(unconstrained))
    value = lower + (upper - lower) * sigmoid
    return {"value": value, "valid": True, "message": "ok", "log_abs_jacobian": math.log(upper - lower) + math.log(sigmoid) + math.log1p(-sigmoid)}

def unconstrain(constrained, contract, tolerance=1e-12):
    lower, upper = _bounds(contract)
    if not (lower + tolerance < constrained < upper - tolerance): return {"value": None, "valid": False, "message": "value outside open finite interval", "log_abs_jacobian": None}
    scaled = (constrained - lower) / (upper - lower)
    return {"value": math.log(scaled) - math.log1p(-scaled), "valid": True, "message": "ok", "log_abs_jacobian": math.log(upper - lower) + math.log(scaled) + math.log1p(-scaled)}

def roundtrip(constrained, contract):
    first = unconstrain(constrained, contract)
    if not first["valid"]: return {"valid": False, "message": first["message"], "unconstrained": first, "reconstrained": None, "abs_error": None}
    second = constrain(first["value"], contract)
    return {"valid": True, "message": "ok", "unconstrained": first, "reconstrained": second, "abs_error": abs(second["value"] - constrained)}

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("operation", choices=["constrain", "unconstrain", "roundtrip"]); parser.add_argument("--contract", required=True); parser.add_argument("--value", required=True, type=float); parser.add_argument("--output", required=True); args = parser.parse_args()
    contract = json.loads(Path(args.contract).read_text())
    result = constrain(args.value, contract) if args.operation == "constrain" else unconstrain(args.value, contract) if args.operation == "unconstrain" else roundtrip(args.value, contract)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True)); print(json.dumps({"ok": result.get("valid", False), "output": args.output}, indent=2))
if __name__ == "__main__": main()
