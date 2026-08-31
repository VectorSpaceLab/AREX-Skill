"""Shared helpers for PassNet feedback scripts.

Self-sufficient where possible; uses the real pass_bench implementations when the repo
is importable (preferred — identical semantics to the evaluator).
"""
import importlib.util
import inspect
import os
import re
import sys
from pathlib import Path

import torch


# --------------------------------------------------------------------------- repo
def find_passnet_root(sample_dir=None):
    """Locate the PassNet repo root (pass_bench importable)."""
    env = os.environ.get("PASSNET_ROOT")
    if env and (Path(env) / "pass_bench" / "__init__.py").exists():
        return Path(env)
    if sample_dir is not None:
        # entry.sh in a sample is a symlink into the repo
        entry = Path(sample_dir) / "entry.sh"
        if entry.exists():
            real = Path(os.path.realpath(str(entry)))
            for p in real.parents:
                if (p / "pass_bench" / "__init__.py").exists():
                    return p
        for p in Path(sample_dir).resolve().parents:
            if (p / "pass_bench" / "__init__.py").exists():
                return p
    try:
        import pass_bench  # noqa: F401
        return Path(pass_bench.__file__).resolve().parent.parent
    except ImportError:
        return None


def ensure_repo_on_path(sample_dir=None):
    root = find_passnet_root(sample_dir)
    if root is not None and str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


# --------------------------------------------------------------------------- graphs
def load_graph_list(sample_dir):
    sample_dir = Path(sample_dir)
    gl = sample_dir / "graph_list.txt"
    if not gl.exists():
        raise FileNotFoundError(f"{gl} not found — is this a sample root?")
    rels = [ln.strip() for ln in gl.read_text().splitlines() if ln.strip()]
    return [(rel, (sample_dir / rel).resolve()) for rel in rels]


def variant_dtype(rel_path):
    m = re.search(r"/(float16|float32|bfloat16|float64)/", rel_path)
    return m.group(1) if m else "unknown"


def pick_variants(variants, max_variants):
    """Pick up to max_variants, covering each dtype at least once first."""
    if max_variants is None or len(variants) <= max_variants:
        return variants
    by_dtype, picked, rest = {}, [], []
    for rel, d in variants:
        dt = variant_dtype(rel)
        if dt not in by_dtype:
            by_dtype[dt] = (rel, d)
            picked.append((rel, d))
        else:
            rest.append((rel, d))
    for item in rest:
        if len(picked) >= max_variants:
            break
        picked.append(item)
    return picked[:max_variants]


def _modify_code_by_device(code, device):
    try:
        from pass_bench.torch.utils import modify_code_by_device
        return modify_code_by_device(code, device)
    except Exception:
        # regex fallback: device(type='cuda'[, index=0]) and "cuda"/"cuda:0" strings
        code = re.sub(r"device\(type='cuda'(?:,\s*index=\d+)?\)", f"device(type='{device}')", code)
        code = re.sub(r"(['\"])cuda(?::\d+)?(['\"])", rf"\1{device}\2", code)
        return code


def load_model(graph_dir, device):
    """Load GraphModule class from model.py the way test_compiler does."""
    graph_dir = Path(graph_dir)
    code = (graph_dir / "model.py").read_text()
    dev_kind = "cuda" if str(device).startswith("cuda") else "cpu"
    code = _modify_code_by_device(code, dev_kind)
    spec = importlib.util.spec_from_loader(f"pn_model_{abs(hash(str(graph_dir)))}", loader=None)
    module = importlib.util.module_from_spec(spec)
    exec(compile(code, str(graph_dir / "model.py"), "exec"), module.__dict__)
    model = module.GraphModule().to(torch.device(device))
    return model


