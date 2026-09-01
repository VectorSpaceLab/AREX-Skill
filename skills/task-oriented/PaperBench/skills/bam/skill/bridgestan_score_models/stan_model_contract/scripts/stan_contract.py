#!/usr/bin/env python3
import argparse, json, re
from pathlib import Path
BLOCK_RE = re.compile(r"\b(data|parameters|transformed parameters|model|generated quantities)\s*\{", re.M)

def _find_blocks(source):
    blocks = {}
    for match in BLOCK_RE.finditer(source):
        name = match.group(1).replace(" ", "_")
        index, depth = match.end(), 1
        while index < len(source) and depth:
            depth += source[index] == "{"
            depth -= source[index] == "}"
            index += 1
        blocks[name] = source[match.end(): index - 1]
    return blocks

def parse_stan_contract(source):
    blocks = {k: re.sub(r"//.*", "", v) for k, v in _find_blocks(source).items()}
    contract = {"schema_version": 1, "data": [], "parameters": [], "transformed_parameters": [], "model_terms": [], "generated_quantities": [], "diagnostics": []}
    for statement in re.findall(r"([^;]+);", blocks.get("data", "")):
        statement = " ".join(statement.split())
        match = re.match(r"array\[(?P<size>[^\]]+)\]\s+(?P<type>int|real)(?P<constraint><[^>]+>)?\s+(?P<name>\w+)$", statement) or re.match(r"(?P<type>int|real)(?P<constraint><[^>]+>)?\s+(?P<name>\w+)$", statement)
        if match:
            item = match.groupdict(); item["kind"] = "array" if "array[" in statement else "scalar"; contract["data"].append(item)
        elif statement: contract["diagnostics"].append(f"unsupported data declaration: {statement}")
    for statement in re.findall(r"([^;]+);", blocks.get("parameters", "")):
        statement = " ".join(statement.split())
        match = re.match(r"(?P<type>real)(?P<constraint><[^>]+>)?\s+(?P<name>\w+)$", statement)
        if match:
            item = match.groupdict(); bounds = dict(re.findall(r"(lower|upper)\s*=\s*([^,>]+)", item.get("constraint") or "")); item["lower"] = float(bounds["lower"]) if "lower" in bounds else None; item["upper"] = float(bounds["upper"]) if "upper" in bounds else None; contract["parameters"].append(item)
        elif statement: contract["diagnostics"].append(f"unsupported parameter declaration: {statement}")
    for statement in re.findall(r"([^;]+);", blocks.get("transformed_parameters", "")):
        match = re.match(r"(?P<type>real)\s+(?P<name>\w+)\s*=\s*(?P<expression>.+)$", " ".join(statement.split()))
        if match: contract["transformed_parameters"].append(match.groupdict())
    for statement in re.findall(r"([^;]+);", blocks.get("model", "")):
        match = re.match(r"(?P<lhs>\w+)\s*~\s*(?P<distribution>\w+)\((?P<args>.*)\)$", " ".join(statement.split()))
        if match:
            item = match.groupdict(); item["args"] = [p.strip() for p in item["args"].split(",") if p.strip()]; contract["model_terms"].append(item)
    for statement in re.findall(r"([^;]+);", blocks.get("generated_quantities", "")):
        match = re.match(r"(?P<type>int|real)\s+(?P<name>\w+)\s*=\s*(?P<expression>.+)$", " ".join(statement.split()))
        if match: contract["generated_quantities"].append(match.groupdict())
    return contract

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--stan", required=True); parser.add_argument("--output", required=True); args = parser.parse_args()
    contract = parse_stan_contract(Path(args.stan).read_text()); Path(args.output).write_text(json.dumps(contract, indent=2, sort_keys=True)); print(json.dumps({"ok": not contract["diagnostics"], "output": args.output, "diagnostics": contract["diagnostics"]}, indent=2))
if __name__ == "__main__": main()
