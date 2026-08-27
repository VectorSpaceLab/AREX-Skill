# Serving workflows

## A. Safe non-interactive CLI planning

Use this sequence when the intended result is an mmCIF file and no interactive
server is needed.

1. **Check the contract.** Decide which protein, RNA, and DNA entities are
   needed. The CLI supports only these three entity families; it has no ligand
   or ion options. Route conversion and richer heterogeneous inputs to the
   input-representation sibling.
2. **Check the checkpoint.** Confirm the checkpoint is an existing regular file
   readable by the eventual runtime. A path that exists but contains a model
   with incompatible constructor/state keys can pass this preflight and still
   fail in `init_and_load`; use model-inference for that diagnosis.
3. **Choose bounded sampling.** If explicitly setting `--num-sample-steps`, use
   a positive integer appropriate to the available compute. This controls model
   sampling work; it does not make a production model cheap or guarantee a
   successful load.
4. **Choose device behavior.** Pass `--use-cuda true` only when CUDA is desired.
   The CLI checks `torch.cuda.is_available()` before moving the model. If the
   request is true but CUDA is unavailable, it silently keeps the model where it
   was loaded (normally CPU). Passing `false` also keeps it there. This is a
   fallback, not a CUDA diagnostic; use the root environment check for hardware
   details.
5. **Build, do not execute.** Run the bundled helper from any current directory
   with a checkpoint, repeated entity options, and output path. Review the
   shell-safe command it prints. The helper checks path and sequence contracts
   but never loads the package or starts inference.
6. **Execute only after review.** The real CLI loads the checkpoint, calls
   `forward_with_alphafold3_inputs(..., return_bio_pdb_structures=True)`, creates
   missing output parents, and writes mmCIF. It has no dry-run switch.
7. **Verify the artifact.** Check that the reported output path is the intended
   `.cif`/`.mmcif` destination and that the file exists. Structure quality,
   atom semantics, and checkpoint internals are sibling responsibilities.

### Repeated-entity planning example

```bash
python scripts/build_cli_command.py \
  --checkpoint /models/af3.pt \
  --protein MKTW \
  --protein AGTC \
  --rna ACGU \
  --dna ACGT \
  --dna TTAA \
  --num-sample-steps 8 \
  --use-cuda true \
  --output results/mixed.cif
```

The helper prints a single shell-safe `alphafold3_pytorch ...` line. It does
not create `/models`, `results`, or any other path.

## B. Local Gradio app planning

Use the app only if an interactive UI is actually required.

1. Check the checkpoint as above. Treat `--checkpoint` as mandatory.
2. Select a disposable, dedicated `--cache-dir`. Startup recursively removes
   an existing directory before recreating it; do not use a shared or valuable
   directory.
3. If supplying `--precision`, record it as an accepted label only. In the
   current app, the intended device/dtype conversion block is commented out:
   the commented code would select CUDA and `getattr(torch, precision)`, but no
   `.to(device, dtype=dtype)` call executes. `--precision float16`,
   `--precision bfloat16`, or an invalid string therefore does not change model
   dtype and does not provide validation or fallback.
4. Start the app only after those destructive cache and server-launch effects
   are accepted. The app loads the model and calls Gradio `launch()`.
5. Add entities one at a time. Polymer values are stripped and uppercased;
   invalid alphabets and values shorter than four characters are rejected with
   an informational message. Ligand labels normalize to the component code
   before `" - "`; ion labels normalize to alphabetic characters only.
6. Set a positive integer copy count. `fold` expands each entity by that count,
   then builds an `Alphafold3Input` and writes a per-session PDB under the cache
   root.
7. Treat session directories as temporary. Unload removes the directory for
   the request's `session_hash`; app restart removes the entire cache root.

The app's UI is a local convenience layer, not a remote service contract. The
source behavior does not configure host binding, authentication, or access
control in this entry point.

## C. Synthetic usability cases

### Case 1: repeated multimolecule command without execution

Input specification:

- checkpoint `/models/af3.pt`;
- proteins `MKTW`, `AGTC`;
- RNA `ACGU`;
- DNA `ACGT`, `TTAA`;
- 8 sampling steps;
- CUDA requested with explicit Click boolean `true`;
- output `runs/mixed/complex.cif`.

Expected helper behavior: exit successfully, print one quoted command containing
five repeated entity options, `--num-sample-steps 8`, `--use-cuda true`, and the
requested output; do not create `runs/`, import torch, load a checkpoint, or
launch a server. The actual CLI's expected behavior after explicit execution is
to create `runs/mixed/` and write mmCIF, subject to a compatible checkpoint and
available runtime resources.

### Case 2: precision-no-effect app assessment

Input specification: an existing compatible checkpoint, disposable cache
`tmp/app-cache`, and `--precision float16` (or `bfloat16`).

Expected assessment: the parser accepts the value, startup deletes and
recreates the cache, and the app loads the model without executing any dtype or
device conversion from that option. Do not promise lower memory, CUDA use, or
quantization. If a caller needs a different dtype/device, route to model and
runtime controls and require explicit, separately verified code; do not suggest
editing or patching the app as part of this sub-skill.