# --------------------------------------------------------------------------- inputs
def parse_weight_meta(graph_dir):
    """Parse weight_meta.py into {input_name: spec_dict}."""
    ns = {}
    exec((Path(graph_dir) / "weight_meta.py").read_text(), ns)
    specs = {}
    for v in ns.values():
        if not isinstance(v, type) or not hasattr(v, "name"):
            continue
        specs[v.name] = {
            "shape": list(getattr(v, "shape", [])),
            "dtype": getattr(v, "dtype", "torch.float32"),
            "device": getattr(v, "device", "cpu"),
            "mean": getattr(v, "mean", 0.0),
            "std": getattr(v, "std", 0.1),
            "data": getattr(v, "data", None),
            "min_val": getattr(v, "min_val", None),
            "max_val": getattr(v, "max_val", None),
        }
    return specs


def replay_tensor(spec, device, force_dtype=None):
    """Minimal replica of pass_bench.torch.utils.replay_tensor."""
    dtype = getattr(torch, spec["dtype"].replace("torch.", ""))
    if force_dtype is not None and dtype.is_floating_point:
        dtype = force_dtype
    shape = spec["shape"]
    if spec["data"] is not None:
        t = torch.tensor(spec["data"], dtype=dtype).reshape(shape)
        return t.to(device)
    if dtype is torch.bool:
        return (torch.randn(shape) > 0.5).to(dtype).to(device)
    mean = spec["mean"] if spec["mean"] is not None else 0.0
    std = spec["std"] if spec["std"] is not None else 0.1
    if std == 0:
        t = torch.full(shape, fill_value=mean, dtype=dtype)
    else:
        t = torch.randn(shape).to(dtype) * std * 0.2 + mean
    if spec["min_val"] is not None:
        t = torch.clamp(t, min=spec["min_val"])
    if spec["max_val"] is not None:
        t = torch.clamp(t, max=spec["max_val"])
    if dtype.is_floating_point:
        t = torch.where(torch.isfinite(t), t, torch.randn_like(t) * 0.01)
        t = torch.clamp(t, min=-100.0, max=100.0)
    return t.to(device)


