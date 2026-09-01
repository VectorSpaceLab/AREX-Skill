#!/usr/bin/env python3
import argparse, json


def run_ttur_saddle(x0=1.0, y0=1.0, generator_lr=0.05, discriminator_lr=0.2, steps=25):
    if generator_lr < 0 or discriminator_lr < 0 or steps < 1:
        raise ValueError("learning rates must be nonnegative and steps positive")
    x = float(x0)
    y = float(y0)
    trace = []
    def energy(a, b):
        return a * a + b * b
    before = energy(x, y)
    for step in range(int(steps)):
        grad_x = x + 0.1 * y
        grad_y = y - 0.1 * x
        old_x, old_y = x, y
        x = x - generator_lr * grad_x
        y = y - discriminator_lr * grad_y
        trace.append({"step": step, "x_before": old_x, "y_before": old_y, "x_after": x, "y_after": y, "generator_lr": generator_lr, "discriminator_lr": discriminator_lr, "grad_x": grad_x, "grad_y": grad_y, "energy": energy(x, y)})
    after = energy(x, y)
    return {"params_before": {"x": x0, "y": y0}, "params_after": {"x": x, "y": y}, "loss_before": before, "loss_after": after, "trace": trace, "diagnostics": {"separate_rates": generator_lr != discriminator_lr, "optimizer_step_executed": True, "loss_decreased": after < before}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--steps", type=int, default=25)
    parser.add_argument("--generator-lr", type=float, default=0.05)
    parser.add_argument("--discriminator-lr", type=float, default=0.2)
    args = parser.parse_args()
    result = run_ttur_saddle(generator_lr=args.generator_lr, discriminator_lr=args.discriminator_lr, steps=args.steps)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()
