#!/usr/bin/env python3
"""Self-contained DARTS genotype catalog, validator, and DOT emitter.

The helper is stdlib-only. It lists built-in CNN/RNN genotypes, prints a
schema-aware summary, and emits DOT text without importing the original repo or
calling Graphviz.
"""

import argparse
import ast
import json
import os
import sys
from collections import OrderedDict, namedtuple

CNNGenotype = namedtuple("Genotype", "normal normal_concat reduce reduce_concat")
RNNGenotype = namedtuple("Genotype", "recurrent concat")

CNN_SEARCH_PRIMITIVES = [
    "none",
    "max_pool_3x3",
    "avg_pool_3x3",
    "skip_connect",
    "sep_conv_3x3",
    "sep_conv_5x5",
    "dil_conv_3x3",
    "dil_conv_5x5",
]

CNN_EVAL_OPS = CNN_SEARCH_PRIMITIVES + [
    "sep_conv_7x7",
    "conv_7x1_1x7",
]

RNN_PRIMITIVES = [
    "none",
    "tanh",
    "relu",
    "sigmoid",
    "identity",
]

CNN_GENOTYPES = OrderedDict([
    ("NASNet", CNNGenotype(
        normal=[
            ("sep_conv_5x5", 1),
            ("sep_conv_3x3", 0),
            ("sep_conv_5x5", 0),
            ("sep_conv_3x3", 0),
            ("avg_pool_3x3", 1),
            ("skip_connect", 0),
            ("avg_pool_3x3", 0),
            ("avg_pool_3x3", 0),
            ("sep_conv_3x3", 1),
            ("skip_connect", 1),
        ],
        normal_concat=[2, 3, 4, 5, 6],
        reduce=[
            ("sep_conv_5x5", 1),
            ("sep_conv_7x7", 0),
            ("max_pool_3x3", 1),
            ("sep_conv_7x7", 0),
            ("avg_pool_3x3", 1),
            ("sep_conv_5x5", 0),
            ("skip_connect", 3),
            ("avg_pool_3x3", 2),
            ("sep_conv_3x3", 2),
            ("max_pool_3x3", 1),
        ],
        reduce_concat=[4, 5, 6],
    )),
    ("AmoebaNet", CNNGenotype(
        normal=[
            ("avg_pool_3x3", 0),
            ("max_pool_3x3", 1),
            ("sep_conv_3x3", 0),
            ("sep_conv_5x5", 2),
            ("sep_conv_3x3", 0),
            ("avg_pool_3x3", 3),
            ("sep_conv_3x3", 1),
            ("skip_connect", 1),
            ("skip_connect", 0),
            ("avg_pool_3x3", 1),
        ],
        normal_concat=[4, 5, 6],
        reduce=[
            ("avg_pool_3x3", 0),
            ("sep_conv_3x3", 1),
            ("max_pool_3x3", 0),
            ("sep_conv_7x7", 2),
            ("sep_conv_7x7", 0),
            ("avg_pool_3x3", 1),
            ("max_pool_3x3", 0),
            ("max_pool_3x3", 1),
            ("conv_7x1_1x7", 0),
            ("sep_conv_3x3", 5),
        ],
        reduce_concat=[3, 4, 6],
    )),
    ("DARTS_V1", CNNGenotype(
        normal=[
            ("sep_conv_3x3", 1), ("sep_conv_3x3", 0),
            ("skip_connect", 0), ("sep_conv_3x3", 1),
            ("skip_connect", 0), ("sep_conv_3x3", 1),
            ("sep_conv_3x3", 0), ("skip_connect", 2),
        ],
        normal_concat=[2, 3, 4, 5],
        reduce=[
            ("max_pool_3x3", 0), ("max_pool_3x3", 1),
            ("skip_connect", 2), ("max_pool_3x3", 0),
            ("max_pool_3x3", 0), ("skip_connect", 2),
            ("skip_connect", 2), ("avg_pool_3x3", 0),
        ],
        reduce_concat=[2, 3, 4, 5],
    )),
    ("DARTS_V2", CNNGenotype(
        normal=[
            ("sep_conv_3x3", 0), ("sep_conv_3x3", 1),
            ("sep_conv_3x3", 0), ("sep_conv_3x3", 1),
            ("sep_conv_3x3", 1), ("skip_connect", 0),
            ("skip_connect", 0), ("dil_conv_3x3", 2),
        ],
        normal_concat=[2, 3, 4, 5],
        reduce=[
            ("max_pool_3x3", 0), ("max_pool_3x3", 1),
            ("skip_connect", 2), ("max_pool_3x3", 1),
            ("max_pool_3x3", 0), ("skip_connect", 2),
            ("skip_connect", 2), ("max_pool_3x3", 1),
        ],
        reduce_concat=[2, 3, 4, 5],
    )),
])
CNN_GENOTYPES["DARTS"] = CNN_GENOTYPES["DARTS_V2"]

