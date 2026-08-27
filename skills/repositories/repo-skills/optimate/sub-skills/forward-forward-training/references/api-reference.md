# Forward-Forward API Reference

## Public entry point

- `train_with_forward_forward_algorithm(n_layers=2, model_type="progressive", device="cpu", hidden_size=2000, lr=0.03, epochs=100, batch_size=5000, theta=2.0, shuffle=True, **kwargs)`

## Model types

- `ForwardForwardModelType.PROGRESSIVE`
- `ForwardForwardModelType.RECURRENT`
- `ForwardForwardModelType.NLP`

## Routing behavior

- `progressive` uses `FCNetFFProgressiveBuildOperation`, `MNISTDataLoaderOperation`, and `ForwardForwardTrainer`.
- `recurrent` uses `RecurrentFCNetFFBuildOperation`, `MNISTDataLoaderOperation`, and `RecurrentForwardForwardTrainer`.
- `nlp` uses `LMFFNetBuildOperation`, `AesopFablesDataLoaderOperation`, and `NLPForwardForwardTrainer`.
- `predicted_tokens` must be present in `kwargs` for the NLP path.

## Output

The function returns `root_op.get_result()`, which is the trained model produced by the selected branch.

## Note

The model branch is determined by `ForwardForwardModelType(model_type)` and the public API raises if an unsupported value is provided.
