#!/usr/bin/env python
"""Tiny CPU-safe smoke test for an Accelerate training loop."""

import argparse
import sys


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a tiny CPU Accelerate training loop that exercises prepare, accumulate, backward, scheduler, and gather_for_metrics."
    )
    parser.add_argument("--steps", type=int, default=4, help="Maximum minibatches to train over.")
    parser.add_argument("--batch-size", type=int, default=2, help="Per-process dataloader batch size.")
    parser.add_argument("--gradient-accumulation-steps", type=int, default=2, help="Minibatches to accumulate.")
    parser.add_argument("--seed", type=int, default=13, help="Torch RNG seed.")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.steps < 1:
        raise SystemExit("--steps must be >= 1")
    if args.batch_size < 1:
        raise SystemExit("--batch-size must be >= 1")
    if args.gradient_accumulation_steps < 1:
        raise SystemExit("--gradient-accumulation-steps must be >= 1")

    try:
        import torch
        from accelerate import Accelerator
    except Exception as error:
        print(f"import failed: {error}", file=sys.stderr)
        return 2

    torch.manual_seed(args.seed)
    accelerator = Accelerator(cpu=True, gradient_accumulation_steps=args.gradient_accumulation_steps)

    inputs = torch.linspace(-1.0, 1.0, steps=24, dtype=torch.float32).unsqueeze(1)
    targets = 3.0 * inputs - 0.5
    dataset = torch.utils.data.TensorDataset(inputs, targets)
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=args.batch_size, shuffle=False)

    model = torch.nn.Sequential(torch.nn.Linear(1, 8), torch.nn.Tanh(), torch.nn.Linear(8, 1))
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.95)
    loss_fn = torch.nn.MSELoss()

    model, optimizer, dataloader, scheduler = accelerator.prepare(model, optimizer, dataloader, scheduler)

    losses = []
    model.train()
    for step, batch in enumerate(dataloader):
        if step >= args.steps:
            break
        features, labels = batch
        with accelerator.accumulate(model):
            predictions = model(features)
            loss = loss_fn(predictions, labels)
            accelerator.backward(loss)
            if accelerator.sync_gradients:
                accelerator.clip_grad_norm_(model.parameters(), max_norm=10.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
        losses.append(float(loss.detach().cpu()))

    if not losses:
        print("no training steps executed", file=sys.stderr)
        return 3
    if not all(torch.isfinite(torch.tensor(losses))):
        print(f"non-finite losses observed: {losses}", file=sys.stderr)
        return 4

    model.eval()
    with torch.no_grad():
        eval_features, eval_labels = next(iter(dataloader))
        eval_predictions = model(eval_features)
        gathered_predictions, gathered_labels = accelerator.gather_for_metrics((eval_predictions, eval_labels))
        eval_loss = loss_fn(gathered_predictions, gathered_labels)

    if gathered_predictions.shape != gathered_labels.shape:
        print(
            f"gathered shape mismatch: predictions={tuple(gathered_predictions.shape)} labels={tuple(gathered_labels.shape)}",
            file=sys.stderr,
        )
        return 5
    if not torch.isfinite(eval_loss):
        print(f"non-finite eval loss: {eval_loss}", file=sys.stderr)
        return 6

    accelerator.print(
        "accelerator_loop_smoke ok "
        f"steps={len(losses)} final_train_loss={losses[-1]:.6f} eval_loss={float(eval_loss):.6f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
