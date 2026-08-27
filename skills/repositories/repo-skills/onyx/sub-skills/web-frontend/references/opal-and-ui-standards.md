# Opal and UI Standards

Use this reference before writing visible UI, selecting components, changing layout, adding icons, or organizing frontend hooks/types.

## Component selection priority

1. Prefer Opal for new UI: `@opal/components`, `@opal/layouts`, `@opal/icons`, `@opal/illustrations`, `@opal/types`, and `@opal/utils`.
2. Use `web/src/sections/**` for reusable feature composites: entity cards, modals, domain-specific rows, action panels, and other page-independent pieces.
3. Use app/page layouts from `web/src/layouts/**` or Opal layout namespaces for route chrome and settings/admin page structure.
4. Fall back to `web/src/refresh-components/**` only when Opal has no equivalent and an existing production component fits.
5. Do not introduce new dependencies on legacy `web/src/components/**` except for existing specialized surfaces such as logo handling or established markdown rendering.
6. Do not use raw `<button>`, `<input>`, `<textarea>`, or naked text when Opal or refresh components exist.

## Opal imports and common components

Use app-level aliases from web app code:

```tsx
import { Button, Card, InputTypeIn, Text } from "@opal/components";
import { Content, ContentAction, IllustrationContent, SettingsLayouts } from "@opal/layouts";
import { SvgPlus, SvgSettings } from "@opal/icons";
import { cn, markdown } from "@opal/utils";
import type { RichStr } from "@opal/types";
```

Inside Opal package source itself, use the package's `@opal/*` aliases, not app `@/*` aliases.

### Button

Always use Opal `Button` for new buttons. Use `variant` for semantic intent, `prominence` for visual hierarchy, `size` for density, and `icon`/`rightIcon` for iconography. Use `aria-label` for icon-only buttons.

Common choices:

- `variant="default"` for standard actions.
- `variant="danger"` for destructive actions.
- `prominence="primary"` for main page actions.
- `prominence="secondary"` or `"tertiary"` for lower-priority actions.
- `prominence="internal"` for chrome/internal controls.

### Text and RichStr

Use Opal `Text` for all user-visible text. Avoid naked strings in `<div>`, `<h*>`, and `<p>` nodes.

- Choose a `font` preset such as `heading-h2`, `main-ui-body`, `main-ui-action`, `secondary-body`, or `secondary-action`.
- Choose semantic text color such as `text-03` instead of raw Tailwind colors.
- Use the `as` prop when semantic HTML matters.
- Type new visible string props as `string | RichStr` so callers can opt into inline markdown.
- Use `markdown("...")` from `@opal/utils` only for trusted or deliberate inline markdown. Plain strings are rendered as text.

Example:

```tsx
interface EmptyStateProps {
  title: string | RichStr;
  description?: string | RichStr;
}

function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <IllustrationContent
      title={title}
      description={description}
      illustration={SvgSettings}
    />
  );
}
```

### Layouts

Use Opal layouts rather than hand-rolled flex blocks for common structures.

- `Content`: icon, title, and description. Choose `sizePreset` and `variant` instead of reimplementing heading/body spacing.
- `ContentAction`: `Content` with right-side actions; use its `padding` prop instead of wrapper divs for spacing.
- `IllustrationContent`: empty states, informational placeholders, and error pages with a centered illustration.
- `SettingsLayouts.Root/Header/Body`: admin/settings pages with centered scrollable content, sticky action headers, back button support, and consistent body spacing.
- `RootLayout` and `SidebarLayouts`: app chrome, sidebars, and responsive app shell behavior.
- `Card`, `MessageCard`, `Table`, `Popover`, `Modal`, `InputTypeIn`, `InputTextArea`, `InputSelect`, and `Checkbox` should be preferred over raw equivalents.

When using size/padding/rounding variant props, default to `"md"` unless the component has a strong reason not to.

## Icons

Use the existing Onyx/Opal icon set for new UI, preferably from `@opal/icons`. Do not import new icons from `lucide-react`, `react-icons`, or other generic icon libraries even if they are present in package dependencies. If a required icon is missing, add or request an Onyx-style SVG icon rather than mixing visual systems.

