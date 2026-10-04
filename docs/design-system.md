# CareerPilot AI — Design System

## 1. Design Philosophy

CareerPilot AI uses a **professional, modern, light-themed** SaaS aesthetic. The interface should feel clean, trustworthy, and approachable — reflecting the platform's role as a career guidance tool for students.

**Principles:**
- Clean and spacious layouts with generous whitespace
- Subtle color accents (lavender, blue) — never overwhelming
- Rounded corners and soft shadows for a friendly feel
- Consistent typography hierarchy
- Responsive and accessible (WCAG 2.1 AA)

**Avoid:**
- Dark/cyberpunk themes
- Excessive gradients or neon colors
- Heavy animations or parallax effects
- Cluttered information density

## 2. Color Palette

### Primary Colors

| Token            | Value (oklch)                   | Hex Approx. | Usage                       |
|------------------|--------------------------------|-------------|-------------------------------|
| `--primary`      | `oklch(0.55 0.18 270)`         | #6C5CE7    | Primary buttons, links, focus |
| `--primary-foreground` | `oklch(0.99 0.005 270)` | #FAFAFF    | Text on primary backgrounds   |

### Accent Colors

| Token            | Value (oklch)                   | Hex Approx. | Usage                       |
|------------------|--------------------------------|-------------|-------------------------------|
| `--accent`       | `oklch(0.93 0.04 270)`         | #EDE9FE    | Subtle highlights, hover states|
| `--accent-foreground` | `oklch(0.30 0.10 270)` | #3B2E6E    | Text on accent backgrounds    |

### Surface Colors

| Token            | Value (oklch)                   | Hex Approx. | Usage                       |
|------------------|--------------------------------|-------------|-------------------------------|
| `--background`   | `oklch(0.995 0.002 270)`       | #FDFCFF    | Page background               |
| `--foreground`   | `oklch(0.18 0.02 270)`         | #1A1625    | Primary body text             |
| `--card`         | `oklch(1 0 0)`                 | #FFFFFF    | Card backgrounds              |
| `--card-foreground` | `oklch(0.18 0.02 270)`      | #1A1625    | Card text                     |
| `--muted`        | `oklch(0.96 0.015 270)`        | #F4F2F9    | Muted backgrounds, badges     |
| `--muted-foreground` | `oklch(0.50 0.04 270)`    | #6B6080    | Secondary text, captions      |

### Semantic Colors

| Token            | Value (oklch)                   | Hex Approx. | Usage                       |
|------------------|--------------------------------|-------------|-------------------------------|
| `--destructive`  | `oklch(0.577 0.245 27.325)`    | #E53E3E    | Error states, delete actions  |
| `--border`       | `oklch(0.92 0.01 270)`         | #E2DFF0    | Borders, dividers             |
| `--input`        | `oklch(0.92 0.01 270)`         | #E2DFF0    | Input field borders           |
| `--ring`         | `oklch(0.55 0.18 270)`         | #6C5CE7    | Focus rings (matches primary) |

### Chart Colors

| Token        | Value (oklch)                   | Hex Approx. | Usage            |
|--------------|--------------------------------|-------------|-------------------|
| `--chart-1`  | `oklch(0.55 0.18 270)`         | #6C5CE7    | Primary series     |
| `--chart-2`  | `oklch(0.62 0.16 250)`         | #4A90D9    | Secondary series   |
| `--chart-3`  | `oklch(0.70 0.12 230)`         | #56B4D3    | Tertiary series    |
| `--chart-4`  | `oklch(0.75 0.10 290)`         | #A78BFA    | Quaternary series  |
| `--chart-5`  | `oklch(0.80 0.08 200)`         | #67D4C0    | Quinary series     |

## 3. Typography

### Font Stack
- **Sans-serif (primary):** Geist Sans — `var(--font-geist-sans)`
- **Monospace (code):** Geist Mono — `var(--font-geist-mono)`

### Scale

| Level | Element | Size       | Weight   | Line Height | Letter Spacing |
|-------|---------|------------|----------|-------------|----------------|
| 1     | h1      | 2.25rem    | 700      | 1.2         | -0.025em       |
| 2     | h2      | 1.875rem   | 600      | 1.25        | -0.02em        |
| 3     | h3      | 1.5rem     | 600      | 1.3         | -0.015em       |
| 4     | h4      | 1.25rem    | 600      | 1.35        | -0.01em        |
| 5     | Body    | 1rem       | 400      | 1.6         | 0              |
| 6     | Small   | 0.875rem   | 400      | 1.5         | 0              |
| 7     | Caption | 0.75rem    | 500      | 1.4         | 0.02em         |

## 4. Spacing & Layout

- **Base unit:** 4px (`0.25rem`)
- **Common spacing:** 8, 12, 16, 20, 24, 32, 48, 64px
- **Max content width:** 1280px (`80rem`)
- **Card padding:** 24px (`1.5rem`)
- **Section gaps:** 32–48px
- **Page padding:** 16px (mobile), 24px (tablet), 32px (desktop)

### Breakpoints

| Name    | Min Width | Usage                    |
|---------|-----------|--------------------------|
| sm      | 640px     | Large phones             |
| md      | 768px     | Tablets                  |
| lg      | 1024px    | Small desktops           |
| xl      | 1280px    | Large desktops           |
| 2xl     | 1536px    | Extra-wide screens       |

## 5. Component Guidelines

### Cards
- Background: `--card` (white)
- Border: `1px solid var(--border)`
- Border radius: `var(--radius-lg)` (0.625rem)
- Shadow: `0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06)`
- Padding: 24px
- Hover: subtle elevation increase (`0 4px 12px rgba(0, 0, 0, 0.06)`)

### Buttons
- Use shadcn/ui `Button` variants: `default`, `secondary`, `outline`, `ghost`, `destructive`, `link`
- Default button uses `--primary` background
- Consistent height scale: xs(24px), sm(28px), default(32px), lg(36px)
- Border radius: `var(--radius-lg)`

### Inputs
- Height: 40px
- Border: `1px solid var(--input)`
- Border radius: `var(--radius-md)`
- Focus: `2px ring` using `--ring` color
- Background: white

### Badges / Tags
- Background: `--muted`
- Text: `--muted-foreground`
- Border radius: full (`9999px`)
- Padding: 4px 12px
- Font size: 0.75rem

## 6. Shadows

| Level   | Value                                                        | Usage                 |
|---------|--------------------------------------------------------------|-----------------------|
| sm      | `0 1px 2px rgba(0, 0, 0, 0.04)`                             | Subtle elements       |
| default | `0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06)` | Cards, dropdowns  |
| md      | `0 4px 12px rgba(0, 0, 0, 0.06)`                            | Elevated cards, hover |
| lg      | `0 8px 24px rgba(0, 0, 0, 0.08)`                            | Modals, popovers      |

## 7. Icons

- Library: **Lucide React** (`lucide-react`)
- Default size: 16px (`size-4`)
- Stroke width: 2px (default)
- Color: inherit from parent text color

## 8. Accessibility

- All interactive elements must have visible focus indicators (`--ring`)
- Minimum contrast ratio: 4.5:1 for normal text, 3:1 for large text
- All images must have descriptive `alt` attributes
- Form inputs must have associated labels
- Keyboard navigation must be fully supported
