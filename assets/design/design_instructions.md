# Design Instructions — Personal Productivity App

Purpose
- A concise, implementable UI spec for a simple, elegant, contemporary "clean-girl" aesthetic on Desktop & Tablet.
- Priorities: calm feminine palette, refined typography, generous whitespace, soft shapes, and accessible touch-friendly controls.

Visual Tokens
- Colors:
  - Primary Blush: #F7D1DC
  - Accent Mauve: #CFA6D6
  - Warm Peach: #FFD8C2
  - Gold Accent: #D4A373
  - Surface/Card: #FFFFFF
  - Background: #FFF8F5
  - Text Primary: #2E2B2B
  - Text Muted: #6B6770
  - Success: #7DC68E
- Gradients:
  - Subtle background: linear from #FFF8F5 ? #FFF3F8
  - Card accent: linear from #CFA6D6 ? #F7D1DC
- Spacing & Size:
  - Baseline: 4px; small 8, base 16, medium 24, large 32, xl 48
  - Corner radius: 12px (cards), 20px (panels)
  - Hit target: min 44×44px (touch)
- Shadows & Motion:
  - Shadow: rgba(46,43,43,0.06) 0px 6px 18px
  - Motion: 150–220ms ease-out; entrance = fade + translateY(-6px)

Typography
- Primary face: Inter or Poppins; Headings optionally Playfair Display for elegance
- Weights: Headings 600, Body 400
- Sizes: H1 24–28, H2 20, H3 16–18, Body 14–15, Small 12

Layout & Core Structure
- Two-pane primary layout:
  - Left: Sidebar tree (navigation) — width default 280px, collapsed 72px
  - Right: Editor area — centered content column max width 960px on wide screens
- Tablet: Sidebar overlays or collapses by default; editor becomes primary focus; toolbar sticky/top-floating
- Top header: slim bar with app name, quick-add, search, profile/settings
- Footer: small status row (auto-save, sync)

Component Specs
- Sidebar (Page Tree):
  - White card on soft background; rounded corners; subtle inner padding
  - Active page: mauve highlight + 4px left accent
  - Nested indentation, subtle dividers, drag handle for reordering
  - Controls: + New Page (top), context menu (rename/delete), multi-select support
- Editor:
  - Editor container: white card, comfortable padding, rounded corners
  - Toolbar: primary formatting controls (B/I/H1/H2/list/code/table/template), undo/redo, save
  - Content blocks: card-like rows with left drag handle, inline actions on hover, focused elevation + subtle outline
  - Tables: alternating soft row backgrounds, editable inline cells
  - Lists/checkboxes: large check hit-area, checked state dims content + shows green success accent
- Floating Action:
  - Rounded FAB (gold accent) for templates/new page; subtle shadow; accessible in both views
- Modals & Dialogs:
  - Centered cards with blurred/backdrop, primary action colored (mauve/gold), cancel as outline
- Buttons & Inputs:
  - Primary: filled blush/mauve pill with white text
  - Secondary: mauve outline
  - Input fields: rounded, soft inner shadow, clear labels

Interactions & Microinteractions
- Hover/focus: 150ms subtle scale/shadow
- Dragging: lift + shadow, placeholder drop line
- Checkbox toggles: quick check animation + green fade for completion
- Auto-save: small toast or status dot that pulses on save
- Templates insertion: modal grid with preview cards

Touch & Tablet Behavior
- Long-press to drag blocks; swipe left on page rows to reveal quick actions (rename/delete)
- Toolbar buttons spaced for thumbs; toolbar can float near selection on large tablets
- Ensure hit targets >= 44×44px

Accessibility
- Text contrast >= 4.5:1 where practical; use darker text on light surfaces
- Keyboard navigation: focusable sidebar, block-level focus, visible focus outlines
- Screen reader: semantic headings, roles on tree and editor blocks, labels for dialogs

Implementation Notes (PyQt6)
- Layout: use `QSplitter` for sidebar/editor; `QTreeView`/`QTreeWidget` for pages; custom `QWidget` for block rows
- Styling: leverage QSS for colors, radii, and shadows; use SVG icons for crisp scaling
- Editor: `QPlainTextEdit` for raw Markdown with a side renderer using `QTextDocument` or a lightweight embedded Markdown renderer widget; consider using split editing/rendering or inline rich rendering per block
- Touch: enable touch attributes (e.g., `Qt.WA_AcceptTouchEvents`) and implement long-press via timers; increase `QWidget` minimum size for touch targets
- Templates: persist JSON snapshots in `templates` table; insertion = deserialize to blocks and append
- Auto-save: debounce changes (e.g., 800–1200ms) and show transient saved indicator
- Performance: lazy-render long pages; virtualize lists if necessary; debounce heavy tasks

Assets & Deliverables
- Deliverables for UI handoff:
  - `design_instructions.md` (this file)
  - Token JSON: colors, spacing, typography
  - SVG icon set (thin-line + filled active variants)
  - Optional: 1–2 PNG/SVG mockups (sidebar+editor) — I can provide these
- Suggested file: `ui/tokens.json` containing color, radius, spacing keys for quick import

Acceptance Criteria
- Layout implemented: resizable/collapsible sidebar + editor card
- Editor supports block-level editing, drag handles, inline formatting controls
- Color tokens applied consistently and match palette
- Tablet-specific gestures and hit targets work and tested
- Keyboard navigation, focus visibility, and ARIA-equivalent labeling present

Next Steps
1. Confirm tokens and typography (choose Inter/Poppins + optional Playfair for headings).
2. I can generate `ui/tokens.json` and 1–2 small mockup PNG/SVG files ready to drop in `assets/` — want that now?
