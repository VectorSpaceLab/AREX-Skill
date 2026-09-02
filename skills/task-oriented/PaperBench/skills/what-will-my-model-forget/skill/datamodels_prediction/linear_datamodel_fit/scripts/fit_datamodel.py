#!/usr/bin/env python3
import argparse
import json
import math


def transpose(matrix):
    return [list(column) for column in zip(*matrix)]


def matmul(a, b):
    b_t = transpose(b)
    return [[sum(x * y for x, y in zip(row, column)) for column in b_t] for row in a]


def matvec(a, vector):
    return [sum(x * y for x, y in zip(row, vector)) for row in a]


def solve_linear_system(matrix, vector):
    n = len(vector)
    aug = [list(matrix[row]) + [vector[row]] for row in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(aug[row][col]))
        if abs(aug[pivot][col]) < 1e-12:
            raise ValueError("singular system")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        scale = aug[col][col]
        aug[col] = [value / scale for value in aug[col]]
        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            aug[row] = [value - factor * base for value, base in zip(aug[row], aug[col])]
    return [aug[row][-1] for row in range(n)]


def pearson(xs, ys):
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denom_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denom_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if denom_x == 0 or denom_y == 0:
        return 0.0
    return numerator / (denom_x * denom_y)


def mse(xs, ys):
    return sum((x - y) ** 2 for x, y in zip(xs, ys)) / len(xs)


def validate_xy(x_matrix, y_values):
    if not x_matrix:
        raise ValueError("X must not be empty")
    if len(x_matrix) != len(y_values):
        raise ValueError("X and y row counts differ")
    width = len(x_matrix[0])
    if width == 0:
        raise ValueError("X must have at least one column")
    for row in x_matrix:
        if len(row) != width:
            raise ValueError("X rows have inconsistent widths")
        if any(value not in (0, 1) for value in row):
            raise ValueError("X must be binary")


def fit_linear_datamodel(x_matrix, y_values, ridge=1e-6):
    validate_xy(x_matrix, y_values)
    design = [[1.0] + [float(value) for value in row] for row in x_matrix]
    xt = transpose(design)
    xtx = matmul(xt, design)
    for index in range(len(xtx)):
        xtx[index][index] += ridge
    xtx[0][0] -= ridge
    xty = matvec(xt, [float(value) for value in y_values])
    params = solve_linear_system(xtx, xty)
    intercept = params[0]
    weights = params[1:]
    predictions = predict(x_matrix, weights, intercept)
    return {"weights": weights, "intercept": intercept, "predictions": predictions, "diagnostics": {"pearson": pearson(predictions, y_values), "mse": mse(predictions, y_values)}}


def predict(x_matrix, weights, intercept):
    return [intercept + sum(float(value) * weight for value, weight in zip(row, weights)) for row in x_matrix]


def demo():
    weights = [0.7, -0.2, 0.4]
    x_matrix = [[1, 0, 1], [1, 1, 0], [0, 1, 1], [1, 1, 1], [0, 0, 1], [1, 0, 0]]
    y_values = [0.1 + sum(value * weight for value, weight in zip(row, weights)) for row in x_matrix]
    return fit_linear_datamodel(x_matrix, y_values, ridge=1e-6)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="JSON with X and y")
    parser.add_argument("--output")
    parser.add_argument("--ridge", type=float, default=1e-6)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if args.demo:
        result = demo()
    else:
        with open(args.input, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        result = fit_linear_datamodel(payload["X"], payload["y"], ridge=args.ridge)
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    else:
        print(text)


if __name__ == "__main__":
    main()
