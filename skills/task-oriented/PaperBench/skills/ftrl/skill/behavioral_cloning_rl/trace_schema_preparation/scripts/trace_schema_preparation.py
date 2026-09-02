import json
from pathlib import Path

REQUIRED_FIELDS = ["height", "distance", "elevation", "airspeed"]

def validate_rows(rows):
    if not rows:
        raise ValueError("trace rows are empty")
    for index, row in enumerate(rows):
        missing = [field for field in REQUIRED_FIELDS if field not in row]
        if missing:
            raise ValueError(f"row {index} missing fields: {missing}")
    return True

def goal_from_state(row):
    height = float(row["height"])
    distance = float(row["distance"])
    if distance > -4000:
        return 0
    if height > 1900:
        return 20
    if height > 1000:
        return 60
    return 100

def action_from_goal(row, goal):
    error = float(goal) - float(row["elevation"])
    if error > 8:
        return "raise"
    if error < -8:
        return "lower"
    return "hold"

def prepare_examples(rows, source="synthetic_proxy"):
    validate_rows(rows)
    examples = []
    for index, row in enumerate(rows):
        goal = row.get("goal_elevation", goal_from_state(row))
        action = row.get("elevator_action", action_from_goal(row, goal))
        examples.append({
            "index": index,
            "height": float(row["height"]),
            "distance": float(row["distance"]),
            "elevation": float(row["elevation"]),
            "airspeed": float(row["airspeed"]),
            "goal_elevation": int(goal),
            "elevator_action": str(action),
            "source": source,
        })
    return examples

def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    rows = json.loads(Path(args.input).read_text())
    examples = prepare_examples(rows)
    Path(args.output).write_text(json.dumps({"examples": examples}, indent=2) + "\n")

if __name__ == "__main__":
    main()
