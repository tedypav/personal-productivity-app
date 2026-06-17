"""Seed data for fun pre-populated pages."""

import json

from src.models.page import Page
from src.models.page_object import PageObject
from src.repositories.page_object_repo import PageObjectRepo
from src.repositories.page_repo import PageRepo


def _checkbox(page_id: int, text: str, sort_order: int) -> PageObject:
    return PageObject(
        page_id=page_id,
        object_type="checkbox",
        content=json.dumps({"text": text, "checked": False}),
        sort_order=sort_order,
    )


def _create_world_domination_page() -> int:
    """Create the World Domination Plan page with all its content blocks."""
    page_id = PageRepo().create(Page(title="World Domination Plan"))

    intro_text = (
        '<h2 style="text-align:center;">'
        "My Plan for World Domination</h2>"
        "<p><b>Phase 1:</b> Acquire cat. Cats are natural leaders.</p>"
        "<p><b>Phase 2:</b> ???</p>"
        "<p><b>Phase 3:</b> World domination (and maybe snacks).</p>"
    )

    reflection_text = (
        '<p style="color:#888;"><i>Today I realized I accidentally '
        'sent my "evil plan" draft to the group chat. '
        "Nobody responded. This is either a good sign "
        "or I need new minions.</i></p>"
    )

    objects = [
        # --- Widget 0: Title textbox (top center) ---
        PageObject(
            page_id=page_id,
            object_type="textbox_meta",
            content=json.dumps(
                {
                    "x": 200,
                    "y": 30,
                    "width": 500,
                    "height": 130,
                    "title": "The Master Plan",
                    "blocks": [{"type": "text", "content": intro_text}],
                }
            ),
            sort_order=50,
        ),
        # --- Widget 1: Daily Goals checklist (left side) ---
        PageObject(
            page_id=page_id,
            object_type="checklist_meta",
            content=json.dumps(
                {
                    "x": 50,
                    "y": 200,
                    "width": 360,
                    "height": 280,
                    "title": "Daily Domination Goals",
                }
            ),
            sort_order=150,
        ),
        _checkbox(
            page_id,
            "Practice evil laugh in mirror (10 min)",
            100,
        ),
        _checkbox(
            page_id,
            "Feed the cat (keep allies happy)",
            101,
        ),
        _checkbox(
            page_id,
            "Post mysterious Instagram story",
            102,
        ),
        _checkbox(
            page_id,
            "Send passive-aggressive emails to coworkers",
            103,
        ),
        _checkbox(
            page_id,
            'Research "how to build a secret lair" on Pinterest',
            104,
        ),
        _checkbox(
            page_id,
            "Rehearse dramatic cape swirling",
            105,
        ),
        # --- Widget 2: Reflection textbox (right side) ---
        PageObject(
            page_id=page_id,
            object_type="textbox_meta",
            content=json.dumps(
                {
                    "x": 450,
                    "y": 200,
                    "width": 400,
                    "height": 280,
                    "title": "Reflections & Revelations",
                    "blocks": [
                        {
                            "type": "text",
                            "content": reflection_text,
                        }
                    ],
                }
            ),
            sort_order=250,
        ),
        # --- Widget 3: Strategic Planning table (bottom) ---
        PageObject(
            page_id=page_id,
            object_type="table_meta",
            content=json.dumps(
                {
                    "x": 80,
                    "y": 510,
                    "width": 620,
                    "height": 220,
                    "title": ("Strategic Planning: " "Countries & Resources"),
                    "headers": [
                        "Target",
                        "Strategy",
                        "Resources Needed",
                        "Status",
                        "ETA",
                    ],
                    "data": [
                        [
                            "Luxembourg",
                            "Bribe with pastries",
                            "500 croissants, " "one charming smile",
                            "In Progress",
                            "Friday",
                        ],
                        [
                            "The Internet",
                            "Post cute cat videos",
                            "10 cats, ring light, Wi-Fi",
                            "Pending",
                            "TBD (cats are unreliable)",
                        ],
                        [
                            "Antarctica",
                            "Exploit penguin loyalty",
                            "Winter coat, fish supply, " "diplomacy",
                            "Planned",
                            "Winter 2027",
                        ],
                    ],
                    "show_row_numbers": False,
                }
            ),
            sort_order=350,
        ),
    ]

    for obj in objects:
        PageObjectRepo().create(obj)

    return page_id


def create_fun_pages():
    """Create fun seed pages if they don't already exist."""
    existing = {p.title for p in PageRepo().get_all()}
    if "World Domination Plan" not in existing:
        _create_world_domination_page()
