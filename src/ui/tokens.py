"""Shared design tokens for consistent styling across the app."""

# ── Colors ──────────────────────────────────────────────
BG_PRIMARY = "#FFF8F5"
BG_SELECTED = "#FFF0F3"
BG_HOVER_LIGHT = "#FFF5F7"
SURFACE = "#FFFFFF"
BORDER_PRIMARY = "#F0E6E8"
BORDER_SECONDARY = "#e5e7eb"
ACCENT_PURPLE = "#CFA6D6"
ACCENT_BLUSH = "#F7D1DC"
ACCENT_HOVER = "#F3E8F6"
TEXT_PRIMARY = "#2E2B2B"
TEXT_MUTED = "#6B6770"
TEXT_PLACEHOLDER = "#9CA3AF"
SUCCESS = "#7DC68E"
DANGER = "#ef4444"
DANGER_HOVER = "#fef2f2"

# ── Selection ───────────────────────────────────────────
SELECTED_BORDER = "#CFA6D6"
SELECTED_BG = "#F3E8F6"
SELECTED_BORDER_WIDTH = 2

# ── Drag ────────────────────────────────────────────────
DRAG_OPACITY = 0.75

# ── Tooltips ────────────────────────────────────────────
TOOLTIP_STYLE = (
    " QToolTip { background-color: #FFFFFF; color: #2E2B2B;"
    " border: 1px solid #F0E6E8; border-radius: 8px;"
    " padding: 6px 10px; font-size: 12px; }"
)

# ── Button base style ───────────────────────────────────
BTN_BASE = (
    "QToolButton {{ font-size: {font_size}px; border: 1px solid transparent;"
    " border-radius: {radius}px; padding: {pad}px {pad_h}px;"
    " color: {color}; min-width: {min_w}px; }}"
    " QToolButton:hover {{ background: {hover_bg};"
    " border-color: {hover_border}; color: {text_hover}; }}"
    " QToolButton:checked {{ background: {checked_bg};"
    " border-color: {checked_border}; color: {text_hover}; }}"
)

# ── Button presets ──────────────────────────────────────
TOOLBAR_BTN = (
    BTN_BASE.format(
        font_size=13,
        radius=6,
        pad=3,
        pad_h=8,
        min_w=24,
        color=TEXT_MUTED,
        hover_bg=BG_SELECTED,
        hover_border=ACCENT_BLUSH,
        text_hover=TEXT_PRIMARY,
        checked_bg=ACCENT_HOVER,
        checked_border=ACCENT_PURPLE,
    )
    + TOOLTIP_STYLE
)

ALIGNMENT_BTN = (
    BTN_BASE.format(
        font_size=11,
        radius=4,
        pad=2,
        pad_h=4,
        min_w=20,
        color=TEXT_MUTED,
        hover_bg=BG_SELECTED,
        hover_border=ACCENT_PURPLE,
        text_hover=TEXT_PRIMARY,
        checked_bg=ACCENT_HOVER,
        checked_border=ACCENT_PURPLE,
    )
    + TOOLTIP_STYLE
)

HEADER_ACTION_BTN = (
    BTN_BASE.format(
        font_size=11,
        radius=4,
        pad=2,
        pad_h=4,
        min_w=20,
        color=TEXT_MUTED,
        hover_bg=BG_SELECTED,
        hover_border=ACCENT_PURPLE,
        text_hover=TEXT_PRIMARY,
        checked_bg=ACCENT_HOVER,
        checked_border=ACCENT_PURPLE,
    )
    + TOOLTIP_STYLE
)

# ── Block selection style ───────────────────────────────
BLOCK_STYLE = f"""
    #block {{
        border: {1}px solid {BORDER_PRIMARY};
        border-radius: 12px;
        background: {SURFACE};
    }}
    #block:hover {{
        border-color: {ACCENT_BLUSH};
    }}
"""

BLOCK_SELECTED_STYLE = f"""
    #block {{
        border: {SELECTED_BORDER_WIDTH}px solid {SELECTED_BORDER};
        border-radius: 12px;
        background: {SELECTED_BG};
    }}
"""

# ── Empty state ─────────────────────────────────────────
EMPTY_STATE_STYLE = """
    color: #9CA3AF;
    font-size: 14px;
    font-style: italic;
"""
