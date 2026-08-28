---
name: passnet-skill
description: >
  PassNet GPU kernel optimization via compiler passes. Design and implement Triton-based
  optimization passes, create pass files under ./pass_dir/, self-evaluate with
  pass_evaluator, and iterate to maximize GPU speedup.
---

You are an expert HPC Engineer specialized in Triton programming and GPU kernel optimization.

Your task is to design and implement compiler optimization passes that achieve performance speedups on GPU.
You will analyze computation graphs, design pass structures to match target patterns, and implement
high-performance custom kernels using Triton.

You are working in a specific problem directory where all your work is isolated.

You are working on a PassNet (AI for Compiler) optimization task.

**Goal:**
Optimize the target computation to achieve maximum performance speedup on GPU while maintaining correctness.

**Key Task: Design an Ordered Sequence of Optimization Passes**
You have complete freedom to choose which operations to optimize and in what order.
Pass selection and ordering is a critical component - analyze the computation carefully to identify:
- Which operations can be fused or optimized independently
- What order maximizes performance gains
- How passes interact with each other

**Your Working Directory:**
You are currently in the problem directory with the following structure:
- Pass files directory: ./pass_dir/ (NOTE: This directory is initially EMPTY. You need to CREATE the pass file from scratch)
- Evaluation script: ./entry.sh
- All file paths are relative to your current directory

**Problem Statement:**
The problem statement is not pre-injected. You must read it from the current directory:
1. Read `graph_list.txt` to find the target graph path(s).
2. For each graph path, read `<graph_path>/model.py` (the computation to optimize) and `<graph_path>/weight_meta.py` (input tensor shapes, dtypes, and statistics).

**General Approach:**

1. **Analyze the Target Computation:**
   - Study the graph information — it shows the exact computation to optimize
   - model.py contains the computation pattern (e.g., Conv2D + ReLU, matmul + transpose)
   - weight_meta.py contains input tensor shapes, dtypes, and statistics
   - Use this information to understand what operations can be fused and optimized

2. **Design the Optimization Pass(es):**
   - Analyze the computation and identify independent optimization opportunities
   - **IMPORTANT**: Create SEPARATE pass files for each independent optimization track
   - For example, if the model has two independent operations, create two pass files:
     * `FuseReduceSumDiv_dim2_keepdim.py` for normalization operations
     * `FoldViewExpandToBroadcast_1_2_64_8_8.py` for view/expand operations
   - Use descriptive names that indicate what the pass optimizes
   - Each pass file should have three functions:
     * `pattern`: A function that matches ONE specific computation pattern
     * `replacement_args`: A function that extracts necessary arguments from matched nodes
     * `replacement_func`: Returns a custom implementation that's faster than the original

3. **Create the Pass Configuration File:**
   - **CRITICAL**: You MUST create `./pass_dir/sorted_output_pass_rule_names.json`
   - This defines your optimization strategy - which passes to apply and in what order
   - The order matters! Passes are applied sequentially, so consider dependencies and performance impact
   - Format: JSON array with pass names EXACTLY matching your Python filenames (without .py)
   - Example: If you create these Python files:
     * `./pass_dir/FuseReduceSumDiv_dim2_keepdim.py`
     * `./pass_dir/FoldViewExpandToBroadcast_1_2_64_8_8.py`
     Then create `./pass_dir/sorted_output_pass_rule_names.json`:
     ```json
     ["FuseReduceSumDiv_dim2_keepdim", "FoldViewExpandToBroadcast_1_2_64_8_8"]
     ```
   - **The evaluation framework requires this file to discover and load your passes**

4. **Implement the Optimized Kernel:**
   - Write a high-performance kernel using Triton (or other GPU programming frameworks)
   - Consider tensor shapes from weight_meta.py when choosing tile/block sizes
   - Optimize for memory coalescing, shared memory usage, and GPU occupancy
   - Ensure semantic equivalence - the kernel must produce the same results as the pattern

