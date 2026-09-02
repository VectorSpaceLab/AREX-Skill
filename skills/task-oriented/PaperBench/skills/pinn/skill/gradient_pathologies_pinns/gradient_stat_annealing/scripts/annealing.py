import argparse, json

def mean_abs(values):
    vals = [abs(v) for v in values]
    return sum(vals) / max(len(vals), 1)

def update_lambdas(residual_grads, data_grads_list, current_lambdas, alpha=0.9, epsilon=1e-12):
    residual_max = max([abs(v) for v in residual_grads] or [0.0])
    hats, updated, data_means = [], [], []
    for grads, lam in zip(data_grads_list, current_lambdas):
        data_mean = mean_abs(grads)
        data_means.append(data_mean)
        hat = residual_max / max(data_mean, epsilon)
        hats.append(hat)
        updated.append((1.0 - alpha) * lam + alpha * hat)
    return {"updated_lambdas": updated, "lambda_hats": hats, "residual_max_abs_grad": residual_max, "data_mean_abs_grads": data_means}

def _self_test():
    out = update_lambdas([2.0, -4.0], [[1.0, -1.0]], [1.0], alpha=0.5)
    assert abs(out["lambda_hats"][0] - 4.0) < 1e-12
    assert abs(out["updated_lambdas"][0] - 2.5) < 1e-12

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--self-test", action="store_true"); args = parser.parse_args()
    if args.self_test:
        _self_test(); print("ok"); return
    print(json.dumps(update_lambdas([2, -4], [[1, -1]], [1]), indent=2))
if __name__ == "__main__": main()
