# Prompt Craft

Use this as a compact recipe book after selecting categories from `gallery-catalog.md`. Produce a generation-ready prompt, not an essay. When execution is requested, hand off to the CLI/API sub-skill instead of running anything here.

## Universal prompt frame

```text
[canvas + aspect + artifact type].
[subject/domain + primary visual goal].
Layout: [zones, panels, grid, viewpoint, hierarchy].
Required visible text: "..." / "..." / "...".
Visual grammar: [arrows, callouts, cards, camera, material, chart encodings, UI components].
Style boundary: [specific medium/context, bounded influences, palette, lighting].
Quality constraints: [readability, margins, label clarity, consistency].
Avoid: [2-5 likely bad defaults].
```

Place structure before surface detail. If layout matters, define zones, panels, rows, columns, and hierarchy before describing textures or mood.

## Generation recipe

1. **Name the artifact**: poster, research Figure 1, dashboard screen, product hero render, isometric map, character sheet, storyboard, field guide, edit.
2. **Set canvas early**: landscape 16:9, landscape 3:2, portrait 3:4, square grid, device frame, or exact pixel-like proportions when required.
3. **List the visible entities**: subject, props, panels, labels, charts, components, environment details.
4. **Specify visual grammar**: arrows, axes, legends, callout lines, card modules, HUD, camera angle, material systems, lighting systems.
5. **Constrain style**: use one primary style anchor and one palette/material/light direction. Avoid stacking many incompatible aesthetics.
6. **Add targeted avoid-lines**: only for likely failures: fake logos, unreadable microtext, wrong genre, excessive clutter, broken anatomy, random kanji, operational security content.
7. **Route execution separately**: provide parameter suggestions only; do not run the API here.

## Exact text and typography

Use exact text handling whenever the image contains labels, UI copy, poster copy, chart axes, legends, or Chinese/multilingual text.

Checklist:

- Wrap every required string in quotes: `"Model A"`, `"Ablation"`, `"山川茶事"`.
- Provide copy as a separate block before style details.
- State script/language if important: Simplified Chinese, Traditional Chinese, English, bilingual.
- Use hierarchy: title largest, subtitle, module labels, axis labels, legend, CTA, fine print.
- Require `crisp`, `legible`, `large enough`, `no garbled characters` when readability matters.
- For dense text, reduce copy. Prefer short labels/modules over paragraph text.

Template:

```text
Design a 3:4 vertical poster. Required exact readable text:
Title: "山川茶事"
Subtitle: "冷泡系列"
Prices: "中杯 16 元" / "大杯 19 元"
CTA: "今日限定"
Use clear promotional hierarchy: title largest, product name second, prices in a neat lower module. Crisp Simplified Chinese typography, no garbled characters, no fake sponsor logos.
```

## Research figures and diagrams

Research figures should use diagram grammar, not generic illustration. Treat generated outputs as drafts, references, or style targets; do not imply they are validated scientific results or final paper evidence.

Include:

- venue/style frame: conference-paper, NeurIPS/ICLR-style, Nature/Cell biomedical figure, publication-grade white background;
- canvas: usually landscape 16:9 or 3:2;
- structural primitives: panels A-D, columns, blocks, nodes, heatmaps, charts, ribbons, dashed dividers;
- directed relationships: arrows, residual arcs, feedback loops, attack paths, numbered flow markers;
- exact labels, axes, legend values, module names, color semantics;
- clarity constraints: generous margins, readable labels, thin gray axes, restrained palette, no fake logos/watermarks.

Method diagram template:

```text
Landscape 16:9 conference-paper Figure 1 for "[method name]".
Layout: left-to-right pipeline with three zones.
Left: input cards labeled "[input 1]", "[input 2]", "[input 3]".
Center: model architecture block labeled "[core module]" with submodules "[submodule]", arrows, skip connection, and memory/cache panel.
Right: outputs labeled "[task A]", "[task B]" with small performance bars.
Use white background, muted teal/slate/orange accents, precise arrows, large readable labels, no poster aesthetics, no fake conference logos.
```

Data/chart template:

```text
Create a publication-grade [chart family] on a white background.
Structure: [rows/columns/panels].
Axes: x-axis "...", y-axis "..."; legend values "...".
Encoding: color = [...], line thickness proportional to [...], dashed line = [...].
Require consistent scales, aligned gridlines, readable tick labels, restrained palette, and no decorative clutter.
```

Security/agent-safety diagram caution:

- Keep payload examples harmless and visibly labeled as examples.
- Separate benign vs attack flows with line style/color semantics.
- Avoid operational exploit steps; frame the figure as defensive/explanatory.

## UI and product mockups

UI prompts should read like product specs.

Checklist:

- Name a fictional product to avoid real-brand leakage.
- Specify device/canvas: mobile screen, desktop monitor, component board, dashboard.
- Define information architecture: header, nav, primary cards, charts, rows, action buttons.
- Provide exact UI copy and values.
- Specify design system: palette, typography mood, spacing, icon alignment.
- Require production-quality mockup, crisp typography, no lorem ipsum unless requested.

