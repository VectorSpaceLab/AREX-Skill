#!/usr/bin/env python3
"""Print a minimal ColossalAI Booster training-loop template."""
import argparse

TEMPLATE = """
import colossalai
import torch
import torch.nn as nn
from torch.optim import AdamW
from colossalai.booster import Booster
from colossalai.booster.plugin import TorchDDPPlugin


def main():
    colossalai.launch_from_torch(seed=42)
    plugin = TorchDDPPlugin()
    booster = Booster(plugin=plugin)

    model = nn.Linear(8, 2).cuda()
    optimizer = AdamW(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()
    data = [(torch.randn(4, 8).cuda(), torch.randint(0, 2, (4,), device='cuda')) for _ in range(2)]

    model, optimizer, criterion, _, _ = booster.boost(model, optimizer, criterion=criterion)
    model.train()
    for x, y in data:
        optimizer.zero_grad()
        loss = criterion(model(x), y)
        booster.backward(loss, optimizer)
        optimizer.step()


if __name__ == '__main__':
    main()
"""

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Print a minimal torchrun-compatible ColossalAI Booster template.")
    ap.add_argument("--no-comments", action="store_true", help="Accepted for compatibility; template is concise by default.")
    ap.parse_args()
    print(TEMPLATE.strip())
