import argparse, json, math

def mse(values):
    return sum(v*v for v in values) / max(len(values), 1)

def finite_grad_weights(model, loss_fn, epsilon=1e-5):
    grads = []
    for i in range(len(model.weights)):
        old = model.weights[i]
        model.weights[i] = old + epsilon; plus = loss_fn()
        model.weights[i] = old - epsilon; minus = loss_fn()
        model.weights[i] = old
        grads.append((plus - minus) / (2 * epsilon))
    return grads

def compute_losses(model, problem, forcing_fn, lambdas=None):
    lambdas = lambdas or [1.0]
    interior = problem["interior"]
    boundary = problem["boundary"]
    boundary_values = problem["boundary_values"]
    residual_errors = [model.predict(x, y) - forcing_fn(x, y) / 10.0 for x, y in interior]
    boundary_errors = [model.predict(x, y) - target for (x, y), target in zip(boundary, boundary_values)]
    residual_loss = mse(residual_errors)
    boundary_loss = mse(boundary_errors)
    return {"residual_loss": residual_loss, "boundary_loss": boundary_loss, "total_loss": residual_loss + lambdas[0] * boundary_loss}

def _self_test():
    class M:
        weights=[0.1]
        def predict(self,x,y): return self.weights[0]*x*y
    problem={"interior":[(0.2,0.3)],"boundary":[(1,0.2)],"boundary_values":[0.0]}
    out=compute_losses(M(), problem, lambda x,y: 1.0, [2.0])
    assert out["total_loss"] >= out["residual_loss"]

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--self-test", action="store_true"); args=parser.parse_args()
    if args.self_test:
        _self_test(); print("ok"); return
    print(json.dumps({"status":"import this module from a recovery harness"}))
if __name__=="__main__": main()
