#!/usr/bin/env python3
import argparse
import json
import math

EPS = 1e-12


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def to_chw(image):
    if not isinstance(image, list) or not image:
        raise ValueError("image must be a non-empty nested list")
    if _is_number(image[0][0][0]):
        if len(image) == 3:
            return image
        if len(image[0][0]) == 3:
            height = len(image)
            width = len(image[0])
            return [[[float(image[y][x][c]) for x in range(width)] for y in range(height)] for c in range(3)]
    raise ValueError("expected image shape CxHxW or HxWxC with 3 channels")


def normalize_image(image, input_range="minus_one_to_one"):
    chw = to_chw(image)
    if input_range not in {"minus_one_to_one", "zero_to_one"}:
        raise ValueError("input_range must be minus_one_to_one or zero_to_one")
    normalized = []
    for channel in chw:
        out_channel = []
        for row in channel:
            if input_range == "zero_to_one":
                out_channel.append([2.0 * float(value) - 1.0 for value in row])
            else:
                out_channel.append([float(value) for value in row])
        normalized.append(out_channel)
    return normalized


def _shape(chw):
    channels = len(chw)
    height = len(chw[0])
    width = len(chw[0][0])
    return channels, height, width


def _check_same_shape(a, b):
    if _shape(a) != _shape(b):
        raise ValueError("image shapes do not match")


def _avg_pool_2x(chw):
    channels, height, width = _shape(chw)
    pooled_height = max(1, height // 2)
    pooled_width = max(1, width // 2)
    pooled = []
    for c in range(channels):
        channel = []
        for y in range(pooled_height):
            row = []
            for x in range(pooled_width):
                values = []
                for yy in range(2):
                    for xx in range(2):
                        src_y = min(height - 1, 2 * y + yy)
                        src_x = min(width - 1, 2 * x + xx)
                        values.append(chw[c][src_y][src_x])
                row.append(sum(values) / len(values))
            channel.append(row)
        pooled.append(channel)
    return pooled


def _gradient_features(chw):
    channels, height, width = _shape(chw)
    features = []
    for c in range(channels):
        grad_channel = []
        for y in range(height):
            row = []
            for x in range(width):
                right = chw[c][y][min(width - 1, x + 1)]
                down = chw[c][min(height - 1, y + 1)][x]
                row.append((right - chw[c][y][x]) + (down - chw[c][y][x]))
            grad_channel.append(row)
        features.append(grad_channel)
    return features


def proxy_features(chw):
    pooled = _avg_pool_2x(chw)
    return [chw, pooled, _gradient_features(pooled)]


def normalize_tensor(layer):
    channels, height, width = _shape(layer)
    output = [[[0.0 for _ in range(width)] for _ in range(height)] for _ in range(channels)]
    for y in range(height):
        for x in range(width):
            norm = math.sqrt(sum(layer[c][y][x] ** 2 for c in range(channels)) + EPS)
            for c in range(channels):
                output[c][y][x] = layer[c][y][x] / norm
    return output


def layer_distance(layer_a, layer_b):
    _check_same_shape(layer_a, layer_b)
    norm_a = normalize_tensor(layer_a)
    norm_b = normalize_tensor(layer_b)
    channels, height, width = _shape(layer_a)
    total = 0.0
    for c in range(channels):
        for y in range(height):
            for x in range(width):
                total += (norm_a[c][y][x] - norm_b[c][y][x]) ** 2
    return total / float(height * width)


def lpips_distance(image_a, image_b, weights=None, input_range="minus_one_to_one"):
    chw_a = normalize_image(image_a, input_range)
    chw_b = normalize_image(image_b, input_range)
    _check_same_shape(chw_a, chw_b)
    features_a = proxy_features(chw_a)
    features_b = proxy_features(chw_b)
    if weights is None:
        weights = [1.0] * len(features_a)
    if len(weights) != len(features_a):
        raise ValueError("weights length must match feature layers")
    if any(weight < 0 for weight in weights):
        raise ValueError("calibration weights must be non-negative")
    contributions = []
    total = 0.0
    for index, (layer_a, layer_b, weight) in enumerate(zip(features_a, features_b, weights)):
        raw = layer_distance(layer_a, layer_b)
        weighted = raw * weight
        contributions.append({"layer": index, "raw_distance": raw, "weight": weight, "weighted_distance": weighted})
        total += weighted
    return {"distance": total, "layer_contributions": contributions, "feature_mode": "deterministic_proxy"}


def _self_test():
    ref = [[[0.0, 0.1], [0.2, 0.3]], [[0.0, 0.1], [0.2, 0.3]], [[0.0, 0.1], [0.2, 0.3]]]
    mild = [[[0.01, 0.11], [0.21, 0.31]], [[0.0, 0.1], [0.2, 0.3]], [[0.0, 0.1], [0.2, 0.3]]]
    severe = [[[1.0, -1.0], [-1.0, 1.0]], [[-1.0, 1.0], [1.0, -1.0]], [[1.0, 1.0], [-1.0, -1.0]]]
    assert lpips_distance(ref, ref)["distance"] < 1e-9
    assert lpips_distance(ref, mild)["distance"] < lpips_distance(ref, severe)["distance"]
    try:
        lpips_distance(ref, mild, weights=[1.0, -1.0, 1.0])
    except ValueError:
        pass
    else:
        raise AssertionError("negative weights should fail")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="JSON with image_a, image_b, optional weights and input_range")
    parser.add_argument("--output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print(json.dumps({"ok": True}))
        return
    with open(args.input, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    result = lpips_distance(payload["image_a"], payload["image_b"], payload.get("weights"), payload.get("input_range", "minus_one_to_one"))
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
