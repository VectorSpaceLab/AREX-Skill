from __future__ import annotations

import json
import math
from pathlib import Path

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def dump_json(data, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def build_grid(width=3, height=3):
    actions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
    states = [(x, y) for y in range(height) for x in range(width)]
    index = {state: idx for idx, state in enumerate(states)}
    transitions = []
    for state_idx, (x, y) in enumerate(states):
        for action_idx, (dx, dy) in enumerate(actions):
            nx = min(width - 1, max(0, x + dx))
            ny = min(height - 1, max(0, y + dy))
            transitions.append({"state": state_idx, "action": action_idx, "next_state": index[(nx, ny)]})
    return {"states": states, "actions": list(range(4)), "transitions": transitions}

def occupancy_matrix(grid, gamma=0.85):
    state_count = len(grid["states"])
    action_count = len(grid["actions"])
    rows = state_count * action_count
    transition = [[0.0] * rows for _ in range(rows)]
    for row_idx, item in enumerate(grid["transitions"]):
        next_state = item["next_state"]
        for next_action in range(action_count):
            transition[row_idx][next_state * action_count + next_action] += 1.0 / action_count
    matrix = [[(-gamma * transition[i][j]) + (1.0 if i == j else 0.0) for j in range(rows)] for i in range(rows)]
    inverse = [[1.0 if i == j else 0.0 for j in range(rows)] for i in range(rows)]
    for col in range(rows):
        pivot = max(range(col, rows), key=lambda row: abs(matrix[row][col]))
        matrix[col], matrix[pivot] = matrix[pivot], matrix[col]
        inverse[col], inverse[pivot] = inverse[pivot], inverse[col]
        scale = matrix[col][col]
        if abs(scale) < 1e-12:
            raise ValueError("singular occupancy system")
        for j in range(rows):
            matrix[col][j] /= scale
            inverse[col][j] /= scale
        for row in range(rows):
            if row == col:
                continue
            factor = matrix[row][col]
            for j in range(rows):
                matrix[row][j] -= factor * matrix[col][j]
                inverse[row][j] -= factor * inverse[col][j]
    return [[sum(inverse[row][state * action_count + action] for action in range(action_count)) for state in range(state_count)] for row in range(rows)]

def loss(forward, backward, target):
    total = 0.0
    count = 0
    for row_idx, row in enumerate(target):
        for state_idx, value in enumerate(row):
            prediction = sum(forward[row_idx][k] * backward[state_idx][k] for k in range(len(backward[state_idx])))
            total += (prediction - value) ** 2
            count += 1
    return total / count

def fit_factorization(target, rank=3, lr=0.002, steps=80):
    forward = [[((i + 1) * (k + 2) % 7) / 20.0 for k in range(rank)] for i in range(len(target))]
    backward = [[((j + 3) * (k + 1) % 5) / 20.0 for k in range(rank)] for j in range(len(target[0]))]
    before = loss(forward, backward, target)
    params_before = {"F00": forward[0][0], "B00": backward[0][0]}
    for _ in range(steps):
        grad_forward = [[0.0] * rank for _ in forward]
        grad_backward = [[0.0] * rank for _ in backward]
        for row_idx, row in enumerate(target):
            for state_idx, value in enumerate(row):
                prediction = sum(forward[row_idx][k] * backward[state_idx][k] for k in range(rank))
                error = 2.0 * (prediction - value) / (len(target) * len(row))
                for k in range(rank):
                    grad_forward[row_idx][k] += error * backward[state_idx][k]
                    grad_backward[state_idx][k] += error * forward[row_idx][k]
        for row_idx in range(len(forward)):
            for k in range(rank):
                forward[row_idx][k] -= lr * grad_forward[row_idx][k]
        for state_idx in range(len(backward)):
            norm = 0.0
            for k in range(rank):
                backward[state_idx][k] -= lr * grad_backward[state_idx][k]
                norm += backward[state_idx][k] * backward[state_idx][k]
            norm = math.sqrt(norm) or 1.0
            for k in range(rank):
                backward[state_idx][k] /= norm
    after = loss(forward, backward, target)
    return {"F": forward, "B": backward, "loss_before": before, "loss_after": after, "params_before": params_before, "params_after": {"F00": forward[0][0], "B00": backward[0][0]}}

def run(rank=3):
    grid = build_grid()
    target = occupancy_matrix(grid)
    result = fit_factorization(target, rank=rank)
    result.update({"grid": grid, "occupancy": target})
    return result

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--rank", type=int, default=3)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    result = run(args.rank)
    if args.self_test:
        assert result["loss_after"] < result["loss_before"]
        assert result["params_before"] != result["params_after"]
        print("ok")
    if args.output:
        dump_json(result, args.output)
