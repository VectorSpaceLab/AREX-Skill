import argparse
import json
import random


def sample_hypercube(dimension, count, lower=0.0, upper=1.0, seed=None):
    rng = random.Random(seed)
    return [[rng.uniform(lower, upper) for _ in range(dimension)] for _ in range(count)]


def sample_boundary(dimension, count, lower=0.0, upper=1.0, seed=None):
    rng = random.Random(seed)
    points = []
    faces = []
    for index in range(count):
        point = [rng.uniform(lower, upper) for _ in range(dimension)]
        if count >= 2 * dimension:
            axis = (index // 2) % dimension
            side = lower if index % 2 == 0 else upper
        else:
            axis = rng.randrange(dimension)
            side = lower if rng.random() < 0.5 else upper
        point[axis] = side
        points.append(point)
        faces.append({"axis": axis, "side": side})
    return points, faces


def face_coverage(faces, dimension, lower=0.0, upper=1.0):
    observed = {(face["axis"], face["side"]) for face in faces}
    expected = {(axis, side) for axis in range(dimension) for side in (lower, upper)}
    return {"covered": len(observed), "total": len(expected), "all_faces": expected.issubset(observed)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dimension", type=int, required=True)
    parser.add_argument("--interior-count", type=int, default=8)
    parser.add_argument("--boundary-count", type=int, default=8)
    parser.add_argument("--lower", type=float, default=0.0)
    parser.add_argument("--upper", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    interior = sample_hypercube(args.dimension, args.interior_count, args.lower, args.upper, args.seed)
    boundary, faces = sample_boundary(args.dimension, args.boundary_count, args.lower, args.upper, args.seed + 1)
    print(json.dumps({"interior": interior, "boundary": boundary, "faces": faces}, indent=2))


if __name__ == "__main__":
    main()
