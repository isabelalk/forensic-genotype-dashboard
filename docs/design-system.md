# Design System

The interface is a compact forensic genomics workbench, not a marketing page. It should feel like a dark or glass scientific dashboard for VCF processing, HIrisPlex-S phenotype reading, and PLEX-34 STRUCTURE ancestry review.

The layout should favor short scan paths, separated processing stages, dense cards, and neon status accents. Avoid oversized hero areas, large promotional copy, and generic SaaS page structure.

## Signature Layout

- Compact header with `Virtual Phenotypic Modeling`, a one-line scientific subtitle, identity chips for `Genomics Workbench` and `HIrisPlex-S + PLEX-34`, and the theme toggle on the right.
- Four separated workflow sections: `Upload VCF`, `Quality Control / Processing Status`, `Conversion / Processing`, and `Result Reader`.
- Result readers stay side-by-side on desktop.
- HIrisPlex phenotype cards and STRUCTURE composition or map review stay compact.

## Themes

Themes are applied at the app root with `data-theme="neon-light"` or `data-theme="dark"`. Neon Light remains the persisted default. Dark Mode is the preferred forensic cockpit surface.

## Color Tokens

| Role | CSS token | Light | Dark | Usage |
|------|-----------|-------|------|-------|
| App background | `--color-bg` | `#F6F8FC` | `#181A2E` | Page base |
| Atmosphere | `--color-bg-soft` | `#F9FAFD` | `#2B3156` | Mesh gradients and quiet washes |
| Card surface | `--color-card` | `#FFFFFF` | `#232847` | Primary card cores |
| Card elevated | `--color-card-strong` | `#F9FAFD` | `#2B3156` | Secondary cards and nested data panels |
| Border | `--color-border` | `#DCE5F2` | `rgba(255,255,255,0.08)` | Hairlines and dropzones |
| Border strong | `--color-border-strong` | `#C8D5E8` | `rgba(255,255,255,0.16)` | Active and focus borders |
| Text primary | `--color-text` | `#172033` | `#F4F6FF` | Headings and labels |
| Text secondary | `--color-text-muted` | `#5C6784` | `#B6BEDA` | Body copy and helper text |
| Text disabled | `--color-text-disabled` | `#74809C` | `#8D96B8` | Disabled controls |
| Primary | `--color-primary` | `#A855F7` | `#A855F7` | Primary actions and active ancestry |
| Secondary | `--color-secondary` | `#EC4899` | `#EC4899` | Gradient pair and result accents |
| Info | `--color-info` | `#06B6D4` | `#06B6D4` | STRUCTURE map, guidance, links |
| Success | `--color-success` | `#10B981` | `#10B981` | Valid states and HIrisPlex actions |
| Warning | `--color-warning` | `#F59E0B` | `#FBBF24` | Missing markers and genotypes |
| Error | `--color-error` | `#EF4444` | `#F87171` | Blocking parse or validation errors |
| Primary action text | `--color-on-primary` | `#FFFFFF` | `#FFFFFF` | Text on brand gradients |
| Success action text | `--color-on-success` | `#052E2B` | `#052E2B` | Text on emerald gradients |

New visual colors should be declared here before component use. Component code should reference CSS variables, semantic utility classes, or Tailwind values that map directly to this token set.

## Derived Surface Tokens

- `--surface-glass`: translucent shell for compact dashboard cards.
- `--surface-hover`: subtle hover tint for cards and dropzones.
- `--surface-dropzone`: dense upload and drop-zone material.
- `--surface-dropzone-brand` and `--surface-dropzone-success`: active upload tints.
- `--surface-disabled`: disabled control material with readable text.
- `--shadow-card`: restrained card elevation.
- `--shadow-glow`: violet and magenta neon glow for primary actions.
- `--shadow-success`: green glow for HIrisPlex success and action states.
- `--gradient-brand`, `--gradient-success`, and `--gradient-info`: tokenized neon ramps.

## Typography

- Primary font: `Aptos, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif`.
- Display font: same stack, tight tracking, restrained size.
- Mono font: `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace` with tabular numbers.

