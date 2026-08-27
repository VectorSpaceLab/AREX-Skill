# customization Troubleshooting

## Symptom → cause → fix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| New task data are wired, but the trainer crashes before the first epoch | `task_dict` or dataloader shape does not match the single-input / multi-input contract | Re-check the task layout and follow the repository's examples for that mode. |
| The decoder output shape does not match the labels | The encoder/decoder contract is wrong | Verify the channel count and the label tensor shape before instantiating `Trainer`. |
| `MTAN` fails on a custom encoder | The encoder does not expose `resnet_network` | Add the attribute or choose a non-ResNet architecture. |
| `PLE` raises `No support PLE for multiple inputs MTL problem` | The method only supports single-input tasks | Use `multi_input=False` or choose another architecture. |
| `CGC`, `MMoE`, or `DSelect_k` fail at construction | `img_size` or `num_experts` is missing or the list length is wrong | Provide the required architecture kwargs before instantiation. |
| A custom weighting strategy never updates the shared parameters correctly | The gradient plumbing is incomplete | Start from `AbsWeighting._get_grads` and `_backward_new_grads`. |

## Extension checklist

Before wiring a new dataset or method, confirm:

1. The task dictionary is complete.
2. The loss and metric objects implement the abstract methods.
3. The encoder output shape is known.
4. The decoders match the encoder output.
5. The trainer is using string method names and has the required kwargs.
6. CUDA is available.

## Common best practices

- Start with the simplest possible encoder/decoder pair.
- Verify the task dictionary with a tiny synthetic batch before touching the
  real dataset.
- If you subclass `Trainer`, override the smallest method that changes the
  workflow, such as `process_preds`.
- Keep custom methods close to one benchmark example until the shape and
  gradient contract are proven.