RNN_GENOTYPES = OrderedDict([
    ("ENAS", RNNGenotype(
        recurrent=[
            ("tanh", 0),
            ("tanh", 1),
            ("relu", 1),
            ("tanh", 3),
            ("tanh", 3),
            ("relu", 3),
            ("relu", 4),
            ("relu", 7),
            ("relu", 8),
            ("relu", 8),
            ("relu", 8),
        ],
        concat=[2, 5, 6, 9, 10, 11],
    )),
    ("DARTS_V1", RNNGenotype(
        recurrent=[
            ("relu", 0), ("relu", 1), ("tanh", 2), ("relu", 3),
            ("relu", 4), ("identity", 1), ("relu", 5), ("relu", 1),
        ],
        concat=list(range(1, 9)),
    )),
    ("DARTS_V2", RNNGenotype(
        recurrent=[
            ("sigmoid", 0), ("relu", 1), ("relu", 1), ("identity", 1),
            ("tanh", 2), ("sigmoid", 5), ("tanh", 3), ("relu", 5),
        ],
        concat=list(range(1, 9)),
    )),
])
RNN_GENOTYPES["DARTS"] = RNN_GENOTYPES["DARTS_V2"]

CATALOG = OrderedDict([
    ("cnn", CNN_GENOTYPES),
    ("rnn", RNN_GENOTYPES),
])


def fail(message):
    sys.stderr.write("error: {}\n".format(message))
    raise SystemExit(1)


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def is_sequence(value):
    return isinstance(value, (list, tuple, range))


def as_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, range):
        return list(value)
    return value


def format_sequence(value):
    if is_sequence(value):
        return repr(list(value))
    return repr(value)


def sequence_len(value):
    if is_sequence(value):
        return len(value)
    return 0


def split_qualified_name(name):
    if not name:
        return None, None
    for sep in (":", "/"):
        if sep in name:
            schema, short = name.split(sep, 1)
            schema = schema.strip().lower()
            short = short.strip()
            if schema in CATALOG and short:
                return schema, short
    return None, name


def infer_schema_from_spec(spec):
    keys = set(spec.keys())
    has_cnn = {"normal", "normal_concat", "reduce", "reduce_concat"}.issubset(keys)
    has_rnn = {"recurrent", "concat"}.issubset(keys)
    if has_cnn and not has_rnn:
        return "cnn"
    if has_rnn and not has_cnn:
        return "rnn"
    if has_cnn and has_rnn:
        fail("custom spec contains both CNN and RNN fields; pass one schema at a time")
    fail("custom spec does not match a CNN or RNN genotype schema")