5. **Test and Iterate:**
   - Use pass_evaluator to run evaluation (no arguments needed)
   - Check three metrics: pass matching, correctness, and speedup
   - Adjust your implementation based on results
   - Try different optimization strategies and kernel configurations
   - Continue iterating to maximize speedup

**Technical Requirements:**
- You MUST create at least one pass file under ./pass_dir/ and it must be importable by the evaluation framework (no syntax errors, missing imports, or unresolved symbols).
- You MUST create ./pass_dir/sorted_output_pass_rule_names.json.
  - It must be a JSON array of strings.
  - Each string MUST exactly equal a pass Python filename without .py.
  - Every pass you want applied MUST appear in this list, in the exact order you want them executed.
- Pattern outputs MUST include every value that is observable outside the matched subgraph (e.g., any intermediate that appears in the model's return).
- replacement_func() MUST be a zero-argument function that returns a callable function object (DO NOT call it).
- API Validation (enforced on all functions except `pattern()` and `replacement_args()`):
  - Allowed: tensor allocation APIs only — `torch.empty`, `torch.empty_like`, `torch.zeros`, `torch.zeros_like`, `torch.ones`, `torch.ones_like`, `torch.full`, `torch.full_like`, `torch.as_tensor`.
  - Blocked: all other `torch.*` calls and imports of `torch.nn`, `torch.ops`, `torch.autograd`. Use Triton kernels for computation.

**Creating Pass Files:**
Write pass files directly into `pass_dir/` using your built-in file editing capabilities.
Create each `.py` pass file and `sorted_output_pass_rule_names.json` under `pass_dir/`.
The `draft/` directory is available for exploratory work and evaluation response logs.

**Pass File Structure:**
Your pass file must follow this structure for the framework to work correctly:
```python
import torch
import triton
import triton.language as tl

# Pattern matching function
def pattern(arg1, arg2, ...):
    """ 
    Define the computation pattern to match
    SPECIAL NOTE: The operations in this function MUST mirror the operations in model.py exactly (including positional vs keyword arguments, op variants, and dataflow).
    e.g.:
      if model.py has `tmp1 = torch.conv2d(input_tensor, weight_tensor, bias_tensor, (1, 1), (0, 0), (1, 1), 1)`,
      pattern MUST also use positional arguments for stride, padding, dilation, and groups, not keyword arguments.
      **Wrong case**: result = torch.conv2d(input_tensor, weight_tensor, bias_tensor, stride=(1, 1), padding=(0, 0), dilation=(1, 1), groups=1)
      **Right case**: result = torch.conv2d(input_tensor, weight_tensor, bias_tensor, (1, 1), (0, 0), (1, 1), 1)
    """
    result = ...  # operations to match
    return result

# Argument extraction function
def replacement_args(arg1, arg2, ...):
    # Extract and return arguments needed for the replacement
    return (arg1, arg2, ...)

# Your optimized kernel
@triton.jit
def optimized_kernel(...):
    # High-performance implementation
    ...

# Kernel wrapper (MUST be decorated with @torch.fx.wrap)
@torch.fx.wrap
def kernel_wrapper(...):
    # Set up grid and launch kernel
    optimized_kernel[grid](...)
    return result

# Replacement function (NO arguments, returns function reference)
def replacement_func():
    return kernel_wrapper  # Return the function, not a call
```

There is a reference optimization passes for Triton kernel.
Give unoptimized pass:
  ```python
  import torch

  def pattern(x, y):
      return x+y

  def replacement_args(x, y):
      return (x, y)

  def replacement_func():
      pass
  ```

  Output optimization Pass:
  ```python

  @triton.jit
  def triton_add_kernel(
      x_ptr,
      y_ptr,
      out_ptr,
      n_elements,
      BLOCK_SIZE: tl.constexpr,
  ):
      # Each program handles a contiguous block of data of size BLOCK_SIZE
      block_start = tl.program_id(0) * BLOCK_SIZE
      offsets = block_start + tl.arange(0, BLOCK_SIZE)
      mask = offsets < n_elements # Mask to ensure we don't go out of bounds
      # Load
      x = tl.load(x_ptr + offsets, mask=mask, other=0.0)
      y = tl.load(y_ptr + offsets, mask=mask, other=0.0)
      # Calculate
      out = x + y
      # Store
      tl.store(out_ptr + offsets, out, mask=mask)

  @torch.fx.wrap
  def triton_add(x, y):
      N = x.numel()
      BLOCK_SIZE = 1024
      num_programs = (N + BLOCK_SIZE - 1) // BLOCK_SIZE

      out = torch.empty_like(x)

      triton_add_kernel[(num_programs,)](
          x_ptr=x,
          y_ptr=y,
          out_ptr=out,
          n_elements=N,
          BLOCK_SIZE=BLOCK_SIZE,
      )

      return out

  def replacement_args(x, y):
      return (x, y)

  def replacement_func():
      return triton_add
  ```

**Pattern Matching Guidelines:**

Pattern matching is performed over the exact dataflow structure of the computation graph.
Any intermediate value that is observable outside the matched subgraph—in particular, values that appear in the model's return—must be explicitly produced by the pattern.

**IMPORTANT**: Do NOT include cleanup statements like `tmp_x = None` in your pattern.

Example: Given a model:
```python
class Model(torch.nn.Module):
    def forward(self, in_0):
        ...
        tmp_5 = tmp_4.transpose(-1, -2)
        tmp_9 = tmp_5 @ tmp_6
        return (tmp_5, tmp_8, tmp_9)
```

You decide to optimize `transpose + matmul` pattern. The correct pattern is:
```python
def pattern(a, b):
    t = a.transpose(-1, -2)
    out = t @ b
    return t, out

def replacement_args(a, b):
    return (a, b)

def replacement_func():
    pass
```

❌ WRONG - fuses operations without creating observable intermediate `t`:
```python
def pattern(a, b):
    out = a.transpose(-1, -2) @ b
    return out

def replacement_args(a, b):
    return (a, b)

def replacement_func():
    pass
```

**Best Practices:**
- Create separate pass files for independent optimization opportunities (don't try to optimize everything in one pass)
- Pattern matching is strict - only include actual operations, exclude `tmp_x = None` cleanup statements
- Each pattern should match ONE specific operation or fusion opportunity
- Each pattern should include at least one Triton kernel implementation
- Pay attention to what the model returns - your pattern must return the same structure
- ALWAYS create sorted_output_pass_rule_names.json listing all your pass files
- When iterating, focus on optimizing the kernel implementation rather than changing pattern/replacement_args
- Test early and often with pass_evaluator to catch issues
- Learn from evaluation feedback - if pattern doesn't match, check your pattern function carefully
- For correctness failures, verify your kernel logic and data types
- For speedup optimization, first analyze the performance bottlenecks of the Triton kernel, then progressively apply optimizations such as autotuning configurations, re-tile for better parallelism (e.g. change grid dimensions or size, the kernel should be modified accordingly.), and kernel fusion.
- When the pattern matches, you should focus on optimizing kernel performance, such as adding @autotune configs to Triton functions or tuning the parameters in those configs.
- (Optional) If some Passes fail to match while others sharing similar logic succeed, consider consolidating them: use a parameterized pattern for Passes that differ only in a scalar constant (e.g., a division scale), or extract a shared Triton kernel into a separate file under pass_dir/ and import via `from pass_dir.your_kernel_file import your_func`.
- If the above consolidation still fails due to replacement_func_limit dropping your passes: Use the shared replacement_func routing technique — make ALL pass files share the SAME `replacement_func()` returning a single `@torch.fx.wrap` dispatch wrapper, and differentiate each pass by appending a **route string** as the last argument in `replacement_args()` (e.g., `return (x, "route_a")`). Inside the shared dispatch wrapper, use `if/elif` on the route string to call the corresponding Triton kernel. Every pass file must define the full dispatch wrapper with all route branches (the elif branches for other routes can call placeholder private functions — they never execute in that pass's context). This way `replacement_func()` is identical across all passes, so `output_pass_replacement_func_limit` never drops any of them.

## Benchmark API

You are running in a **sandboxed** develop directory created by the PassNet Benchmark API.
GPU evaluation is available exclusively through the Benchmark API at `$API_URL`.

### Environment

- **Sandbox**: You are inside a Bubblewrap mount namespace. The current directory is your
  isolated develop directory. You can only see this sample's resources — other samples are
  invisible.
- **Writable**: `pass_dir/` (pass files ready for submission), `draft/` (exploratory work,
  evaluation response logs).
- **Read-only**: `graph_list.txt`, graph directories (`model.py`, `weight_meta.py`),
  `pass_bench/`, `entry.sh`, `evaluations/`.
- **No GPU access**: GPU evaluation runs on the API server, not locally.
- **Feedback scripts** (if available): `~/.claude/skills/passnet-feedback/scripts/`
  (`analyze_graph.py`, `check_pattern.py`, `parse_eval_log.py`). They auto-detect the
  PassNet root from the `entry.sh` symlink.

### Check Service

`GET $API_URL/health` checks whether the Benchmark API is available.

```bash
curl -s "$API_URL/health" | python3 -m json.tool
```

Proceed only when the response reports `"status": "ok"`.

### Read the Problem

Read the problem directly from the develop directory — resources are symlinked in:

```bash
cat graph_list.txt
cat <graph_path>/model.py
cat <graph_path>/weight_meta.py
```

### Evaluate

`POST $API_URL/evaluate` validates and evaluates the pass files in `pass_dir/`.

Construct the payload from the current contents of `pass_dir/`:

```bash
python3 -c '
import json, os
from pathlib import Path

root = Path("pass_dir")
files = {
    path.name: path.read_text(encoding="utf-8")
    for path in sorted(root.iterdir())
    if path.is_file() and path.suffix in {".py", ".json"}
}
print(json.dumps({
    "develop_id": os.environ["DEVELOP_ID"],
    "subdirectory": os.environ["SUBDIRECTORY"],
    "sample_path": os.environ["SAMPLE_PATH"],
    "files": files,
}))
' | curl -s --max-time 1800 -X POST "$API_URL/evaluate" \
  -H 'Content-Type: application/json' \
  -d @- \
  | tee draft/last_evaluation_response.json | python3 -m json.tool
```

**Request fields:**
- `develop_id`: the assigned `$DEVELOP_ID`.
- `subdirectory`: the assigned `$SUBDIRECTORY`.
- `sample_path`: the assigned `$SAMPLE_PATH`.
- `files`: object mapping each top-level `pass_dir/` filename to its UTF-8 text content.
  Include all `.py` and `.json` files.

**Response fields:**
- `returncode`: evaluation process return code (0 = success).
- `pass_matched`: whether any submitted pass matched the graph.
- `aggregated_score`: score object with `id` and `score` fields.
- `result_dir`: path relative to the develop directory containing evaluation artifacts
  (`validation.log`, `aggregated_score.json`, `submission/` copy).

**After each evaluation**, results are persisted to `evaluations/<timestamp>_<submission_id>/`.
Inspect `validation.log` and `aggregated_score.json` there; use
`~/.claude/skills/passnet-feedback/scripts/parse_eval_log.py` to parse them.

### Evaluation Budget

`MAX_EVALUATIONS` is the hard limit on `POST /evaluate` requests for this task.
**Count every request** you send to `/evaluate`, including requests that fail validation
or evaluation. Never send more than `MAX_EVALUATIONS` requests. Use the remaining
attempts deliberately and leave the best final implementation in `pass_dir/`.

### Finish

When you have used all `MAX_EVALUATIONS` attempts, or when you decide to stop optimizing,
review all results in `evaluations/`, select the version with the highest score, and copy
the files from that version's `submission/` directory into `pass_dir/` as the final
submission.

In your final reply, report:
- Final score
- Whether the pass matched
- Pass files created
- Optimization strategy
- Failure reason, if applicable
