from __future__ import annotations

from collections import deque


def adjacency(taxonomy):
    graph = {s["id"]: [] for s in taxonomy.get("synsets", [])}
    for synset in taxonomy.get("synsets", []):
        for relation in synset.get("relations", []):
            target = relation["target"]
            rel_type = relation.get("type", "related")
            graph.setdefault(synset["id"], []).append((target, rel_type))
            graph.setdefault(target, []).append((synset["id"], rel_type))
    return graph


def shortest_distance(taxonomy, start, goal):
    if start == goal:
        return {"distance": 0, "path": [start], "relations": []}
    graph = adjacency(taxonomy)
    queue = deque([(start, [start], [])])
    seen = {start}
    while queue:
        node, path, rels = queue.popleft()
        for nxt, rel in graph.get(node, []):
            if nxt in seen:
                continue
            if nxt == goal:
                return {"distance": len(path), "path": path + [nxt], "relations": rels + [rel]}
            seen.add(nxt)
            queue.append((nxt, path + [nxt], rels + [rel]))
    return {"distance": None, "path": [], "relations": []}


def classify_pair(taxonomy, start, goal, threshold):
    result = shortest_distance(taxonomy, start, goal)
    distance = result["distance"]
    result["classification"] = "near" if distance is not None and distance <= threshold else "far"
    return result
