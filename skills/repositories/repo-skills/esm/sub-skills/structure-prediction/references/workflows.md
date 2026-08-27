# Structure Prediction Workflows

## Single Sequence with Python

Use this when the caller has one sequence and wants an in-memory PDB string or direct control over model/device setup.

```python
import torch
import esm

sequence = "MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG"
model = esm.pretrained.esmfold_v1().eval()

if torch.cuda.is_available():
    model = model.cuda()
else:
    model.esm.float()
    model = model.cpu()

model.set_chunk_size(128)

with torch.no_grad():
    pdb_string = model.infer_pdb(sequence)

with open("result.pdb", "w", encoding="utf-8") as handle:
    handle.write(pdb_string)
```

Decision points:

- Use `.cuda()` only when CUDA PyTorch and GPU memory are known to work.
- Use `model.esm.float()` before CPU inference.
- Add `model.set_chunk_size(128)` for long sequences or unknown GPU memory; reduce to `64` or `32` if OOM persists.
- Use `model.infer(..., num_recycles=N)` instead of `infer_pdb` when the caller needs confidence tensors or non-default recycles.

## Multiple FASTA Records with the CLI

Use `esm-fold` for bulk FASTA-to-PDB conversion.

```bash
esm-fold -i proteins.fasta -o pdbs --chunk-size 128 --max-tokens-per-batch 512
```

Preflight checklist:

1. Confirm `fair-esm[esmfold]` and OpenFold-style dependencies are installed.
2. Confirm PyTorch is installed and the intended CPU/CUDA path is available.
3. Confirm the FASTA file exists and contains unique filesystem-safe headers.
4. Confirm the output directory can be created or written.
5. Decide whether downloads are allowed; if not, supply a populated `--model-dir` cache.

## Build Commands Without Running Inference

Use the bundled helper when the user asks for a command, a dry run, or validation of CLI arguments:

```bash
python scripts/esm_fold_command_builder.py \
  --fasta small.fasta \
  --pdb pdbs \
  --cpu-only \
  --chunk-size 128 \
  --max-tokens-per-batch 512
```

The helper prints a shell-quoted command such as:

```bash
esm-fold -i small.fasta -o pdbs --max-tokens-per-batch 512 --chunk-size 128 --cpu-only
```

It validates that the FASTA path exists, that output parent directories are usable, and that mutually risky execution modes such as `--cpu-only` plus `--cpu-offload` are not combined.

## CPU-Only Folding

CPU-only ESMFold is useful for command construction, tiny tests, or environments without GPU, but real folding can be very slow.

CLI:

```bash
esm-fold -i small.fasta -o pdbs --cpu-only --chunk-size 128 --max-tokens-per-batch 512
```

Python:

```python
model = esm.pretrained.esmfold_v1().eval()
model.esm.float()
model = model.cpu()
model.set_chunk_size(128)
```

If CPU inference fails with dtype or half-precision errors, verify the fp32 conversion happened before running inference.

## CUDA OOM Response

For `CUDA out of memory` on a batch of short sequences:

1. Lower `--max-tokens-per-batch` from the default `1024` to `512`, `256`, or `128`.
2. If needed, set `--max-tokens-per-batch 0` to disable batching.
3. Add `--chunk-size 128`, then try `64` or `32`.
4. Reduce `--num-recycles`, for example from default to `2` or `1` when approximate results are acceptable.

For OOM on one long sequence:

1. Batching changes will not help much because the sequence is alone.
2. Use `--chunk-size 128`, then lower to `64` or `32`.
3. Try fewer recycles.
4. If CUDA is present but model weights exceed GPU memory, try `--cpu-offload`.
5. If no GPU path is viable, use `--cpu-only` with a warning about runtime.

## CPU Offload

`--cpu-offload` wraps the ESM language-model component with PyTorch FSDP CPU offload, then places the rest of ESMFold on CUDA. Use it for long sequences or limited GPU memory when CUDA is still available.

Constraints:

- It initializes a local distributed process group and expects a usable CUDA/NCCL stack.
- It is not a replacement for `--cpu-only`.
- It may need enough CPU RAM to hold offloaded parameters.
- Do not combine it with `--cpu-only`.

## Multimer Prediction

For multimer prediction, put all chains in a single sequence with colon separators:

```text
>complex_a_b
MKTAYIAKQRQISFVKSHFSRQ:DLLKKALE
```

Then run:

```bash
esm-fold -i complex.fasta -o pdbs --chunk-size 128
```

In Python:

```python
with torch.no_grad():
    pdb_string = model.infer_pdb("MKTAYIAKQRQISFVKSHFSRQ:DLLKKALE")
```

Do not split chains into multiple FASTA records unless independent monomer predictions are intended.

## Confidence Interpretation

- Use pLDDT as local confidence; higher values are better, and PDB B-factors contain pLDDT values written by `output_to_pdb`.
- Use pTM as global fold confidence, especially for domain arrangement.
- Low pLDDT/pTM should prompt caution or additional validation; it is not a Python or CLI failure by itself.
