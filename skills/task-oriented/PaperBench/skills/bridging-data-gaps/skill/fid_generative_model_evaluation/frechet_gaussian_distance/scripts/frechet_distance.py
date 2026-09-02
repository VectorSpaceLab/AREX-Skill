#!/usr/bin/env python3
import argparse
import json
import math


def _shape_matrix(matrix):
    return len(matrix), len(matrix[0]) if matrix else 0


def _matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]


def _trace(matrix):
    return sum(matrix[i][i] for i in range(len(matrix)))


def _sqrtm_trace_psd_2x2(matrix):
    if len(matrix) == 1:
        return math.sqrt(max(matrix[0][0], 0.0)), 0.0
    if len(matrix) != 2 or len(matrix[0]) != 2:
        raise ValueError("standard-library implementation supports 1x1 or 2x2 covariance matrices")
    a, b = matrix[0]
    c, d = matrix[1]
    det = a * d - b * c
    if det < 0 and abs(det) < 1e-9:
        det = 0.0
    if det < 0:
        raise ValueError("covariance product has negative determinant")
    s = math.sqrt(det)
    trace = a + d
    value = trace + 2.0 * s
    if value < 0 and abs(value) < 1e-9:
        value = 0.0
    if value < 0:
        raise ValueError("covariance product has negative square-root trace argument")
    return math.sqrt(value), 0.0


def calculate_frechet_distance(mu1, sigma1, mu2, sigma2, eps=1e-6):
    mu1 = [float(value) for value in mu1]
    mu2 = [float(value) for value in mu2]
    sigma1 = [[float(value) for value in row] for row in sigma1]
    sigma2 = [[float(value) for value in row] for row in sigma2]
    if len(mu1) != len(mu2):
        raise ValueError("mean vectors have different lengths")
    if _shape_matrix(sigma1) != _shape_matrix(sigma2) or _shape_matrix(sigma1) != (len(mu1), len(mu1)):
        raise ValueError("covariance matrices have incompatible dimensions")
    values = mu1 + mu2 + [value for row in sigma1 + sigma2 for value in row]
    if any(value != value or value in (float("inf"), float("-inf")) for value in values):
        raise ValueError("inputs must be finite")
    diff_term = sum((a - b) ** 2 for a, b in zip(mu1, mu2))
    product = _matmul(sigma1, sigma2)
    regularized = False
    try:
        sqrt_trace, imaginary_max = _sqrtm_trace_psd_2x2(product)
    except ValueError:
        adjusted1 = [[sigma1[i][j] + (eps if i == j else 0.0) for j in range(len(sigma1))] for i in range(len(sigma1))]
        adjusted2 = [[sigma2[i][j] + (eps if i == j else 0.0) for j in range(len(sigma2))] for i in range(len(sigma2))]
        sqrt_trace, imaginary_max = _sqrtm_trace_psd_2x2(_matmul(adjusted1, adjusted2))
        regularized = True
    fid = diff_term + _trace(sigma1) + _trace(sigma2) - 2.0 * sqrt_trace
    if fid < 0 and abs(fid) < 1e-8:
        fid = 0.0
    return {"fid": fid, "diagnostics": {"regularized": regularized, "imaginary_max": imaginary_max, "nonnegative": fid >= -1e-8}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = json.loads(open(args.input_json, encoding="utf-8").read())
    result = calculate_frechet_distance(data["mu1"], data["sigma1"], data["mu2"], data["sigma2"], data.get("eps", 1e-6))
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)


if __name__ == "__main__":
    main()
