# CareerPilot AI — Design System

## 1. Design Philosophy

CareerPilot AI uses a **professional, modern, light-themed** SaaS aesthetic. The interface should feel clean, trustworthy, and approachable — reflecting the platform's role as a career guidance tool for students.

**Principles:**
- Clean and spacious layouts with purposeful whitespace
- Forest green for branding and primary actions — conveying growth and trust
- Saffron for selective, high-visibility calls to action
- Rounded corners and soft shadows for a friendly feel
- Consistent typography hierarchy
- Responsive and accessible (WCAG 2.1 AA)

**Avoid:**
- Dark/cyberpunk themes
- Excessive gradients or neon colors
- Heavy animations or parallax effects
- Cluttered information density
- Generic AI-generated landing-page patterns

## 2. Color Palette

### Primary Colors

| Token                  | Value (oklch)              | Hex Approx. | Usage                          |
|------------------------|---------------------------|-------------|--------------------------------|
| `--primary`            | `oklch(0.385 0.085 157)`  | #1B5E3B     | Branding, primary buttons, links, focus rings |
| `--primary-foreground` | `oklch(0.99 0 0)`         | #FFFFFF     | Text on primary backgrounds    |

**Hover state:** `primary/80` (approx. #2E7D4F) — used via Tailwind opacity modifier.

### Saffron Accent

| Token                  | Value (oklch)              | Hex Approx. | Usage                          |
|------------------------|---------------------------|-------------|--------------------------------|
| `--saffron`            | `oklch(0.795 0.160 75)`   | #F59E0B     | Important CTAs, attention-drawing elements |
| `--saffron-foreground` | `oklch(0.185 0.025 157)`  | #14261C     | Text on saffron backgrounds    |

> Use saffron selectively — only for the most important conversion actions (e.g., "Get Started" in hero). Do not use for general UI elements.

### Semantic Colors

| Token                  | Value (oklch)              | Hex Approx. | Usage                          |
|------------------------|---------------------------|-------------|--------------------------------|
| `--info`               | `oklch(0.655 0.148 230)`  | #0EA5E9     | Informational badges, highlights |
| `--info-foreground`    | `oklch(0.99 0 0)`         | #FFFFFF     | Text on info backgrounds       |
| `--destructive`        | `oklch(0.548 0.218 27)`   | #DC2626     | Error states, delete actions   |

### Surface Colors

| Token                  | Value (oklch)              | Hex Approx. | Usage                          |
|------------------------|---------------------------|-------------|--------------------------------|
| `--background`         | `oklch(0.981 0.004 155)`  | #F6FAF7     | Page background (green-tinted white) |
| `--foreground`         | `oklch(0.185 0.025 157)`  | #14261C     | Primary body text              |
| `--card`               | `oklch(1 0 0)`            | #FFFFFF     | Card backgrounds               |
| `--card-foreground`    | `oklch(0.185 0.025 157)`  | #14261C     | Card text                      |
| `--muted`              | `oklch(0.965 0.006 155)`  | #F0F5F1     | Muted backgrounds, badges      |
| `--muted-foreground`   | `oklch(0.45 0.03 157)`    | #5A7362     | Secondary text, captions       |
| `--accent`             | `oklch(0.935 0.012 155)`  | #E5EDE7     | Subtle highlights, hover states |
| `--accent-foreground`  | `oklch(0.25 0.04 157)`    | #1E3B28     | Text on accent backgrounds     |
| `--border`             | `oklch(0.915 0.008 155)`  | #DAE3DC     | Borders, dividers (green-tinted) |
| `--input`              | `oklch(0.915 0.008 155)`  | #DAE3DC     | Input field borders            |
| `--ring`               | `oklch(0.385 0.085 157)`  | #1B5E3B     | Focus rings (matches primary)  |

### Chart Colors

| Token        | Value (oklch)              | Hex Approx. | Usage            |
|--------------|---------------------------|-------------|-------------------|
| `--chart-1`  | `oklch(0.385 0.085 157)`  | #1B5E3B     | Primary series (green) |
| `--chart-2`  | `oklch(0.795 0.160 75)`   | #F59E0B     | Secondary series (saffron) |
| `--chart-3`  | `oklch(0.655 0.148 230)`  | #0EA5E9     | Tertiary series (blue) |
| `--chart-4`  | `oklch(0.487 0.092 157)`  | #2E7D4F     | Quaternary (lighter green) |
| `--chart-5`  | `oklch(0.55 0.10 180)`    | #2D8A8A     | Quinary (teal)   |

### Color Usage Rules

| Color    | Use For                                  | Do NOT Use For                    |
|----------|------------------------------------------|-----------------------------------|
| Green    | Branding, nav, primary buttons, links    | Warnings, errors                  |
| Saffron  | Hero CTA, important conversion actions   | General buttons, backgrounds      |
| Blue     | Informational badges, stats, info alerts | Primary actions, branding         |
| Red      | Error states, delete confirmations       | Anything else                     |

## 3. Typography

### Font Stack
- **Sans-serif (primary):** Geist Sans — `var(--font-geist-sans)`
- **Monospace (code):** Geist Mono — `var(--font-geist-mono)`

### Scale

| Level | Element | Size       | Weight   | Line Height | Letter Spacing |
|-------|---------|------------|----------|-------------|----------------|
| 1     | h1      | 2.75rem    | 700      | 1.15        | -0.025em       |
| 2     | h2      | 1.875rem   | 700      | 1.25        | -0.02em        |
| 3     | h3      | 1.25rem    | 600      | 1.35        | -0.01em        |
| 4     | h4      | 0.95rem    | 600      | 1.4         | 0              |
| 5     | Body    | 1rem       | 400      | 1.6 (1.75)  | 0              |
| 6     | Small   | 0.875rem   | 400–500  | 1.5         | 0              |
| 7     | Caption | 0.75rem    | 500      | 1.4         | 0.02em         |
| 8     | Overline| 0.75rem    | 600      | 1.4         | 0.08em (uppercase) |

## 4. Spacing & Layout

- **Base unit:** 4px (`0.25rem`)
- **Common spacing:** 8, 12, 16, 20, 24, 32, 48, 64px
- **Max content width:** 1152px (`72rem` / `max-w-6xl`)
- **Card padding:** 24px (`1.5rem`)
- **Section padding:** 80–96px vertical (`py-20 sm:py-24`)
- **Page horizontal padding:** 16px (mobile), 24px (tablet), 32px (desktop)

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
- Border: `1px solid var(--border)` (green-tinted)
- Border radius: `var(--radius-lg)` (0.625rem) for standard cards, `var(--radius-xl)` for featured/CTA cards
- Shadow: `0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06)` (default)
- Padding: 24px
- Hover: subtle shadow increase (`shadow-md`)

### Buttons
- **Default (primary):** `bg-primary` (forest green) — use for navigation, secondary actions
- **Saffron CTA:** `bg-saffron text-saffron-foreground` — use sparingly for main conversion actions
- **Outline:** `border-border bg-background` — secondary alternative actions
- **Ghost:** transparent, hover shows muted background
- **Destructive:** red-tinted, for delete/danger actions
- Consistent height scale: xs(24px), sm(28px), default(32px), lg(36px)
- Border radius: `var(--radius-lg)`

### Feature Cards
- Background: `--background` on `--card` section (or vice versa) for subtle contrast
- Icon container: `size-10 rounded-lg bg-primary/10 text-primary`
- Hover: icon container transitions to `bg-primary text-primary-foreground`
- Shadow: none by default, `shadow-md` on hover

### Inputs
- Height: 40px
- Border: `1px solid var(--input)` (green-tinted)
- Border radius: `var(--radius-md)`
- Focus: `2px ring` using `--ring` color (green)
- Background: white

### Badges / Tags
- Background: `--muted` or `--primary/5`
- Text: `--muted-foreground` or `--primary`
- Border: optional `border-primary/20` for emphasis
- Border radius: full (`9999px`)
- Padding: 4px 12px
- Font size: 0.75rem

## 6. Shadows

| Level   | Value                                                        | Usage                 |
|---------|--------------------------------------------------------------|-----------------------|
| sm      | `0 1px 2px rgba(0, 0, 0, 0.04)`                             | Subtle elements       |
| default | `0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06)` | Cards, dropdowns  |
| md      | `0 4px 12px rgba(0, 0, 0, 0.06)`                            | Elevated cards, hover |
| lg      | `0 8px 24px rgba(0, 0, 0, 0.08)`                            | Dashboard preview, modals |

## 7. Icons

- Library: **Lucide React** (`lucide-react`)
- Default size: 16px (`size-4`) in buttons, 20px (`size-5`) in feature cards
- Stroke width: 2px (default)
- Color: inherit from parent text color, or `text-primary` for emphasis
- Brand icon: `Leaf` from Lucide (used in nav and footer)

## 8. Landing Page Sections

The landing page follows this structure:

| Section       | Background         | Content                              |
|---------------|--------------------|--------------------------------------|
| Navigation    | `card/90` + blur   | Logo, links, CTA button              |
| Hero          | `background`       | Headline, description, CTA, dashboard preview |
| Features      | `card`             | 4 feature cards in 2×2 grid          |
| How It Works  | `background`       | 3 numbered steps                     |
| Benefits      | `card`             | Asymmetric: text left, benefit cards right |
| CTA           | `background`       | Featured card with primary/saffron CTAs |
| Footer        | `card`             | 4-column: brand, platform, resources, legal |

Alternating `background` ↔ `card` creates subtle section separation without heavy borders or backgrounds.

## 9. Accessibility

- All interactive elements must have visible focus indicators (`--ring`, green)
- Minimum contrast ratio: 4.5:1 for normal text, 3:1 for large text
- Primary green (#1B5E3B) on white background: ~7.5:1 contrast ratio ✓
- Saffron (#F59E0B) on dark foreground (#14261C): ~5.2:1 contrast ratio ✓
- All images must have descriptive `alt` attributes
- Form inputs must have associated labels
- Keyboard navigation must be fully supported
- Hover-only states must not hide essential information
