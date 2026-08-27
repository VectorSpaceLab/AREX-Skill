#!/usr/bin/env python3
"""Select likely GPT Image 2 gallery categories for a task phrase.

Safe, deterministic, no-network helper. It uses a hard-coded distilled category
map from the generated prompt-gallery sub-skill; it does not inspect files or
call image APIs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from typing import Iterable


@dataclass(frozen=True)
class Category:
    name: str
    range: str
    count: int
    best_for: str
    keywords: tuple[str, ...]
    hybrids: tuple[str, ...]


CATEGORIES: tuple[Category, ...] = (
    Category(
        "Anime & Manga",
        "1-12",
        12,
        "2D anime scenes, manga panels, expression grids, multi-character scenes",
        ("anime", "manga", "cel", "shading", "character relationship", "expression", "panel", "naruto", "jjk", "bus stop"),
        ("Character Design", "Gaming", "Cinematic & Animation"),
    ),
    Category(
        "Gaming",
        "13-22",
        10,
        "Game screenshots, HUDs, worldbuilding boards, RPG/RTS/MOBA scenes",
        ("game", "gaming", "hud", "minimap", "quest", "health bar", "ammo", "rpg", "moba", "strategy", "worldbuilding", "screenshot"),
        ("Anime & Manga", "Pixel Art", "Isometric", "Retro & Cyberpunk"),
    ),
    Category(
        "Retro & Cyberpunk",
        "23-25",
        3,
        "Neon cyberpunk boards, synth crews, mecha, retro-future panels",
        ("cyberpunk", "retro", "synth", "neon", "mecha", "glowing", "future", "dystopian"),
        ("Gaming", "Cinematic Film References", "Typography & Posters"),
    ),
    Category(
        "Cinematic & Animation",
        "26-30",
        5,
        "Animated-film stills, storyboards, VHS/security-camera scenes",
        ("storyboard", "animation", "animated", "film still", "vhs", "security camera", "noir", "pixar", "ghibli"),
        ("Cinematic Film References", "Anime & Manga", "Photography"),
    ),
    Category(
        "Character Design",
        "31-32",
        2,
        "Character reference sheets, costume/prop breakdowns, art-direction pages",
        ("character", "reference sheet", "turnaround", "front side back", "costume", "expression sheet", "concept sheet", "prop"),
        ("Anime & Manga", "Gaming", "Tattoo Design"),
    ),
    Category(
        "Typography & Posters",
        "33-45",
        13,
        "Posters, covers, flyers, narrative silhouettes, readable copy hierarchy",
        ("poster", "typography", "title", "label", "labels", "text", "flyer", "cover", "cta", "price", "tagline", "chinese text", "copy", "silhouette"),
        ("Product & Food", "Events & Experience", "Fine Art Painting"),
    ),
    Category(
        "Illustration",
        "46-47",
        2,
        "Editorial illustration, travel/poster-like scenes, papercut/flat styles",
        ("illustration", "editorial", "papercut", "paper cut", "flat illustration", "stylized"),
        ("More Illustration Styles", "Watercolor", "Typography & Posters"),
    ),
    Category(
        "Watercolor",
        "48-49",
        2,
        "Soft watercolor scenes, paper grain, airy illustration",
        ("watercolor", "watercolour", "wash", "paper grain", "soft edge"),
        ("Illustration", "Fine Art Painting", "Ink & Chinese"),
    ),
    Category(
        "Ink & Chinese",
        "50-51",
        2,
        "Chinese ink landscapes, scroll scenes, brush textures",
        ("ink", "chinese", "gongbi", "scroll", "rice paper", "brush", "shan shui"),
        ("Watercolor", "Typography & Posters", "Fine Art Painting"),
    ),
    Category(
        "Pixel Art",
        "52-53",
        2,
        "Pixel still lifes, sprites, retro game assets",
        ("pixel", "sprite", "8-bit", "16-bit", "tile", "retro console"),
        ("Gaming", "Isometric"),
    ),
    Category(
        "Isometric",
        "54-55",
        2,
        "Isometric maps, cafes, fantasy villages, tile-readable layouts",
        ("isometric", "top-down", "diorama", "tile", "grid map", "map"),
        ("Gaming", "Pixel Art", "Architecture & Interior"),
    ),
    Category(
        "Product & Food",
        "56-59",
        4,
        "Product hero renders, food motion, packaging, commercial beverage posters",
        ("product", "food", "bottle", "packaging", "beverage", "ingredient", "splash", "commercial", "studio lighting", "hero render"),
        ("Brand Systems & Identity", "Photography", "Typography & Posters"),
    ),
    Category(
        "Brand Systems & Identity",
        "60-62",
        3,
        "Brand boards, logos, packaging/social touchpoints, visual identity systems",
        ("brand", "identity", "logo", "wordmark", "brand kit", "palette", "packaging set", "social post", "design system"),
        ("Product & Food", "UI/UX Mockups", "Typography & Posters"),
    ),
    Category(
        "Photography",
        "63-66",
        4,
        "Photoreal scenes, screen/notebook shots, casual camera realism",
        ("photo", "photography", "photoreal", "iphone", "raw", "lens", "camera", "subway", "notebook", "panorama"),
        ("Product & Food", "Beauty & Lifestyle", "Screen Photography"),
    ),
    Category(
        "Infographics & Field Guides",
        "67-74",
        8,
        "Encyclopedia cards, travel/cooking guides, museum boards, labeled layouts",
        ("infographic", "field guide", "guide", "encyclopedia", "callout", "tutorial", "travel", "module", "museum", "card"),
        ("Scientific & Educational", "Typography & Posters", "Data Visualization"),
    ),
    Category(
        "Research Paper Figures",
        "75-95",
        21,
        "Academic method figures, ML/biomedical workflows, paper-ready diagrams",
        ("research", "paper", "figure", "method", "pipeline", "architecture", "neurips", "iclr", "nature", "ablation", "rag", "transformer", "workflow", "llm", "agent"),
        ("Data Visualization", "Technical Illustration", "Scientific & Educational"),
    ),
    Category(
        "Official OpenAI Cookbook Examples",
        "96-99",
        4,
        "General cookbook-style examples: logos, pet/comic transformations, simple infographics",
        ("cookbook", "openai", "logo", "comic pet", "simple example"),
        ("Edit Endpoint Showcase", "Product & Food", "Infographics & Field Guides"),
    ),
    Category(
        "Edit Endpoint Showcase",
        "100-101",
        2,
        "Reference-image edits, inpainting/change prompts, poster/lightbox edits",
        ("edit", "inpaint", "mask", "preserve", "reference image", "same subject", "change only", "unchanged", "replace"),
        ("Photography", "Typography & Posters", "CLI/API execution route"),
    ),
    Category(
        "UI/UX Mockups",
        "102-106",
        5,
        "App screens, dashboards, design-system components, product mockups",
        ("ui", "ux", "app", "dashboard", "screen", "mobile", "desktop", "component", "wireframe", "mockup", "nav", "card"),
        ("Brand Systems & Identity", "Data Visualization"),
    ),
    Category(
        "Data Visualization",
        "107-111",
        5,
        "Small multiples, network graph, chord, treemap, choropleth",
        ("chart", "graph", "heatmap", "small multiple", "network", "chord", "treemap", "choropleth", "axis", "legend", "bar chart", "sankey"),
        ("Research Paper Figures", "Infographics & Field Guides"),
    ),
    Category(
        "Technical Illustration",
        "112-116",
        5,
        "Exploded views, cutaways, labeled assemblies, engineering plates",
        ("technical", "exploded", "cutaway", "assembly", "callout", "blueprint", "internal", "component", "engineering"),
        ("Scientific & Educational", "Product & Food", "Research Paper Figures"),
    ),
    Category(
        "Architecture & Interior",
        "117-121",
        5,
        "Interior/architecture renders, rooms, atriums, labs, realistic space design",
        ("architecture", "interior", "room", "atrium", "lab", "cathedral", "museum", "living room", "office", "brutalist"),
        ("Isometric", "Photography", "Scientific & Educational"),
    ),
    Category(
        "Scientific & Educational",
        "122-128",
        7,
        "Classroom science posters, anatomy, geology, weather, taxonomy",
        ("science", "educational", "anatomy", "geology", "weather", "periodic table", "phylogeny", "classroom", "poster"),
        ("Infographics & Field Guides", "Technical Illustration", "Research Paper Figures"),
    ),
    Category(
        "Fashion Editorial",
        "129-135",
        7,
        "Fashion lookbooks, runway/editorial portraits, luxury campaigns",
        ("fashion", "editorial", "runway", "lookbook", "haute couture", "streetwear", "y2k", "luxury", "portrait"),
        ("Photography", "Typography & Posters", "Beauty & Lifestyle"),
    ),
    Category(
        "Fine Art Painting",
        "136-140",
        5,
        "Painterly art styles, murals, color-field, impressionist or impasto scenes",
        ("painting", "fine art", "mural", "impasto", "impressionist", "color field", "hockney", "rothko"),
        ("Watercolor", "Ink & Chinese", "Illustration"),
    ),
    Category(
        "More Illustration Styles",
        "141-146",
        6,
        "Chibi, risograph, flat design, low-poly, stickers, holographic badges",
        ("chibi", "kawaii", "risograph", "flat design", "sticker", "holographic", "low-poly", "low poly"),
        ("Illustration", "Pixel Art", "Typography & Posters"),
    ),
    Category(
        "Cinematic Film References",
        "147-152",
        6,
        "Film-inspired scenes with bounded framing, lighting, and color",
        ("cinematic", "film", "director", "neo-noir", "symmetric", "pastel", "expressionist", "desert", "misty"),
        ("Cinematic & Animation", "Photography", "Retro & Cyberpunk"),
    ),
    Category(
        "Beauty & Lifestyle",
        "153-154",
        2,
        "Skincare/fragrance rituals, soft lifestyle product settings",
        ("beauty", "skincare", "fragrance", "vanity", "morning routine", "lifestyle", "ritual"),
        ("Product & Food", "Photography", "Fashion Editorial"),
    ),
    Category(
        "Events & Experience",
        "155-156",
        2,
        "Wayfinding maps, visitor routes, event/scenic-experience graphics",
        ("event", "wayfinding", "visitor", "route", "zoo", "scenic", "map", "experience", "festival"),
        ("Infographics & Field Guides", "Typography & Posters", "UI/UX Mockups"),
    ),
    Category(
        "Tattoo Design",
        "157-160",
        4,
        "Tattoo flash/sleeve studies, irezumi, black/grey, neo-traditional motifs",
        ("tattoo", "flash", "sleeve", "irezumi", "black grey", "linework", "negative space", "moth", "dragon"),
        ("Character Design", "Fine Art Painting", "Illustration"),
    ),
    Category(
        "Screen Photography",
        "161-162",
        2,
        "Realistic device/screen photos, webcam/laptop compositions",
        ("screen", "laptop", "webcam", "facetime", "music app", "glare", "monitor"),
        ("Photography", "UI/UX Mockups"),
    ),
)


ARTIFACT_HINTS: tuple[tuple[re.Pattern[str], str, int], ...] = (
    (re.compile(r"\b(figure|paper|method|pipeline|architecture|neurips|iclr|nature|rag|transformer|ablation)\b", re.I), "Research Paper Figures", 4),
    (re.compile(r"\b(chart|graph|heatmap|axis|legend|treemap|choropleth|network|sankey)\b", re.I), "Data Visualization", 4),
    (re.compile(r"\b(ui|ux|app|dashboard|mobile|screen|component|mockup)\b", re.I), "UI/UX Mockups", 4),
    (re.compile(r"\b(poster|flyer|cover|typography|title|copy|cta|price|label|labels)\b|chinese[- ]?(label|text|copy)", re.I), "Typography & Posters", 4),
    (re.compile(r"\b(product|packaging|bottle|beverage|food|commercial)\b", re.I), "Product & Food", 4),
    (re.compile(r"\b(edit|inpaint|mask|reference image|preserve|change only|unchanged)\b", re.I), "Edit Endpoint Showcase", 5),
    (re.compile(r"\b(game|hud|rpg|moba|strategy|minimap|quest)\b", re.I), "Gaming", 4),
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def score_category(query: str, category: Category) -> tuple[int, list[str]]:
    q = normalize(query)
    score = 0
    hits: list[str] = []

    for pattern, target, weight in ARTIFACT_HINTS:
        if target == category.name and pattern.search(query):
            score += weight
            hits.append(f"artifact:{target}")

    for keyword in category.keywords:
        k = normalize(keyword)
        if not k:
            continue
        if " " in k:
            if k in q:
                score += 3
                hits.append(keyword)
        else:
            if re.search(rf"(?<![\w-]){re.escape(k)}(?![\w-])", q):
                score += 2
                hits.append(keyword)

    # Gentle boost for exact category word fragments.
    for word in re.findall(r"[a-z0-9]+", category.name.casefold()):
        if len(word) >= 4 and re.search(rf"(?<![\w-]){re.escape(word)}(?![\w-])", q):
            score += 1
            hits.append(word)

    return score, hits


def select_categories(query: str, top: int) -> list[dict[str, object]]:
    ranked: list[tuple[int, Category, list[str]]] = []
    for category in CATEGORIES:
        score, hits = score_category(query, category)
        ranked.append((score, category, hits))

    ranked.sort(key=lambda item: (item[0], item[1].count), reverse=True)
    selected = [item for item in ranked if item[0] > 0][:top]
    if not selected:
        # Fallback: broad craft categories that help refine underspecified tasks.
        fallback_names = {"Typography & Posters", "Photography", "Illustration"}
        selected = [item for item in ranked if item[1].name in fallback_names][:top]

    result: list[dict[str, object]] = []
    for score, category, hits in selected:
        payload = asdict(category)
        payload["score"] = score
        payload["matched_signals"] = hits[:8]
        result.append(payload)
    return result


def print_list() -> None:
    print("Category\tRange\tCount\tBest for")
    for category in CATEGORIES:
        print(f"{category.name}\t{category.range}\t{category.count}\t{category.best_for}")


def print_selection(query: str, results: Iterable[dict[str, object]]) -> None:
    print(f"Query: {query}")
    for idx, item in enumerate(results, start=1):
        print(f"\n{idx}. {item['name']} (score {item['score']}, range {item['range']}, count {item['count']})")
        print(f"   Best for: {item['best_for']}")
        signals = item.get("matched_signals") or []
        if signals:
            print("   Matched signals: " + ", ".join(map(str, signals)))
        hybrids = item.get("hybrids") or []
        if hybrids:
            print("   Useful hybrids: " + ", ".join(map(str, hybrids)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Map a GPT Image 2 task phrase to likely prompt-gallery categories. No network/API calls.",
    )
    parser.add_argument("query", nargs="*", help="Task phrase to classify, e.g. 'Chinese ablation figure for ICLR paper'")
    parser.add_argument("--list", action="store_true", help="List all distilled gallery categories")
    parser.add_argument("--top", type=int, default=3, help="Number of category suggestions to return (default: 3)")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.top < 1:
        parser.error("--top must be >= 1")
    top = min(args.top, len(CATEGORIES))

    if args.list:
        if args.json:
            print(json.dumps([asdict(category) for category in CATEGORIES], ensure_ascii=False, indent=2))
        else:
            print_list()
        return 0

    query = " ".join(args.query).strip()
    if not query:
        parser.error("provide a query or use --list")

    results = select_categories(query, top)
    if args.json:
        print(json.dumps({"query": query, "results": results}, ensure_ascii=False, indent=2))
    else:
        print_selection(query, results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