def _literal_or_call(node):
    if isinstance(node, ast.Constant):
        return node.value
    node_kind = type(node).__name__
    if node_kind == "NameConstant":
        return node.value
    if node_kind == "Num":
        return node.n
    if node_kind == "Str":
        return node.s
    if isinstance(node, ast.List):
        return [_literal_or_call(elt) for elt in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_literal_or_call(elt) for elt in node.elts)
    if isinstance(node, ast.Set):
        return set(_literal_or_call(elt) for elt in node.elts)
    if isinstance(node, ast.Dict):
        return {
            _literal_or_call(key): _literal_or_call(value)
            for key, value in zip(node.keys, node.values)
        }
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        value = _literal_or_call(node.operand)
        if not isinstance(value, (int, float)):
            fail("unsupported unary expression in custom spec")
        return -value
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "range":
            if node.keywords:
                fail("range() in custom specs cannot use keyword arguments")
            args = [_literal_or_call(arg) for arg in node.args]
            if len(args) == 1:
                return list(range(args[0]))
            if len(args) == 2:
                return list(range(args[0], args[1]))
            if len(args) == 3:
                return list(range(args[0], args[1], args[2]))
            fail("range() in custom specs must have 1-3 arguments")
        if isinstance(node.func, ast.Name) and node.func.id == "Genotype":
            if node.args:
                fail("Genotype() in custom specs must use keyword arguments only")
            data = {}
            for keyword in node.keywords:
                if keyword.arg is None:
                    fail("Genotype() in custom specs cannot use **kwargs expansion")
                data[keyword.arg] = _literal_or_call(keyword.value)
            return data
        fail("unsupported function call in custom spec: {}".format(getattr(node.func, "id", type(node.func).__name__)))
    if isinstance(node, ast.Name):
        if node.id == "True":
            return True
        if node.id == "False":
            return False
        if node.id == "None":
            return None
    fail("unsupported value in custom spec: {}".format(type(node).__name__))


def load_spec(path):
    if path == "-":
        raw = sys.stdin.read()
    else:
        with open(path, "r") as handle:
            raw = handle.read()
    raw = raw.strip()
    if not raw:
        fail("custom spec is empty")
    try:
        data = json.loads(raw)
    except ValueError:
        try:
            parsed = ast.parse(raw, mode="eval")
            data = _literal_or_call(parsed.body)
        except (SyntaxError, ValueError) as exc:
            fail("custom spec is neither JSON nor a supported genotype expression: {}".format(exc))
    if not isinstance(data, dict):
        fail("custom spec must evaluate to a mapping/dict")
    return data


def coerce_cnn(spec):
    required = ["normal", "normal_concat", "reduce", "reduce_concat"]
    missing = [key for key in required if key not in spec]
    if missing:
        fail("CNN spec is missing fields: {}".format(", ".join(missing)))
    return CNNGenotype(
        normal=as_list(spec["normal"]),
        normal_concat=as_list(spec["normal_concat"]),
        reduce=as_list(spec["reduce"]),
        reduce_concat=as_list(spec["reduce_concat"]),
    )


def coerce_rnn(spec):
    required = ["recurrent", "concat"]
    missing = [key for key in required if key not in spec]
    if missing:
        fail("RNN spec is missing fields: {}".format(", ".join(missing)))
    return RNNGenotype(
        recurrent=as_list(spec["recurrent"]),
        concat=as_list(spec["concat"]),
    )


def resolve_genotype(name, schema, spec_path=None):
    if spec_path:
        spec = load_spec(spec_path)
        inferred = infer_schema_from_spec(spec)
        if schema and schema != "auto" and schema != inferred:
            fail("custom spec looks like {}, but --schema {} was requested".format(inferred, schema))
        schema = inferred
        genotype = coerce_cnn(spec) if schema == "cnn" else coerce_rnn(spec)
        label = name or "custom"
        return schema, label, genotype

    if not name:
        fail("provide a built-in genotype name or --spec")

    qualified_schema, short_name = split_qualified_name(name)
    if qualified_schema:
        if schema and schema != "auto" and schema != qualified_schema:
            fail("qualified name uses schema {}, but --schema {} was requested".format(qualified_schema, schema))
        schema = qualified_schema
        name = short_name

    if not schema or schema == "auto":
        matches = [candidate for candidate, genotypes in CATALOG.items() if name in genotypes]
        if not matches:
            fail("unknown architecture name {!r}; run the list command".format(name))
        if len(matches) > 1:
            fail("architecture name {!r} is ambiguous across {}; pass --schema cnn/rnn or use cnn:{} / rnn:{}".format(
                name, ", ".join(matches), name, name))
        schema = matches[0]

    if schema not in CATALOG:
        fail("unknown schema {!r}".format(schema))
    if name not in CATALOG[schema]:
        fail("{} architecture {!r} is not bundled; run the list command".format(schema, name))
    return schema, name, CATALOG[schema][name]


