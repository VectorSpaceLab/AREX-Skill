# Generative Model Troubleshooting

## Keras or Torchvision downloads begin during import

Symptoms: importing a script attempts to download MNIST/CIFAR/LSUN or fails in
`keras.datasets`, `torchvision.datasets`, tokenizer, or cache code.

Likely cause: several compact scripts load datasets at module top level for
brevity.

Recovery:

- Do not import the full upstream file for a shape check. Copy the relevant
  class/function into a guarded scratch script.
- Move dataset calls behind `if __name__ == "__main__"` or an explicit function
  in the user's adaptation.
- If full reproduction is required, ask for network/cache approval and install
  the exact per-paper requirements in an isolated environment.

## Old dependency pins conflict

Symptoms: installing several requirements files causes Torch/Keras/Torchvision
resolution failures, import errors, or CUDA ABI mismatches.

Recovery:

1. Use the catalog to identify the single selected entry.
2. Install only that entry's requirements in a new environment.
3. For educational adaptation, loosen pins only after a tiny tensor smoke test
   proves that API changes are handled.

## CUDA hard-code or device mismatch

Symptoms: `RuntimeError: CUDA error`, `Torch not compiled with CUDA enabled`,
`Expected all tensors to be on the same device`, or direct `.cuda()` failures.

Recovery:

- Replace `device = 'cuda'` and `.cuda()` with an explicit `device` argument for
  CPU shape tests.
- Keep realistic text-to-image, DreamBooth, and large image-generation runs on
  a verified GPU when the user needs actual outputs.
- Verify a tiny tensor allocation on the selected device before starting a long
  loop.

## Stable Diffusion checkpoint or tokenizer missing

Symptoms: missing safetensors file, `from_pretrained` download, key mismatch in
`load_state_dict`, or CLIP tokenizer/cache error.

Recovery:

1. Ask for the local checkpoint path and tokenizer/cache policy.
2. Check that checkpoint keys match the minimal model wrapper before sampling.
3. Reduce image size/steps only for debugging; do not claim representative
   quality from a reduced smoke.

## Flow log-determinants are wrong or NaN

Symptoms: Real NVP/MAF/NICE produces NaNs, exploding log-probs, or inconsistent
inverse/forward results.

Recovery:

- Validate a round trip on a tiny tensor: `inverse(forward(x))` near `x` and
  finite log-determinants.
- Check mask shape, squeeze/unsqueeze order, and logit transform clamps.
- Lower learning rate and start with small batches before long training.

## GAN loss does not move

Symptoms: discriminator loss saturates, generator outputs constant images, or
training collapses quickly.

Recovery:

- Confirm input normalization matches the activation range (`Tanh` usually
  expects data in `[-1, 1]`; `Sigmoid` expects `[0, 1]`).
- Preserve per-paper optimizer/loss choices before experimenting.
- Reduce to a few steps with fixed random seed and verify both models receive
  gradients.

## Output directories or image writes fail

Symptoms: `FileNotFoundError` for `Imgs/...`, permission errors, or plots saved
in the wrong location.

Recovery:

- Create a scratch output directory explicitly in the adaptation.
- Avoid writing into the generated skill directory or a read-only checkout.
- For verification, assert tensor shapes and finite values before enabling
  image writes.