For icon-only interactive controls, provide an accessible label and verify it is reachable by role/label queries in tests.

## Colors and dark mode

Use Onyx semantic color classes and Opal tokens. Do not use raw Tailwind palette classes such as `bg-white`, `text-gray-*`, `border-slate-*`, `bg-blue-*`, or `text-green-*` for new UI.

Common semantic families:

- Text: `text-01` through `text-05`, plus inverted text colors.
- Backgrounds: `background-neutral-*`, `background-tint-*`, and inverted background variants.
- Borders: `border-01` through `border-05`, plus inverted border variants.
- Actions: `action-selection-*`, `action-danger-*`.
- Status: `status-info-*`, `status-success-*`, `status-warning-*`, `status-error-*`.
- Theme: `theme-primary-*`, `theme-red-*`, `theme-blue-*`, and related theme tokens.

Do not use Tailwind `dark:` modifiers in normal UI. Theme inversion is handled by CSS variables and the `next-themes` class. The only acceptable `dark:` usage is logo/brand asset handling where different image assets or inversion are required.

## Class names, spacing, and wrappers

Use `cn()` from `@opal/utils` for conditional class names and class merging. Do not build className strings manually with template interpolation when `cn()` would be clearer.

Prefer padding over margins:

- Use a component's own `padding` prop when it exists.
- Use padding utilities on the content container when no prop exists.
- Avoid wrapper divs whose only purpose is adding spacing.
- Avoid margins for component spacing unless you are working with an existing legacy pattern that cannot be changed safely.

Keep comments brief and only explain durable intent. Avoid comments that restate the code or describe the current change.

## Imports, components, and TypeScript style

- Use absolute app imports with `@/` in web app code. Avoid deep relative imports such as `../../../`.
- Use `@tests/*` aliases in tests and `@opal/*` aliases for Opal subpaths.
- Prefer regular function declarations for React components.
- Extract prop interfaces in the same file as the component.
- Put shared DTOs, enums, and models in a co-located `interfaces.ts` or feature `types.ts`, not in component files that other modules import.
- Keep strict TypeScript and avoid `any`. If a third-party or backend response is unknown, parse or narrow it at the boundary.
- Use `"use client"` only for files that need hooks, browser APIs, or client event handlers.

## Hooks organization

Put hooks in the most specific owner:

1. Feature hooks in `web/src/lib/<feature>/hooks.ts` when tied to a domain such as users, agents, billing, connectors, projects, settings, tools, or Craft service data.
2. Opal hooks under `web/lib/opal/src/hooks/**` when reusable UI behavior has no Onyx app knowledge.
3. `web/src/hooks/**` only for genuinely cross-cutting web app hooks with no feature home and no Opal fit.

Pair hooks with service modules and stable SWR keys when they fetch data. Avoid dumping feature-specific hooks into the global hooks directory.

## Opal package and shared package rules

Opal package source uses kebab-case component directories and commonly contains `components.tsx`, `README.md`, optional CSS, and optional stories. Types/interfaces are usually local to `components.tsx` and re-exported from a single block at the bottom.

The shared package is platform-agnostic design tokens, contracts, DTOs, and pure utilities. It must not add runtime dependencies and must not depend on DOM, Node, React, Next, or React Native APIs. Edit token JSON sources rather than generated `dist` output, and rebuild when package-style consumers need generated CSS/types.

## Quick review checklist

Before sending a web UI change for review, check:

- New UI uses Opal first and does not introduce raw controls where components exist.
- Visible text goes through `Text` or a component that renders through `Text`.
- String props that render text accept `string | RichStr` where useful.
- Imports are absolute and use `@opal`/`@` aliases correctly.
- Colors are semantic Onyx classes and no new `dark:` classes were added outside logo handling.
- Spacing uses padding/component props, not wrapper-only divs or margins.
- Component props/types are strict, co-located, and readable.
- Data fetching remains in feature hooks/services rather than scattered through page bodies.
