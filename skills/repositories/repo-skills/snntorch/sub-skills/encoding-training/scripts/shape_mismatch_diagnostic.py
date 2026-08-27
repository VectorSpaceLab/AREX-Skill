#!/usr/bin/env python
from __future__ import annotations

import argparse
import json

import torch
import snntorch.functional as SF


def run_case(case: str):
    spk_out = torch.zeros((3, 2, 3))
    loss_fn = SF.mse_count_loss()

    if case == 'batch-size':
        bad_targets = torch.tensor([0, 1, 2], dtype=torch.long)
        fixed_targets = torch.tensor([0, 1], dtype=torch.long)
        fix_note = 'Match the target vector length to the batch size.'
    else:
        bad_targets = torch.tensor([[1, 0, 0], [0, 1, 0]], dtype=torch.long)
        fixed_targets = torch.tensor([0, 1], dtype=torch.long)
        fix_note = 'Use integer class labels, not one-hot rows, for mse_count_loss.'

    try:
        loss_fn(spk_out, bad_targets)
    except Exception as exc:
        error_type = type(exc).__name__
        error_message = str(exc)
    else:
        raise AssertionError('expected a mismatch failure')

    fixed_loss = loss_fn(spk_out, fixed_targets)
    assert torch.isfinite(fixed_loss)
    return {
        'case': case,
        'error_type': error_type,
        'error_message': error_message,
        'fixed_targets_shape': list(fixed_targets.shape),
        'fixed_loss': float(fixed_loss.item()),
        'fix_note': fix_note,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Demonstrate a deliberate spike/target mismatch and the corrected label shape.'
    )
    parser.add_argument('--case', choices=['batch-size', 'one-hot'], default='batch-size')
    args = parser.parse_args()
    summary = run_case(args.case)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
