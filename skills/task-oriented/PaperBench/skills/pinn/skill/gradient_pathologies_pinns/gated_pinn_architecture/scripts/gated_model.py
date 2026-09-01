import argparse, json, math, random

class BasisModel:
    def __init__(self, seed=0, gated=True):
        rng = random.Random(seed)
        self.gated = gated
        self.weights = [rng.uniform(-0.1, 0.1) for _ in range(4)]
        self.gates = [0.5, 0.5] if gated else [1.0, 1.0]
    def features(self, x, y):
        gx, gy = self.gates
        return [math.sin(math.pi*x)*math.sin(math.pi*y), math.sin(2*math.pi*x)*math.sin(math.pi*y), gx*x, gy*y]
    def predict(self, x, y):
        return sum(w*f for w, f in zip(self.weights, self.features(x, y)))
    def state(self):
        return {"weights": list(self.weights), "gates": list(self.gates), "gated": self.gated}
    def parameter_count(self):
        return len(self.weights) + (len(self.gates) if self.gated else 0)

def _self_test():
    model = BasisModel(seed=2, gated=True)
    assert len(model.features(0.1, 0.2)) == 4
    assert model.parameter_count() == 6
    assert model.state() == BasisModel(seed=2, gated=True).state()

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--self-test", action="store_true"); args = parser.parse_args()
    if args.self_test:
        _self_test(); print("ok"); return
    print(json.dumps(BasisModel().state(), indent=2))
if __name__ == "__main__": main()
