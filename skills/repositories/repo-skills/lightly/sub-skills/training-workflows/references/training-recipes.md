# Training recipes

This reference distills the package examples into no-download training patterns. It focuses on how to choose a recipe and how to adapt a method example to a local image folder or synthetic smoke input.

## Recipe selection at a glance

| Family | Start here when... | Loop shape | Notes |
|---|---|---|---|
| SimCLR / NT-Xent | you want the simplest contrastive baseline | two augmented views, projection head, contrastive loss | benefits from larger batches; the SimCLR docs prefer CNN backbones over transformers |
| SimSiam / BYOL / VICReg / Barlow Twins | you want a strong two-view recipe without relying on negatives | two views, projection/prediction or regularized projection, no queue | often easier to run with smaller batches than SimCLR-style losses |
| MoCo | you want contrastive negatives but do not want to depend on a very large batch | two views plus queue or memory bank | useful when batch size per device is limited |
| SwaV | you want multi-crop training | global and local crops, prototype head, assignment loss | the transform must emit the same crop structure the loss expects |
| DINO / iBOT / MAE / LeJEPA / CAPI | you want teacher-student or masked/token-level training | backbone plus task-specific head and specialized loss | more transformer-friendly than SimCLR-style recipes |

If you just need a first pass, start with SimCLR on a CNN backbone and a local image folder. If the backbone is transformer-like, move to a teacher-student or masked recipe instead of forcing SimCLR.

## Bare PyTorch loop pattern

A minimal Lightly-style PyTorch recipe usually looks like this:

```python
transform = transforms.SimCLRTransform(input_size=32, gaussian_blur=0.0)
dataset = LightlyDataset(input_dir="path/to/images", transform=transform)
loader = torch.utils.data.DataLoader(
    dataset,
    batch_size=256,
    shuffle=True,
    drop_last=True,
    num_workers=8,
)

model = SimCLR(backbone)
criterion = loss.NTXentLoss(temperature=0.5)
optimizer = torch.optim.SGD(model.parameters(), lr=0.06)

for epoch in range(num_epochs):
    for views, _, _ in loader:
        x0, x1 = views[:2]
        z0 = model(x0)
        z1 = model(x1)
        step_loss = criterion(z0, z1)
        step_loss.backward()
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
```

Practical rules:
- Keep `drop_last=True` for contrastive and batch-norm-heavy recipes.
- Tune `num_workers` for the host; start small on CPU and increase only if the input pipeline is the bottleneck.
- If you swap the backbone, make sure the projection head input dimension matches the flattened feature size.
- For multi-crop methods, unpack every crop the transform returns instead of assuming exactly two views.

## Adapting a download example to a local folder

Many repository examples use a download-ready dataset for convenience. For a runtime skill, adapt them to a local image folder instead:

1. Keep the method-specific transform.
2. Replace the download dataset with `LightlyDataset(input_dir=..., transform=...)` or a custom local dataset wrapper.
3. Preserve the same model, loss, optimizer, and train loop structure.
4. Use synthetic tensors or the bundled smoke helper to verify feature shapes before you connect real data.

Guidelines for local folders:
- Point `input_dir` at a real directory that already contains images.
- If you need labels later for evaluation, keep the folder structure compatible with a label-aware dataset wrapper, but do not change the self-supervised training loop just to keep labels around.
- Do not build runtime instructions around network downloads, CIFAR fetches, or multi-epoch example runs.

## Method-family notes

- **SimCLR**: straightforward contrastive baseline, but it is sensitive to batch size and augmentation choice.
- **SimSiam**: good when you want a simpler two-view loop without negatives.
- **BYOL**: uses an online/target split; the training recipe still looks like a two-view loop, but the target branch updates differently.
- **MoCo**: introduce the queue or memory bank early so the recipe stays faithful to the method.
- **SwaV**: the crop list matters as much as the model; global and local views must match the loss assumptions.
- **DINO / iBOT / MAE / LeJEPA / CAPI**: usually need a richer backbone/head pairing than the simplest contrastive baseline; keep the training skeleton but swap the specialized head and loss.

## When to stop and use the helper

If you only need to confirm that a backbone output dimension, projection head, and contrastive loss agree, use the bundled synthetic SimCLR step instead of scaling straight to a real dataset.