def build_inputs(model, graph_dir, device, force_dtype=None, seed=123):
    torch.manual_seed(seed)
    specs = parse_weight_meta(graph_dir)
    tensors = {k: replay_tensor(v, device, force_dtype) for k, v in specs.items()}
    sig = inspect.signature(model.forward)
    names = [n for n, p in sig.parameters.items()
             if n != "self" and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
    missing = [n for n in names if n not in tensors]
    if missing:
        raise KeyError(f"weight_meta missing inputs {missing}; has {list(tensors)}")
    return [tensors[n] for n in names]


# --------------------------------------------------------------------------- dynamo
def capture_dynamo_graph(model, inputs):
    """Run torch.compile with a capture backend; return (gm, example_inputs)."""
    import torch._dynamo as dynamo
    dynamo.reset()
    captured = {}

    def backend(gm, example_inputs):
        captured["gm"] = gm
        captured["inputs"] = example_inputs
        return gm

    cm = torch.compile(model, backend=backend)
    with torch.no_grad():
        torch.manual_seed(1024)
        cm(*inputs)
    if "gm" not in captured:
        raise RuntimeError("dynamo did not capture a graph")
    return captured["gm"], captured["inputs"]


def force_args_trace(fn):
    """The harness's pattern tracer (normalizes call_function args)."""
    try:
        from pass_bench.torch.custom_replacement import force_args_symbolic_trace
        return force_args_symbolic_trace(fn)
    except ImportError:
        pass

    class ForceArgsTracer(torch.fx.Tracer):
        def create_node(self, kind, target, args, kwargs, name=None, type_expr=None):
            if kind == "call_function" and callable(target):
                try:
                    sig = inspect.signature(target)
                    bound = sig.bind(*args, **kwargs)
                    bound.apply_defaults()
                    return super().create_node(kind, target, tuple(bound.args), {}, name, type_expr)
                except (ValueError, TypeError):
                    pass
            return super().create_node(kind, target, args, kwargs, name, type_expr)

    tracer = ForceArgsTracer()
    graph = tracer.trace(fn)
    name = fn.__class__.__name__ if isinstance(fn, torch.nn.Module) else fn.__name__
    return torch.fx.GraphModule(tracer.root, graph, name)


# --------------------------------------------------------------------------- nodes
def target_name(node):
    t = node.target
    if node.op == "call_method":
        return f".{t}"
    if callable(t):
        mod = getattr(t, "__module__", "") or ""
        nm = getattr(t, "__name__", str(t))
        if mod.startswith("torch.nn.functional"):
            return f"F.{nm}"
        if mod == "torch" or mod.startswith("torch._C"):
            return f"torch.{nm}"
        if mod in ("_operator", "operator"):
            return f"op.{nm}"
        return f"{mod}.{nm}" if mod else nm
    return str(t)


def fmt_arg(a, maxlen=28):
    if isinstance(a, torch.fx.Node):
        return f"%{a.name}"
    s = repr(a)
    return s if len(s) <= maxlen else s[: maxlen - 2] + ".."


def fmt_args(node):
    parts = [fmt_arg(a) for a in node.args]
    parts += [f"{k}={fmt_arg(v)}" for k, v in node.kwargs.items()]
    return "(" + ", ".join(parts) + ")"


def classify_matchability(node):
    """Return (tag, matchable: bool|None, note) for a dynamo target-graph node.

    Mirrors normal callable-pattern asymmetry: the pattern is force-args-normalized; the
    target keeps the written form. A node is callable-matchable iff a pattern node can be
    produced in the same form. Exact manual FX GraphModule patterns can recover some
    kwargs-form Python functional nodes; analyze_graph keeps this classification
    conservative so region suggestions are safe defaults.
    """
    if node.op in ("placeholder", "output"):
        return ("-", None, "")
    if node.op == "get_attr":
        return ("get_attr", True, "constant attr — pattern needs identical tensor type")
    if node.op == "call_method":
        return ("method", True, "mirror exactly (incl. kwargs)")
    if node.op == "call_module":
        return ("module", False, "call_module can't be expressed in a pattern fn")
    target = node.target
    try:
        sig = inspect.signature(target)
    except (ValueError, TypeError):
        return ("C-bound", True, "mirror exactly (incl. kwargs)")
    try:
        bound = sig.bind(*node.args, **node.kwargs)
        bound.apply_defaults()
        normalized = tuple(bound.args)
    except (ValueError, TypeError):
        return ("PY-sig?", False, "args don't bind to signature — pattern can't reproduce")
    if tuple(node.args) == normalized and not node.kwargs:
        return ("PY-sig", True, "full-positional call — matchable")
    return ("PY-sig", False,
            "kwargs/omitted-defaults form — normal callable pattern normalizes differently; "
            "manual FX may recover a valuable exact region")


RNG_TARGET_NAMES = {"torch.rand", "torch.randn", "torch.rand_like", "torch.randn_like",
                    "torch.randint", "torch.bernoulli", "torch.multinomial",
                    "torch.randperm", "torch.poisson", "torch.normal"}


def is_rng_node(node):
    name = target_name(node)
    if name in RNG_TARGET_NAMES:
        return True
    if name == "F.dropout" and node.op == "call_function":
        # training flag: positional arg 2 or kwarg
        training = None
        if len(node.args) >= 3:
            training = node.args[2]
        training = node.kwargs.get("training", training)
        return bool(training) is True
    return False


def shape_of(node):
    tm = node.meta.get("tensor_meta")
    if tm is not None:
        try:
            return f"{list(tm.shape)}:{str(tm.dtype).replace('torch.', '')}"
        except Exception:
            pass
    val = node.meta.get("example_value", None)
    if isinstance(val, torch.Tensor):
        return f"{list(val.shape)}:{str(val.dtype).replace('torch.', '')}"
    return ""