def validate_cnn_cell(cell_name, pairs, errors, warnings):
    if not is_sequence(pairs):
        errors.append("{} is not a sequence".format(cell_name))
        return 0
    if len(pairs) == 0:
        errors.append("{} has no edges".format(cell_name))
        return 0
    if len(pairs) % 2 != 0:
        errors.append("{} has an odd number of edges; CNN steps require two edges each".format(cell_name))
    steps = len(pairs) // 2
    for pos, pair in enumerate(pairs):
        if not is_sequence(pair) or len(pair) != 2:
            errors.append("{} edge {} is not an (op, source_index) pair".format(cell_name, pos))
            continue
        op, source = pair[0], pair[1]
        step = pos // 2
        if op not in CNN_EVAL_OPS:
            errors.append("{} edge {} uses unsupported CNN op {!r}".format(cell_name, pos, op))
        if not is_int(source):
            errors.append("{} edge {} source index is not an integer: {!r}".format(cell_name, pos, source))
            continue
        max_source = step + 1
        if source < 0 or source > max_source:
            errors.append(
                "{} edge {} source index {} is out of range for step {}; valid range is 0..{}".format(
                    cell_name, pos, source, step, max_source))
    return steps


def validate_cnn_concat(name, concat, steps, errors, warnings):
    if not is_sequence(concat):
        errors.append("{} is not a sequence".format(name))
        return
    if len(concat) == 0:
        errors.append("{} is empty".format(name))
        return
    seen = set()
    for value in concat:
        if not is_int(value):
            errors.append("{} contains non-integer value {!r}".format(name, value))
            continue
        if value < 0 or value > steps + 1:
            errors.append("{} value {} is out of range; cell with {} steps has states 0..{}".format(
                name, value, steps, steps + 1))
        if value < 2:
            warnings.append("{} includes input state {}; canonical CNN DARTS cells usually concat intermediate states only".format(
                name, value))
        if value in seen:
            warnings.append("{} contains duplicate state {}".format(name, value))
        seen.add(value)


def validate_cnn(genotype):
    errors = []
    warnings = []
    normal_steps = validate_cnn_cell("normal", genotype.normal, errors, warnings)
    reduce_steps = validate_cnn_cell("reduce", genotype.reduce, errors, warnings)
    validate_cnn_concat("normal_concat", genotype.normal_concat, normal_steps, errors, warnings)
    validate_cnn_concat("reduce_concat", genotype.reduce_concat, reduce_steps, errors, warnings)
    if normal_steps and reduce_steps and normal_steps != reduce_steps:
        warnings.append("normal and reduce cells have different step counts")
    return errors, warnings