Template:

```text
Create a 1290x2796 smartphone screen mockup for a fictional wellness app "AURAE".
Top header text: "Good morning, Lina" and "Today: Recovery 82".
Main cards: sleep score, hydration, breath session, weekly trend chart.
Bottom nav labels: "Home", "Plan", "Insights", "Profile".
Soft sage/cream palette, rounded cards, precise icon alignment, realistic app spacing, crisp readable text, no real brand logos.
```

## Posters, brands, and commercial imagery

Commercial prompts need hierarchy and material/lighting separation.

Checklist:

- First glance: recognizable hero silhouette/product/theme.
- Second glance: readable story, offer, or campaign promise.
- Third glance: texture, fine details, labels, atmosphere.
- Split controls: materials, lighting, palette, typography, background.
- Use `No visible brand logos` unless exact logos/brands are supplied by the user and permitted.

Product config pattern:

```text
/* PRODUCT_RENDER_CONFIG: [short name]
   AESTHETIC: Premium commercial photography */
{
  "GLOBAL_SETTINGS": {
    "aspect_ratio": "2:3 vertical",
    "style": "hyper-realistic commercial photography",
    "quality_flags": ["sharp_foreground", "micro_texture", "editorial_finish"]
  },
  "ENVIRONMENT": {
    "background": "[studio/backdrop/location]",
    "lighting": "[softbox/rim/natural side light]",
    "palette": "[3-5 color words]"
  },
  "CORE_ASSETS": {
    "primary_subject": "[product/food]",
    "materials": ["...", "..."],
    "composition": "[centered/diagonal/zero-gravity/flat lay]"
  },
  "OUTPUT": {
    "mood": "premium, precise, editorial",
    "avoid": ["fake brand logos", "cheap e-commerce banner", "plastic CGI"]
  }
}
```

## Multi-panel boards

Use panel-count discipline for grids, storyboards, expression sheets, worldbuilding sets, and small multiples.

Checklist:

- State exact grid/page count: `3x3`, `4x3`, `3x2`, `16-panel`, `19 numbered miniature pages`.
- Assign every panel a role, beat, or label.
- State shared identity/style constraints across panels.
- For storyboards: include camera language such as WIDE, OTS, CU, aerial, pan, static, duration.
- For character sheets: require front/side/back views, expression variations, accessories, color palette, material notes.
- For data small multiples: require consistent axes/scales and aligned legends.

Template:

```text
Create a 3x2 film storyboard grid for "[scene]". Each panel has a small shot label and camera note:
1 WIDE establishing shot, 2 OTS conversation, 3 CU object reveal, 4 low-angle tension shot, 5 tracking movement, 6 final static wide.
Keep the same character design, costume colors, lighting direction, and location continuity across all panels.
```

## Edit and reference-image prompts

Use this skill to draft edit prompts only. Execution, file checks, masks, and `gpt-image` commands belong to the CLI/API sub-skill.

Edit checklist:

- State the transformation first.
- Name what must remain unchanged: subject identity, layout, pose, text, geometry, product logo, chart values, camera angle.
- If using multiple references, identify roles: Image 1 subject, Image 2 style, Image 3 logo/packaging.
- For localized edits, say `change only [region/object]`; for all other regions say `keep everything else unchanged`.
- Repeat invariants in iterative edits.

Template:

```text
Transform the scene into a winter evening with heavy snowfall and cold blue-grey lighting.
Preserve the original subject identity, camera angle, composition, and all readable text exactly. Keep the chess position/object layout clearly readable. Change only the season, atmosphere, and surface snow; keep everything else unchanged.
```

## Photography and screen realism

Photorealism improves when the prompt says how the image was captured.

Useful controls:

- `RAW, unprocessed, full iPhone camera quality` for casual realism.
- `amateur iPhone photo`, `shot from the crowd at a distance`, or `eye-level 28 mm lens feel` for capture context.
- Add ordinary imperfections: reflections, lens glare, clutter, fingerprints, wet asphalt, motion blur, timestamp, screen moire.
- Pick one dominant capture frame; too many camera specs conflict.

## Quality, size, and cost-aware intent

This sub-skill does not execute the model, but it can recommend parameter intent:

- Use portrait orientation for posters, product ads, vertical cards, mobile mockups, and social-style infographics.
- Use landscape orientation for research figures, dashboards, game screenshots, storyboards, technical diagrams, and cinematic stills.
- Use square when the artifact is a grid board, icon-like asset, sticker pack, or neutral product crop.
- Suggest high quality only when final typography, product detail, or publication-like diagrams matter. Use lower/auto quality for exploratory drafts to manage cost.
- For dense text or exact labels, say this in the prompt and recommend a higher-quality final pass after the user approves the draft direction.
