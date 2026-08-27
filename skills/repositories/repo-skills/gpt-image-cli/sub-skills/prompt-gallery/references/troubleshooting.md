# Prompt Gallery Troubleshooting

Use this file to repair weak GPT Image 2 prompts before handing them to the CLI/API sub-skill.

## Symptom -> likely cause -> repair

| Symptom | Likely cause | Repair |
|---|---|---|
| Output looks generic or stock | Prompt names a subject but not an artifact, layout, capture context, or style boundary | Start with artifact + canvas; add 5-12 concrete visible nouns; separate material, lighting, and palette controls |
| Text is garbled or tiny | Required copy was implied, too dense, or mixed into prose | Create a `Required exact readable text` block; quote every string; reduce copy; require crisp large labels and no garbled characters |
| Diagram looks like an illustration | Missing diagram grammar | Add panels, nodes, arrows, axis labels, legends, color semantics, dashed dividers, and publication-grade white background |
| Layout drifts or panels merge | Grid/panel count not explicit | State exact grid dimensions, assign each panel a role, require aligned gutters/margins, and repeat shared style/identity constraints |
| Too many concepts compete | Multiple categories or styles stacked without priority | Pick one primary category; keep at most 2-3 hybrid categories; move optional details to avoid-line or second iteration |
| Wrong category/style | Selected by aesthetic word instead of artifact type | Reclassify by output artifact first: paper figure, UI screen, poster, product hero, game screenshot, edit, etc. |
| Edit changes too much | Invariants not named | State transformation first, then list identity/layout/text/geometry/position elements that must remain unchanged |
| Reference-image composition fails | Reference roles are ambiguous | Label references by role: Image 1 subject, Image 2 style, Image 3 logo/layout; say exactly how they combine |
| Product image looks plasticky | Material/lighting/palette collapsed into vague "premium" | Specify real materials, surface micro-texture, condensation/fibers/metal/glass, studio lighting, and avoid plastic CGI |
| UI mockup feels decorative | Missing product spec and real copy/data | Add fictional product name, device/canvas, header text, cards, values, rows, nav labels, and design-system rules |
| Research figure looks misleading | Prompt asks for final paper evidence or invented results | Frame output as a conceptual figure/reference; provide exact labels and avoid claims of validated measurements unless supplied |
| Fake logos/brands appear | Prompt leaves commercial identity open | Say `No visible brand logos` or supply exact fictional brand name/wordmark; avoid sponsor strips unless exact names are provided |
| Chinese/multilingual text fails | Language/script and hierarchy unspecified | State Simplified/Traditional Chinese or bilingual rules; use short modules; quote all required strings; avoid pinyin/English unless wanted |

## Repair patterns

### Weak prompt

```text
Make a good AI research diagram about agents.
```

### Stronger repair

```text
Landscape 16:9 conference-paper Figure 1 titled "Closed-loop LLM Agent System".
Layout: left-to-right pipeline with five labeled blocks: "User Prompt", "Planner", "Tool Use", "Memory", "Verifier". Add a feedback arrow from "Verifier" back to "Planner" labeled "self-correction".
Use white background, muted slate/blue/orange palette, precise arrows, generous margins, large readable labels, no poster aesthetics, no fake conference logos.
```

### Weak typography prompt

```text
Make a Chinese tea ad with prices.
```

### Stronger repair

```text
Design a 3:4 vertical premium tea poster. Required exact readable Simplified Chinese text: "山川茶事" / "冷泡系列" / "中杯 16 元" / "大杯 19 元" / "今日限定".
Hierarchy: title largest at top, hero cup/bottle centered, prices in a lower rounded module, CTA as small red seal. Crisp legible Chinese typography, warm paper texture, soft studio lighting, no garbled characters, no fake sponsor logos.
```

## Category mismatch recovery

1. Restate the requested artifact in one noun phrase.
2. Select the category from artifact type, not style adjective.
3. Add style as a bounded influence only after the layout is stable.
4. If the result is hybrid, name primary + secondary categories in the prompt planning note.

Examples:

- "anime research figure" -> primary `Research Paper Figures`, secondary `Anime & Manga` only for palette/character stylization.
- "dashboard poster" -> primary `UI/UX Mockups` if it is an interface; primary `Typography & Posters` if it is an advertisement about a dashboard product.
- "scientific infographic" -> primary `Scientific & Educational` for classroom/science accuracy; secondary `Infographics & Field Guides` for modular layout.

## Research-figure misuse cautions

- Do not present generated images as validated results, measured outputs, or finished scientific evidence.
- If the user supplies no numbers, use placeholders or clearly fictional values; do not invent metrics as if factual.
- Require visible uncertainty or schematic wording for conceptual mechanisms.
- For chart-like figures, ask for or preserve exact axes, values, labels, and legends when correctness matters.
- For security or prompt-injection figures, keep payload examples harmless and defensive; avoid operational instructions.

## Edit invariant checklist

Before handing an edit prompt to the CLI/API sub-skill, ensure the prompt states:

- transformation target;
- input/reference role(s);
- unchanged identity and composition;
- unchanged text, logos, chart values, geometry, and object positions when relevant;
- masked/localized region if only part of the image should change;
- allowed changes and forbidden drift.

If any of these are missing, revise the prompt before execution.
