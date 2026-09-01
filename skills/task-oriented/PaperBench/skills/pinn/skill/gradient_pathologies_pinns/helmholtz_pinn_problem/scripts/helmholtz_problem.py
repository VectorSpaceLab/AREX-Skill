import argparse, json, math, random

def exact_u(x, y, a1=1.0, a2=1.0):
    return math.sin(a1 * math.pi * x) * math.sin(a2 * math.pi * y)

def forcing(x, y, a1=1.0, a2=1.0, k=1.0):
    u = exact_u(x, y, a1, a2)
    lap = -((a1 * math.pi) ** 2 + (a2 * math.pi) ** 2) * u
    return lap + (k ** 2) * u

def build_problem(n_interior=16, n_boundary=16, n_eval_side=8, seed=0, a1=1.0, a2=1.0, k=1.0):
    rng = random.Random(seed)
    interior = [(rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in range(n_interior)]
    boundary = []
    per_side = max(1, n_boundary // 4)
    for _ in range(per_side):
        t = rng.uniform(-1, 1)
        boundary.extend([(-1.0, t), (1.0, t), (t, -1.0), (t, 1.0)])
    boundary = boundary[:n_boundary]
    eval_points = []
    if n_eval_side == 1:
        grid = [0.0]
    else:
        grid = [-1.0 + 2.0 * i / (n_eval_side - 1) for i in range(n_eval_side)]
    for x in grid:
        for y in grid:
            eval_points.append((x, y))
    return {
        "interior": interior,
        "boundary": boundary,
        "boundary_values": [exact_u(x, y, a1, a2) for x, y in boundary],
        "eval_points": eval_points,
        "eval_values": [exact_u(x, y, a1, a2) for x, y in eval_points],
        "params": {"a1": a1, "a2": a2, "k": k, "seed": seed},
    }

def relative_l2(predictions, targets):
    num = sum((p - t) ** 2 for p, t in zip(predictions, targets)) ** 0.5
    den = sum(t ** 2 for t in targets) ** 0.5
    return num / max(den, 1e-12)

def _self_test():
    problem = build_problem(seed=3)
    assert len(problem["interior"]) == 16
    assert len(problem["boundary"]) == 16
    assert problem == build_problem(seed=3)
    assert abs(relative_l2(problem["eval_values"], problem["eval_values"])) < 1e-12
    assert abs(forcing(0.25, 0.5)) > 1e-9

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test(); print("ok"); return
    print(json.dumps(build_problem(), indent=2))
if __name__ == "__main__":
    main()
