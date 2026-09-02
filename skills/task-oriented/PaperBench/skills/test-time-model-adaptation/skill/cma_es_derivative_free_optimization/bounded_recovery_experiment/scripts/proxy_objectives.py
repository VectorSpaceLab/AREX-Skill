import math

def rotated_ellipsoid_matrix(angle=0.6, condition=30.0):
    c, s = math.cos(angle), math.sin(angle)
    return [[c*c + condition*s*s, c*s*(1.0-condition)], [c*s*(1.0-condition), s*s + condition*c*c]]

def make_rotated_ellipsoid(angle=0.6, condition=30.0):
    matrix = rotated_ellipsoid_matrix(angle, condition)
    def objective(x):
        return float(x[0]*(matrix[0][0]*x[0]+matrix[0][1]*x[1]) + x[1]*(matrix[1][0]*x[0]+matrix[1][1]*x[1]))
    return objective, matrix
