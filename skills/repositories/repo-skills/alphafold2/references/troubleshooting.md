# Cross-cutting troubleshooting

Read this for installation, import, backend, or scope failures that span more
than one sub-skill.

## Import fails in `alphafold2_pytorch`

**Symptoms:** `ModuleNotFoundError` for `pytorch3d`,
`invariant_point_attention`, `sidechainnet`, `openmm`, `mdtraj`, `ProDy`, or
`mp_nerf`, or a binary/ABI error while importing a scientific package.

**Recovery:** install the package's declared scientific dependencies as a
compatible set. Match PyTorch and PyTorch3D rather than installing a current
PyTorch wheel after PyTorch3D. For SidechainNet imports, check that its
OpenMM dependency and its legacy `pkg_resources` expectation are satisfied.
Run `scripts/check_environment.py` after each change. Do not treat a partial
import as proof that coordinate or utility routes work.

## Pip resolver replaces a compatible Torch build

The distribution metadata accepts a broad `torch>=1.6` range. A normal install
can select a newer wheel than the installed PyTorch3D build supports. Check
`torch.__version__`, `torch.version.cuda`, and the PyTorch3D version together;
use an isolated environment and a documented compatible wheel/channel set.
Do not repair a user-owned environment in place without approval.

## CUDA is visible but the model cannot run

**Symptoms:** `torch.cuda.is_available()` is true but allocation or `.to("cuda")`
raises out-of-memory, driver, or kernel errors.

**Recovery:** retry the tiny CPU smoke first. Check free memory on the actual
GPU, reduce batch/sequence/MSA dimensions, use one device explicitly, and only
then retry CUDA. A successful import or framework probe does not verify this
repository's GPU forward path.

## Shape or mask errors

Use integer `seq` with shape `(B,N)`, optional integer `msa` `(B,M,N)`, and
boolean masks on matching axes. At this version the MSA width must equal the
sequence width even though older README examples imply otherwise. Ensure all
tensors share a device. For coordinate outputs, route to the structure
reference; for atom/mask and metric layouts, route to utilities.

## README option is rejected

Treat the installed signature and the owning API reference as authoritative.
Options such as `atoms`, `structure_module_type`, `predict_real_value_distances`,
several sparse/linear/convolutional flags, and some template names are not
verified constructor arguments at this snapshot. Remove them or use a package
version whose source actually defines them; do not suppress the error by
silently changing the requested workflow.

## Pretrained model or embedding wrapper fails

Wrapper construction may use `torch.hub`, Hugging Face, network access,
model caches, tokenizers, or Apex/fused operations. Confirm the model source,
cache policy, disk budget, and backend before constructing it. If those are not
available, use local `seq_embed`/`msa_embed` representations through the
`embeddings` route and keep the model-download limitation explicit.

## OOM or unexpectedly slow execution

Attention and pairwise tensors scale steeply with sequence length and MSA
rows. Start with the bundled CPU smoke helpers and small dimensions; use
`model.eval()` and `torch.no_grad()` for inference. Do not infer scientific
quality from a tiny untrained run.
