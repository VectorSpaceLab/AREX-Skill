def synthetic_clusters():
    frequent_train = [[0.0, 0.1], [0.1, 0.0], [0.05, 0.05], [-0.05, 0.0], [0.0, -0.05]]
    frequent_eval = [[0.02, 0.08], [0.08, 0.02], [0.04, 0.04]]
    rare_eval = [[1.0, 1.1], [0.9, 1.0], [1.1, 0.9]]
    return frequent_train, frequent_eval, rare_eval


def default_matrices():
    target = [[0.7, -0.2], [0.3, 0.5], [-0.4, 0.6]]
    predictor = [[-0.4, 0.1], [0.2, -0.3], [0.05, 0.2]]
    return target, predictor
