# Training recipes

This reference distills the Jittor training patterns that appear most often in the README and tests.

## 1. Scratch regression or classification

The simplest useful recipe is: build a `Module`, choose a loss, choose an optimizer, then call `opt.step(loss)`.

```python
import jittor as jt
from jittor import nn

class Model(jt.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(1, 1)

    def execute(self, x):
        return self.linear(x)

model = Model()
opt = nn.SGD(model.parameters(), 0.1)

x = jt.float32([[0.0], [1.0]])
y = jt.float32([[1.0], [3.0]])
loss = ((model(x) - y) ** 2).mean()
opt.step(loss)
```

## 2. PyTorch-to-Jittor porting map

| PyTorch habit | Jittor equivalent |
| --- | --- |
| `forward(...)` | `execute(...)` |
| `optimizer.step()` after manual backward | `optimizer.step(loss)` for the simple case, or `optimizer.backward(loss)` followed by `optimizer.step()` for accumulation |
| `model.train()` / `model.eval()` | same concept and same intent |
| `state_dict()` / `load_state_dict()` | same concept; use it to save and restore module state |
| `torch.no_grad()` | `jt.no_grad()` |
| `torch.cuda.synchronize()` | `jt.sync_all()` or a targeted `var.sync()` when you need a concrete value |

## 3. Gradient accumulation

Use accumulation when a large logical batch is split into multiple smaller steps.

```python
opt.zero_grad()
for micro_x, micro_y in micro_batches:
    loss = ((model(micro_x) - micro_y) ** 2).mean()
    opt.backward(loss / accumulation_steps)
opt.step()
```

Rules:

- Divide the loss when you want the average gradient.
- Call `step()` only after the accumulated backward passes.
- Keep the accumulation loop small and deterministic while debugging.

## 4. Train, evaluate, and save

```python
model.train()
loss = ((model(x) - y) ** 2).mean()
opt.step(loss)

model.eval()
with jt.no_grad():
    pred = model(x)
    pred.sync()

state = model.state_dict()
jt.save(state, "checkpoint.pkl")
```

To restore:

```python
loaded = jt.load("checkpoint.pkl")
model.load_state_dict(loaded)
```

## 5. Bounded smoke pattern

The bundled `scripts/training_smoke.py` keeps the exercise small and CPU-only:

1. build a tiny synthetic regression batch,
2. run a few optimizer steps,
3. confirm the loss decreases,
4. switch to `eval()` and `jt.no_grad()` for the final read.

That is enough to validate the training API without turning the smoke into a benchmark.

## 6. When the recipe fails

If loss does not drop, do not immediately change the architecture. First check:

- did the model implement `execute`?
- are the parameters actually in the forward path?
- is the loss reduced to a scalar?
- are you using the right train or eval mode?
- are you accidentally retaining old graphs or storing every loss value?

Those checks are usually more informative than changing hyperparameters right away.