def validate_rnn(genotype):
    errors = []
    warnings = []
    recurrent = genotype.recurrent
    concat = genotype.concat
    if not is_sequence(recurrent):
        errors.append("recurrent is not a sequence")
        recurrent = []
    if len(recurrent) == 0:
        errors.append("recurrent has no edges")
    for step, pair in enumerate(recurrent):
        if not is_sequence(pair) or len(pair) != 2:
            errors.append("recurrent edge {} is not an (op, predecessor_index) pair".format(step))
            continue
        op, predecessor = pair[0], pair[1]
        if op not in RNN_PRIMITIVES:
            errors.append("recurrent edge {} uses unsupported RNN op {!r}".format(step, op))
        if not is_int(predecessor):
            errors.append("recurrent edge {} predecessor is not an integer: {!r}".format(step, predecessor))
            continue
        if predecessor < 0 or predecessor > step:
            errors.append("recurrent edge {} predecessor {} is out of range; valid range is 0..{}".format(
                step, predecessor, step))
    if not is_sequence(concat):
        errors.append("concat is not a sequence")
        concat = []
    if len(concat) == 0:
        errors.append("concat is empty")
    seen = set()
    for value in concat:
        if not is_int(value):
            errors.append("concat contains non-integer value {!r}".format(value))
            continue
        if value < 0 or value > len(recurrent):
            errors.append("concat value {} is out of range; recurrent cell with {} steps has states 0..{}".format(
                value, len(recurrent), len(recurrent)))
        if value == 0:
            warnings.append("concat includes initial state 0; canonical DARTS recurrent cells usually use later states")
        if value in seen:
            warnings.append("concat contains duplicate state {}".format(value))
        seen.add(value)
    return errors, warnings


def validation_for(schema, genotype):
    if schema == "cnn":
        return validate_cnn(genotype)
    return validate_rnn(genotype)


def ensure_valid_for_dot(schema, genotype):
    errors, warnings = validation_for(schema, genotype)
    for warning in warnings:
        sys.stderr.write("warning: {}\n".format(warning))
    if errors:
        for error in errors:
            sys.stderr.write("error: {}\n".format(error))
        raise SystemExit(1)


def unique_ops(pairs):
    if not is_sequence(pairs):
        return []
    return sorted(set(pair[0] for pair in pairs if is_sequence(pair) and len(pair) == 2))


def format_pair_groups(pairs, edges_per_step):
    if not is_sequence(pairs):
        return ["    invalid edge list: {}".format(repr(pairs))]
    lines = []
    steps = len(pairs) // edges_per_step if edges_per_step else 0
    for step in range(steps):
        group = pairs[step * edges_per_step:(step + 1) * edges_per_step]
        edges = []
        for pair in group:
            if is_sequence(pair) and len(pair) == 2:
                op, source = pair[0], pair[1]
                edges.append("{}:{}".format(source, op))
            else:
                edges.append(repr(pair))
        lines.append("    step {} -> [{}]".format(step, ", ".join(edges)))
    return lines