| Level | Tailwind scale | Weight | Usage |
|-------|----------------|--------|-------|
| App title | `text-2xl` to `sm:text-[1.75rem]` | 800 to 900 | Compact dashboard header |
| Section | `text-xl` to `md:text-2xl` | 800 | Workflow section titles |
| Card title | `text-lg` to `text-xl` | 750 to 900 | Upload, conversion, and result cards |
| Body | `text-sm` to `text-base` | 400 to 600 | Instructions and summaries |
| Data caption | `text-xs` | 600 to 800 | Marker IDs, row indices, table labels |

Do not use `text-4xl`, `text-5xl`, or `text-6xl` marketing headings in the app shell. Data values should use mono or tabular figures. User-facing workflow labels and helper copy are English.

## Spacing and Layout

All spacing follows Tailwind's 4px-based scale.

| Token | Tailwind | Usage |
|-------|----------|-------|
| Tight | `gap-2`, `p-2`, `px-2 py-1` | Badges, chips, table controls |
| Standard | `gap-3`, `p-3`, `p-4` | Rows, alerts, selected-file panels |
| Compact card | `gap-4`, `p-5`, `p-6` | Analysis cores and upload cards |
| Dashboard rhythm | `space-y-5`, `gap-5`, `md:space-y-6` | Section separation |
| Page | `px-4 sm:px-6 lg:px-8`, `py-6 md:py-8` | Full-width app rhythm |

Layout rules:

- Keep root and atmospheric background full width.
- Center the foreground dashboard rail with responsive full-width padding and a wide cap such as `max-w-[min(100%,112rem)]`.
- Use `.analysis-shell` around `.analysis-core` for major workflow sections.
- Keep upload and result readers side-by-side at `xl:grid-cols-2`, stacked below desktop.
- Use wide responsive caps such as `max-w-[min(100%,104rem)]` rather than narrow rails.
- Preserve workflow order on responsive layouts: upload, validate, convert or parse, read results.

## Component Rules

### Compact Dashboard Header

- Left title group, scientific subtitle, two small identity chips, right theme toggle.
- Native theme button with `aria-pressed`, visible labels, and SVG or `react-icons` only.
- No oversized hero, giant marketing headline, workflow hero card, or large nav bar.

### Upload Cards and Dropzones

- Label row, compact dashed dropzone, selected-file row, primary action button, success or error alert.
- States: empty, drag-active, selected, uploading or parsing, success, error.
- Use `react-icons/hi`; no emojis.

### Buttons

- `.btn-primary`: brand gradient, compact rounded rectangle, violet and magenta glow.
- `.btn-success`: emerald and teal glow for HIrisPlex actions.
- `.btn-secondary`: quiet border/core for downloads and tertiary actions.
- Include default, hover, active, focus-visible, disabled, and loading states.

### Phenotype Cards

- Cards: Eye Color, Hair Color, Skin Color.
- Use only `HirisPlexSResultRow.top_predictions` fields.
- Use a compact three-column grid on desktop for parsed results.
- Keep scientific inline SVG illustrations, never emoji or image replacements.
- Display backend skin labels directly: `Very Pale`, `Pale`, `Intermediate`, `Dark`, and `Dark-to-Black`.
- When `skin_probability` is `null`, show unavailable with no invented probability.

### STRUCTURE Ancestry Dashboard

- Supported labels only: Africa, Europe, East Asia, South Asia.
- Put composition bars and inline world map side-by-side on desktop, stacked on mobile.
- Highlight only the highest supported probability from `row.probabilities`.
- Do not display or highlight Americas, Oceania, Middle East, or other unsupported labels.
- Keep additional sample cards hidden by default behind a checkbox using the validation-panel checkbox pattern.
- Preserve raw extracted STRUCTURE lines as dense themed data with sticky header and mono text.

## Motion and Depth

- Micro transitions: `180ms`, for icon color, focus, and chips.
- Standard transitions: `280ms`, for buttons, dropzones, and cards.
- Entry motion: `420ms` to `640ms`, for section or card fade-up.
- Pulse: `2400ms`, only for selected ancestry glow.

Animate only `transform`, `opacity`, `filter`, `color`, and shadow-like properties. Don't animate layout properties. `prefers-reduced-motion: reduce` disables entry, pulse, float, glow, and spinner flourish animations while preserving state changes.

Both themes keep the same dashboard hierarchy. Dark Mode changes tokens and contrast only. It must not add a separate layout, processing path, backend contract, or unsupported ancestry region.
