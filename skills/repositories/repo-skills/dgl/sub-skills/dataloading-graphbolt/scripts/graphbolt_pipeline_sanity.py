#!/usr/bin/env python3
"""CPU-safe GraphBolt pipeline and metadata sanity checks."""

import argparse
import ast
import json
from pathlib import Path


SPLIT_NAMES = ("train_set", "validation_set", "test_set")
VALID_FEATURE_FORMATS = {"numpy", "torch"}
VALID_EDGE_FORMATS = {"csv", "numpy"}
VALID_FEATURE_DOMAINS = {"node", "edge", "graph"}


class ValidationError(Exception):
    """Raised when shallow metadata validation fails."""


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def strip_comment(line):
    in_single = False
    in_double = False
    for index, character in enumerate(line):
        if character == "'" and not in_double:
            in_single = not in_single
        elif character == '"' and not in_single:
            in_double = not in_double
        elif character == "#" and not in_single and not in_double:
            return line[:index]
    return line


def parse_scalar(value):
    value = value.strip()
    lowered = value.lower()
    if value == "":
        return None
    if lowered in {"null", "none", "~"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value[1:-1]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def split_key_value(content):
    if ":" not in content:
        raise ValidationError(f"expected key: value mapping, got: {content}")
    key, value = content.split(":", 1)
    key = key.strip()
    require(key != "", f"empty mapping key in line: {content}")
    return key, value.strip()


def preprocess_yaml_lines(text):
    parsed_lines = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        require("\t" not in raw_line, f"tabs are not supported in metadata line {line_number}")
        stripped_comment = strip_comment(raw_line).rstrip()
        if not stripped_comment.strip():
            continue
        indent = len(stripped_comment) - len(stripped_comment.lstrip(" "))
        parsed_lines.append((indent, stripped_comment.strip()))
    return parsed_lines


def parse_mapping(lines, index, indent):
    result = {}
    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent < indent:
            break
        require(current_indent == indent, f"unexpected indentation near: {content}")
        require(not content.startswith("- "), f"unexpected list item in mapping near: {content}")
        key, raw_value = split_key_value(content)
        index += 1
        if raw_value == "" and index < len(lines) and lines[index][0] > indent:
            value, index = parse_block(lines, index, lines[index][0])
        else:
            value = parse_scalar(raw_value)
        result[key] = value
    return result, index


def parse_sequence(lines, index, indent):
    result = []
    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent < indent:
            break
        require(current_indent == indent, f"unexpected indentation near: {content}")
        if not content.startswith("- "):
            break
        item_text = content[2:].strip()
        index += 1
        if item_text == "":
            if index < len(lines) and lines[index][0] > indent:
                item, index = parse_block(lines, index, lines[index][0])
            else:
                item = None
        elif ":" in item_text:
            key, raw_value = split_key_value(item_text)
            item = {}
            pending_nested_key = None
            if raw_value == "":
                pending_nested_key = key
            else:
                item[key] = parse_scalar(raw_value)
            if index < len(lines) and lines[index][0] > indent:
                child, index = parse_block(lines, index, lines[index][0])
                if pending_nested_key is not None:
                    item[pending_nested_key] = child
                elif isinstance(child, dict):
                    item.update(child)
                else:
                    raise ValidationError(f"cannot merge nested list into item near: {item_text}")
            elif pending_nested_key is not None:
                item[pending_nested_key] = None
        else:
            item = parse_scalar(item_text)
        result.append(item)
    return result, index


def parse_block(lines, index, indent):
    if index >= len(lines):
        return {}, index
    require(lines[index][0] == indent, "internal parser indentation mismatch")
    if lines[index][1].startswith("- "):
        return parse_sequence(lines, index, indent)
    return parse_mapping(lines, index, indent)


def parse_yaml_subset(text):
    lines = preprocess_yaml_lines(text)
    if not lines:
        return {}
    require(lines[0][0] == 0, "metadata root must start at indentation 0")
    metadata, index = parse_block(lines, 0, 0)
    require(index == len(lines), "metadata parser did not consume the full file")
    return metadata


def safe_load_metadata(text):
    try:
        import yaml
    except Exception:
        return parse_yaml_subset(text)
    loaded = yaml.safe_load(text)
    return loaded or {}


def load_metadata(path):
    metadata_path = Path(path)
    require(metadata_path.exists(), f"metadata file does not exist: {metadata_path}")
    text = metadata_path.read_text(encoding="utf-8")
    metadata = safe_load_metadata(text)
    require(isinstance(metadata, dict), "metadata root must be a mapping")
    return metadata_path, metadata


def check_relative_path(entry, field_path, base_dir, check_paths):
    if "path" not in entry:
        return None
    value = entry["path"]
    require(isinstance(value, str) and value, f"{field_path}.path must be a non-empty string")
    referenced_path = Path(value)
    require(not referenced_path.is_absolute(), f"{field_path}.path should be relative, not absolute")
    if check_paths:
        full_path = base_dir / referenced_path
        require(full_path.exists(), f"referenced path does not exist: {value}")
    return value


def validate_graph(metadata, base_dir, check_paths):
    graph_summary = {"present": False, "nodes": 0, "edges": 0, "topology": False}
    graph = metadata.get("graph")
    graph_topology = metadata.get("graph_topology")

    if graph is not None:
        require(isinstance(graph, dict), "graph must be a mapping")
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        require(isinstance(nodes, list), "graph.nodes must be a list")
        require(isinstance(edges, list), "graph.edges must be a list")
        for node_index, node_entry in enumerate(nodes):
            require(isinstance(node_entry, dict), f"graph.nodes[{node_index}] must be a mapping")
            require("num" in node_entry, f"graph.nodes[{node_index}].num is required")
            require(isinstance(node_entry["num"], int) and node_entry["num"] >= 0, f"graph.nodes[{node_index}].num must be a non-negative integer")
        for edge_index, edge_entry in enumerate(edges):
            require(isinstance(edge_entry, dict), f"graph.edges[{edge_index}] must be a mapping")
            require(edge_entry.get("format") in VALID_EDGE_FORMATS, f"graph.edges[{edge_index}].format must be one of {sorted(VALID_EDGE_FORMATS)}")
            check_relative_path(edge_entry, f"graph.edges[{edge_index}]", base_dir, check_paths)
            edge_type = edge_entry.get("type")
            if edge_type is not None:
                require(isinstance(edge_type, str), f"graph.edges[{edge_index}].type must be a string or null")
                require(len(edge_type.split(":")) == 3, f"graph.edges[{edge_index}].type should look like src:rel:dst")
        graph_summary.update({"present": True, "nodes": len(nodes), "edges": len(edges)})

    if graph_topology is not None:
        require(isinstance(graph_topology, dict), "graph_topology must be a mapping")
        require(graph_topology.get("type") == "FusedCSCSamplingGraph", "graph_topology.type must be FusedCSCSamplingGraph")
        check_relative_path(graph_topology, "graph_topology", base_dir, check_paths)
        graph_summary.update({"present": True, "topology": True})

    return graph_summary


def validate_features(metadata, base_dir, check_paths):
    features = metadata.get("feature_data", []) or []
    require(isinstance(features, list), "feature_data must be a list")
    for feature_index, feature_entry in enumerate(features):
        require(isinstance(feature_entry, dict), f"feature_data[{feature_index}] must be a mapping")
        require(feature_entry.get("domain") in VALID_FEATURE_DOMAINS, f"feature_data[{feature_index}].domain must be one of {sorted(VALID_FEATURE_DOMAINS)}")
        require(isinstance(feature_entry.get("name"), str) and feature_entry.get("name"), f"feature_data[{feature_index}].name is required")
        require(feature_entry.get("format") in VALID_FEATURE_FORMATS, f"feature_data[{feature_index}].format must be one of {sorted(VALID_FEATURE_FORMATS)}")
        check_relative_path(feature_entry, f"feature_data[{feature_index}]", base_dir, check_paths)
        feature_type = feature_entry.get("type")
        if feature_entry.get("domain") == "edge" and feature_type is not None:
            require(isinstance(feature_type, str), f"feature_data[{feature_index}].type must be a string or null")
            require(len(feature_type.split(":")) == 3, f"feature_data[{feature_index}].type for edge features should look like src:rel:dst")
    return len(features)


def validate_split_items(split_items, split_path, base_dir, check_paths):
    require(isinstance(split_items, list), f"{split_path} must be a list")
    data_entry_count = 0
    for item_index, split_item in enumerate(split_items):
        item_path = f"{split_path}[{item_index}]"
        require(isinstance(split_item, dict), f"{item_path} must be a mapping")
        split_type = split_item.get("type")
        if split_type is not None:
            require(isinstance(split_type, str), f"{item_path}.type must be a string or null")
        data_entries = split_item.get("data")
        require(isinstance(data_entries, list) and data_entries, f"{item_path}.data must be a non-empty list")
        seen_names = []
        for data_index, data_entry in enumerate(data_entries):
            data_path = f"{item_path}.data[{data_index}]"
            require(isinstance(data_entry, dict), f"{data_path} must be a mapping")
            entry_name = data_entry.get("name")
            if entry_name is not None:
                require(isinstance(entry_name, str) and entry_name, f"{data_path}.name must be a non-empty string or null")
                seen_names.append(entry_name)
            require(data_entry.get("format") in VALID_FEATURE_FORMATS, f"{data_path}.format must be one of {sorted(VALID_FEATURE_FORMATS)}")
            check_relative_path(data_entry, data_path, base_dir, check_paths)
            data_entry_count += 1
        if seen_names:
            require("seeds" in seen_names, f"{item_path}.data should include name: seeds for default MiniBatch mapping")
    return data_entry_count


def validate_tasks(metadata, base_dir, check_paths):
    tasks = metadata.get("tasks", []) or []
    require(isinstance(tasks, list), "tasks must be a list")
    data_entry_count = 0
    for task_index, task_entry in enumerate(tasks):
        require(isinstance(task_entry, dict), f"tasks[{task_index}] must be a mapping")
        for split_name in SPLIT_NAMES:
            if split_name in task_entry and task_entry[split_name] is not None:
                data_entry_count += validate_split_items(
                    task_entry[split_name],
                    f"tasks[{task_index}].{split_name}",
                    base_dir,
                    check_paths,
                )
    return {"tasks": len(tasks), "task_data_entries": data_entry_count}


def validate_metadata(path, check_paths):
    metadata_path, metadata = load_metadata(path)
    base_dir = metadata_path.parent
    graph_summary = validate_graph(metadata, base_dir, check_paths)
    feature_count = validate_features(metadata, base_dir, check_paths)
    task_summary = validate_tasks(metadata, base_dir, check_paths)
    return {
        "path": str(metadata_path),
        "dataset_name": metadata.get("dataset_name"),
        "graph": graph_summary,
        "feature_count": feature_count,
        **task_summary,
    }


def run_graphbolt_item_sampler(run_dataloader):
    import torch
    import dgl.graphbolt as graphbolt

    item_set = graphbolt.ItemSet(torch.arange(6), names="seeds")
    item_sampler = graphbolt.ItemSampler(item_set, batch_size=2, shuffle=False, drop_last=False)
    first_minibatch = next(iter(item_sampler))
    require(hasattr(first_minibatch, "seeds"), "ItemSampler did not return a MiniBatch with seeds")
    require(first_minibatch.seeds.tolist() == [0, 1], "unexpected first ItemSampler batch")

    summary = {
        "itemset_length": len(item_set),
        "first_batch_seeds": first_minibatch.seeds.tolist(),
        "dataloader_checked": False,
    }

    if run_dataloader:
        dataloader = graphbolt.DataLoader(item_sampler, num_workers=0)
        dataloader_minibatch = next(iter(dataloader))
        require(hasattr(dataloader_minibatch, "seeds"), "GraphBolt DataLoader did not return a MiniBatch with seeds")
        require(dataloader_minibatch.seeds.tolist() == [0, 1], "unexpected first GraphBolt DataLoader batch")
        summary["dataloader_checked"] = True

    return summary


def main():
    parser = argparse.ArgumentParser(description="Run CPU-safe GraphBolt ItemSampler and metadata sanity checks.")
    parser.add_argument("--metadata", help="Optional GraphBolt metadata.yaml path for shallow schema validation.")
    parser.add_argument("--check-paths", action="store_true", help="Require referenced metadata paths to exist locally.")
    parser.add_argument("--skip-graphbolt", action="store_true", help="Skip importing dgl.graphbolt and only validate metadata when provided.")
    parser.add_argument("--run-dataloader", action="store_true", help="Also instantiate and iterate a minimal GraphBolt DataLoader.")
    parser.add_argument("--quiet", action="store_true", help="Print nothing on success.")
    args = parser.parse_args()

    result = {"ok": True, "metadata": None, "graphbolt": None}

    if args.metadata:
        result["metadata"] = validate_metadata(args.metadata, args.check_paths)

    if not args.skip_graphbolt:
        result["graphbolt"] = run_graphbolt_item_sampler(args.run_dataloader)

    if not args.quiet:
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
