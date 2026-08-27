# Classification Losses

## Available loss choices

- `cross_entropy`
- `focal_loss`
- `class_balanced_cross_entropy`
- `class_balanced_focal_loss`

## When to use each

- **cross_entropy**: the simplest baseline when the class distribution is already balanced.
- **focal_loss**: focus on hard examples when the easy examples dominate.
- **class_balanced_cross_entropy**: reweight classes by effective-number style balancing.
- **class_balanced_focal_loss**: combine class balance with focal shaping.

## Head and metric notes

- The repo supports an optional MLP head for extra separability.
- Validation uses accuracy, precision, recall, and weighted F1.
- Early stopping can trigger when the monitored metric stops improving.

## Shape expectations

- The dataset’s label strings must map to valid class ids.
- The trainer expects one label per sample after collation.
- If the dataset has an eval split, use the same label vocabulary in both splits.
