# Embedding and Mining Troubleshooting

## Shape mismatch

`EmbeddingNet` expects a grayscale `1×28×28` image tensor. If a custom dataset uses another shape, the convolution stack or the linear layer will fail.

## Empty mined results

Mining selectors need enough same-class and different-class examples inside the mini-batch. If the batch is too small or label diversity is too low, the mined pair or triplet set can be empty or trivial.

## CPU vs GPU confusion

The mining helpers are label-driven and distance-matrix-driven. Even if the backbone is on GPU, parts of the selector logic may still execute on CPU. That is normal for this repository.

## Margin mismatch

Make sure the selector margin and the loss margin describe the same training intent. Reusing a selector with the wrong margin can make the miner behave very differently from the notebook recipes.

## `EmbeddingNetL2` instability

The L2 variant divides by the embedding norm directly. If a custom input path can produce zero vectors, add an epsilon in your own wrapper or avoid the L2 variant.