def show_cnn(label, genotype, errors, warnings):
    print("name: {}".format(label))
    print("schema: cnn")
    print("normal_steps: {}".format(sequence_len(genotype.normal) // 2))
    print("normal_concat: {}".format(format_sequence(genotype.normal_concat)))
    print("normal_ops: {}".format(", ".join(unique_ops(genotype.normal))))
    for line in format_pair_groups(genotype.normal, 2):
        print(line)
    print("reduce_steps: {}".format(sequence_len(genotype.reduce) // 2))
    print("reduce_concat: {}".format(format_sequence(genotype.reduce_concat)))
    print("reduce_ops: {}".format(", ".join(unique_ops(genotype.reduce))))
    for line in format_pair_groups(genotype.reduce, 2):
        print(line)
    print_validation(errors, warnings)


def show_rnn(label, genotype, errors, warnings):
    print("name: {}".format(label))
    print("schema: rnn")
    print("recurrent_steps: {}".format(sequence_len(genotype.recurrent)))
    print("concat: {}".format(format_sequence(genotype.concat)))
    print("ops: {}".format(", ".join(unique_ops(genotype.recurrent))))
    for line in format_pair_groups(genotype.recurrent, 1):
        print(line)
    print_validation(errors, warnings)


def print_validation(errors, warnings):
    if errors:
        print("validation: errors")
        for error in errors:
            print("  error: {}".format(error))
    elif warnings:
        print("validation: ok with warnings")
    else:
        print("validation: ok")
    for warning in warnings:
        print("  warning: {}".format(warning))


def dot_quote(value):
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return '"{}"'.format(text)


def dot_node(lines, name, fillcolor):
    lines.append("  {} [fillcolor={}];".format(dot_quote(name), dot_quote(fillcolor)))


def dot_edge(lines, source, target, label=None):
    attrs = ['fillcolor="gray"']
    if label is not None:
        attrs.append("label={}".format(dot_quote(label)))
    lines.append("  {} -> {} [{}];".format(dot_quote(source), dot_quote(target), ", ".join(attrs)))


def dot_header(graph_name, label):
    return [
        "// generated by darts_genotype_tools.py",
        "digraph {} {{".format(graph_name),
        "  graph [rankdir=LR, label={}, labelloc=\"t\"];".format(dot_quote(label)),
        "  node [style=filled, shape=rect, align=center, fontsize=20, height=0.5, width=0.5, penwidth=2, fontname=\"times\"];",
        "  edge [fontsize=20, fontname=\"times\"];",
    ]


def cnn_source_label(source_index):
    if source_index == 0:
        return "c_{k-2}"
    if source_index == 1:
        return "c_{k-1}"
    return str(source_index - 2)


def cnn_dot(genotype, cell_name, label):
    if cell_name == "normal":
        pairs = genotype.normal
        concat = genotype.normal_concat
        graph_name = "normal"
    elif cell_name in ("reduce", "reduction"):
        pairs = genotype.reduce
        concat = genotype.reduce_concat
        graph_name = "reduction"
    else:
        fail("CNN dot cell must be normal, reduce, reduction, or both")

    steps = len(pairs) // 2
    lines = dot_header(graph_name, "{} {} cell".format(label, graph_name))
    dot_node(lines, "c_{k-2}", "darkseagreen2")
    dot_node(lines, "c_{k-1}", "darkseagreen2")
    for step in range(steps):
        dot_node(lines, str(step), "lightblue")
    for step in range(steps):
        target = str(step)
        for pos in (2 * step, 2 * step + 1):
            op, source = pairs[pos]
            dot_edge(lines, cnn_source_label(source), target, label=op)
    dot_node(lines, "c_{k}", "palegoldenrod")
    for state_index in concat:
        dot_edge(lines, cnn_source_label(state_index), "c_{k}")
    lines.append("}")
    return "\n".join(lines) + "\n"


def rnn_dot(genotype, label):
    pairs = genotype.recurrent
    steps = len(pairs)
    lines = dot_header("recurrent", "{} recurrent cell".format(label))
    dot_node(lines, "x_t", "darkseagreen2")
    dot_node(lines, "h_{t-1}", "darkseagreen2")
    dot_node(lines, "0", "lightblue")
    dot_edge(lines, "x_t", "0")
    dot_edge(lines, "h_{t-1}", "0")
    for step in range(1, steps + 1):
        dot_node(lines, str(step), "lightblue")
    for step, pair in enumerate(pairs):
        op, predecessor = pair
        dot_edge(lines, str(predecessor), str(step + 1), label=op)
    dot_node(lines, "h_t", "palegoldenrod")
    for state_index in genotype.concat:
        dot_edge(lines, str(state_index), "h_t")
    lines.append("}")
    return "\n".join(lines) + "\n"


def write_text(path, text):
    directory = os.path.dirname(os.path.abspath(path))
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(path, "w") as handle:
        handle.write(text)


def command_list(args):
    schemas = [args.schema] if args.schema != "all" else list(CATALOG.keys())
    for schema in schemas:
        if schema not in CATALOG:
            fail("unknown schema {!r}".format(schema))
        print("{} built-ins:".format(schema))
        for name in CATALOG[schema]:
            if name == "DARTS":
                print("  {}:{} (alias of {}:DARTS_V2)".format(schema, name, schema))
            else:
                print("  {}:{}".format(schema, name))
        if schema == "cnn":
            print("  search primitives: {}".format(", ".join(CNN_SEARCH_PRIMITIVES)))
            print("  eval ops: {}".format(", ".join(CNN_EVAL_OPS)))
        else:
            print("  primitives: {}".format(", ".join(RNN_PRIMITIVES)))
        print("")


def command_show(args):
    schema, name, genotype = resolve_genotype(args.name, args.schema, args.spec)
    label = "{}:{}".format(schema, name)
    errors, warnings = validation_for(schema, genotype)
    if schema == "cnn":
        show_cnn(label, genotype, errors, warnings)
    else:
        show_rnn(label, genotype, errors, warnings)
    if errors:
        raise SystemExit(1)


def graph_requests(schema, cell):
    if schema == "cnn":
        if cell == "both":
            return ["normal", "reduction"]
        if cell in ("normal", "reduce", "reduction"):
            return [cell]
        fail("CNN dot cell must be normal, reduce, reduction, or both")
    if cell in ("both", "recurrent"):
        return ["recurrent"]
    fail("RNN dot cell must be recurrent")


def command_dot(args):
    schema, name, genotype = resolve_genotype(args.name, args.schema, args.spec)
    label = "{}:{}".format(schema, name)
    ensure_valid_for_dot(schema, genotype)
    requests = graph_requests(schema, args.cell)
    graphs = []
    for request in requests:
        if schema == "cnn":
            basename = "normal" if request == "normal" else "reduction"
            graphs.append((basename, cnn_dot(genotype, request, label)))
        else:
            graphs.append(("recurrent", rnn_dot(genotype, label)))

    if args.output_dir:
        if not os.path.isdir(args.output_dir):
            os.makedirs(args.output_dir)
        for basename, text in graphs:
            path = os.path.join(args.output_dir, basename + ".dot")
            write_text(path, text)
            sys.stderr.write("wrote {}\n".format(path))
        return

    if args.output:
        if len(graphs) != 1:
            fail("--output writes one graph; use --output-dir for multiple graphs")
        write_text(args.output, graphs[0][1])
        sys.stderr.write("wrote {}\n".format(args.output))
        return

    for index, item in enumerate(graphs):
        if index:
            print("")
        sys.stdout.write(item[1])


def build_parser():
    parser = argparse.ArgumentParser(
        description="Inspect DARTS CNN/RNN genotypes and emit DOT without Graphviz.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python darts_genotype_tools.py list\n"
            "  python darts_genotype_tools.py show DARTS --schema cnn\n"
            "  python darts_genotype_tools.py show rnn:DARTS\n"
            "  python darts_genotype_tools.py dot DARTS --schema cnn --cell normal\n"
            "  python darts_genotype_tools.py dot DARTS --schema cnn --cell both --output-dir out\n"
            "  python darts_genotype_tools.py dot DARTS --schema rnn --output recurrent.dot\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list", help="list built-in genotypes and operation catalogs")
    list_parser.add_argument("--schema", choices=["all", "cnn", "rnn"], default="all", help="filter the catalog")
    list_parser.set_defaults(func=command_list)

    show_parser = subparsers.add_parser("show", help="show and validate one genotype")
    show_parser.add_argument("name", nargs="?", help="built-in name, optionally qualified as cnn:NAME or rnn:NAME")
    show_parser.add_argument("--schema", choices=["auto", "cnn", "rnn"], default="auto", help="schema for ambiguous built-in names")
    show_parser.add_argument("--spec", help="custom JSON/mapping/Genotype(...) spec; use - for stdin")
    show_parser.set_defaults(func=command_show)

    dot_parser = subparsers.add_parser("dot", help="emit DOT for a genotype")
    dot_parser.add_argument("name", nargs="?", help="built-in name, optionally qualified as cnn:NAME or rnn:NAME")
    dot_parser.add_argument("--schema", choices=["auto", "cnn", "rnn"], default="auto", help="schema for ambiguous built-in names")
    dot_parser.add_argument("--spec", help="custom JSON/mapping/Genotype(...) spec; use - for stdin")
    dot_parser.add_argument("--cell", choices=["both", "normal", "reduce", "reduction", "recurrent"], default="both", help="graph to emit")
    dot_parser.add_argument("--output", help="write a single graph to this DOT file")
    dot_parser.add_argument("--output-dir", help="write one DOT file per graph into this directory")
    dot_parser.set_defaults(func=command_dot)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
