from math import sqrt

def dot(a, b):
    if len(a) != len(b):
        raise ValueError('vectors must have the same length')
    return sum(x * y for x, y in zip(a, b))

def add(a, b, alpha=1.0):
    if len(a) != len(b):
        raise ValueError('vectors must have the same length')
    return [x + alpha * y for x, y in zip(a, b)]

def norm(v):
    return sqrt(max(dot(v, v), 0.0))

def normalize(v):
    n = norm(v)
    if n <= 1e-12:
        raise ValueError('cannot normalize a zero vector')
    return [x / n for x in v]

def matrix_hvp(matrix, vector):
    if any(len(row) != len(vector) for row in matrix):
        raise ValueError('matrix/vector shape mismatch')
    return [sum(row[j] * vector[j] for j in range(len(vector))) for row in matrix]

def rayleigh(matrix, vector):
    return dot(vector, matrix_hvp(matrix, vector))
