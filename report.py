"""Render the sorting report PDF: crest, house banner, details, and a quote.

The crest is drawn as vector art at fixed page coordinates so it appears in
exactly the same place on every PDF. To use your own artwork instead, drop an
image at assets/hogwarts_logo.png (any format fpdf2 supports); it replaces the
vector crest in the same position. Only use artwork you have the rights to.
"""

from datetime import date
from pathlib import Path
from typing import Optional, Sequence, Tuple

from fpdf import FPDF

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
LOGO_PATH = ASSETS_DIR / "hogwarts_logo.png"

# Page geometry (A4 portrait, 210 x 297 mm). The crest position is a constant
# so it is identical on every report.
PAGE_W = 210
CX = PAGE_W / 2
CREST_TOP = 20
CREST_HALF_W = 14
CREST_RECT_H = 22
CREST_POINT_H = 34
CREST_BANNER_TOP = CREST_TOP + 36

HOUSE_COLOURS = {
    "Gryffindor": {
        "primary": (116, 0, 1),
        "secondary": (211, 166, 65),
        "on_primary": (255, 255, 255),
    },
    "Slytherin": {
        "primary": (26, 71, 42),
        "secondary": (170, 170, 170),
        "on_primary": (255, 255, 255),
    },
    "Hufflepuff": {
        "primary": (236, 185, 57),
        "secondary": (55, 46, 41),
        "on_primary": (55, 46, 41),
    },
    "Ravenclaw": {
        "primary": (14, 26, 64),
        "secondary": (148, 107, 45),
        "on_primary": (255, 255, 255),
    },
}
DEFAULT_COLOURS = {
    "primary": (60, 60, 60),
    "secondary": (180, 150, 60),
    "on_primary": (255, 255, 255),
}

# The Wizard World API has a typo in one trait name.
TRAIT_NAME_FIXES = {"Chivalary": "Chivalry"}

HOUSE_QUOTES = {
    "Gryffindor": [
        (
            "You might belong in Gryffindor, where dwell the brave at heart, "
            "their daring, nerve and chivalry set Gryffindors apart.",
            "The Sorting Hat",
        )
    ],
    "Hufflepuff": [
        (
            "You might belong in Hufflepuff, where they are just and loyal, "
            "those patient Hufflepuffs are true and unafraid of toil.",
            "The Sorting Hat",
        )
    ],
    "Ravenclaw": [
        (
            "Or yet in wise old Ravenclaw, if you've a ready mind, "
            "where those of wit and learning will always find their kind.",
            "The Sorting Hat",
        )
    ],
    "Slytherin": [
        (
            "Or perhaps in Slytherin you'll make your real friends, "
            "those cunning folk use any means to achieve their ends.",
            "The Sorting Hat",
        )
    ],
}

GENERAL_QUOTES = [
    (
        "It is our choices, Harry, that show what we truly are, "
        "far more than our abilities.",
        "Albus Dumbledore",
    ),
    (
        "Happiness can be found even in the darkest of times, "
        "if one only remembers to turn on the light.",
        "Albus Dumbledore",
    ),
    ("It does not do to dwell on dreams and forget to live.", "Albus Dumbledore"),
]


def quotes_for(house_name: str) -> Sequence[Tuple[str, str]]:
    """Quotes that fit a house: its Sorting Hat verse first, then general lore."""
    return HOUSE_QUOTES.get(house_name, []) + GENERAL_QUOTES


def _draw_crest(pdf: FPDF) -> None:
    y0 = CREST_TOP
    half_w, rect_h, point_h = CREST_HALF_W, CREST_RECT_H, CREST_POINT_H

    if LOGO_PATH.is_file():
        pdf.image(str(LOGO_PATH), x=CX - half_w, y=y0, w=half_w * 2)
        return

    # Four house colours quarterly, like a school crest.
    quadrants = [
        (
            [(CX - half_w, y0), (CX, y0), (CX, y0 + rect_h), (CX - half_w, y0 + rect_h)],
            (116, 0, 1),
        ),
        (
            [(CX, y0), (CX + half_w, y0), (CX + half_w, y0 + rect_h), (CX, y0 + rect_h)],
            (26, 71, 42),
        ),
        ([(CX - half_w, y0 + rect_h), (CX, y0 + rect_h), (CX, y0 + point_h)], (236, 185, 57)),
        ([(CX + half_w, y0 + rect_h), (CX, y0 + rect_h), (CX, y0 + point_h)], (14, 26, 64)),
    ]
    for points, colour in quadrants:
        pdf.set_fill_color(*colour)
        pdf.polygon(points, style="F")

    # Shield outline.
    pdf.set_draw_color(120, 90, 30)
    pdf.set_line_width(0.7)
    shield = [
        (CX - half_w, y0),
        (CX + half_w, y0),
        (CX + half_w, y0 + rect_h),
        (CX, y0 + point_h),
        (CX - half_w, y0 + rect_h),
    ]
    pdf.polygon(shield, style="D")

    # Roundel with the school initial.
    pdf.set_fill_color(255, 255, 255)
    pdf.ellipse(CX - 7, y0 + 7, 14, 14, style="F")
    pdf.set_draw_color(120, 90, 30)
    pdf.set_line_width(0.3)
    pdf.ellipse(CX - 7, y0 + 7, 14, 14, style="D")
    pdf.set_text_color(14, 26, 64)
    pdf.set_font("Times", "B", 15)
    pdf.set_xy(0, y0 + 8.5)
    pdf.cell(PAGE_W, 11, "H", align="C")

    # Banner.
    pdf.set_fill_color(120, 90, 30)
    pdf.rect(CX - 16, CREST_BANNER_TOP, 32, 6, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 6)
    pdf.set_xy(0, CREST_BANNER_TOP + 1.2)
    pdf.cell(PAGE_W, 4, "HOGWARTS", align="C")


def build_report(
    house: dict,
    output_path: Path,
    quote: Optional[Tuple[str, str]] = None,
    sorted_on: Optional[str] = None,
) -> Path:
    """Write the sorting report for `house` to `output_path` and return it."""
    name = house.get("name", "Unknown House")
    colours = HOUSE_COLOURS.get(name, DEFAULT_COLOURS)
    primary, secondary, on_primary = colours["primary"], colours["secondary"], colours["on_primary"]

    raw_traits = [t["name"] if isinstance(t, dict) else t for t in house.get("traits", [])]
    traits = [TRAIT_NAME_FIXES.get(t, t) for t in raw_traits]
    if quote is None:
        options = quotes_for(name)
        quote = options[0] if options else ("", "")
    quote_text, quote_author = quote
    if sorted_on is None:
        sorted_on = date.today().strftime("%d %B %Y")

    pdf = FPDF(format="A4", unit="mm")
    # Core fonts default to latin-1; cp1252 adds typographic dashes (—).
    pdf.core_fonts_encoding = "cp1252"
    pdf.set_auto_page_break(False)
    pdf.set_title(f"{name} — Sorting Report")
    pdf.set_author("potter-pdf-maker-saas")
    pdf.add_page()

    # Explicit white background so every renderer agrees.
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(0, 0, PAGE_W, 297, style="F")

    # Certificate frame.
    pdf.set_draw_color(120, 90, 30)
    pdf.set_line_width(0.8)
    pdf.rect(8, 8, 194, 281)
    pdf.set_line_width(0.2)
    pdf.rect(11, 11, 188, 275)

    _draw_crest(pdf)

    # Letterhead.
    pdf.set_text_color(40, 40, 40)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_xy(0, 66)
    pdf.cell(PAGE_W, 5, "HOGWARTS SCHOOL OF WITCHCRAFT AND WIZARDRY", align="C")
    pdf.set_font("Times", "I", 11)
    pdf.set_xy(0, 72)
    pdf.cell(PAGE_W, 5, "The Sorting Hat has sorted you into", align="C")

    # House banner.
    pdf.set_fill_color(*primary)
    pdf.rect(25, 80, 160, 24, style="F")
    pdf.set_text_color(*on_primary)
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_xy(0, 85.5)
    pdf.cell(PAGE_W, 13, name.upper(), align="C")

    # House colour swatches.
    pdf.set_fill_color(*primary)
    pdf.rect(CX - 6.5, 110, 6, 6, style="F")
    pdf.set_fill_color(*secondary)
    pdf.rect(CX + 0.5, 110, 6, 6, style="F")

    pdf.set_text_color(40, 40, 40)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(0, 118)
    pdf.cell(PAGE_W, 5, f"House colours: {house.get('houseColours', 'unknown')}", align="C")

    # Details.
    details = [
        f"Founder — {house['founder']}" if house.get("founder") else "",
        f"House of the {house['animal']} — Element: {house['element']}"
        if house.get("animal") and house.get("element")
        else "",
        f"Common room — {house['commonRoom']}" if house.get("commonRoom") else "",
        f"House ghost — {house['ghost']}" if house.get("ghost") else "",
    ]
    y = 125
    for line in details:
        if line:
            pdf.set_xy(0, y)
            pdf.cell(PAGE_W, 5, line, align="C")
            y += 6

    if traits:
        pdf.set_text_color(90, 70, 30)
        pdf.set_font("Times", "I", 11)
        pdf.set_xy(0, y + 2)
        pdf.cell(PAGE_W, 6, "  ·  ".join(traits), align="C")

    # Quote box, with quote and attribution centred as one block.
    box_top, box_h = 165, 50
    pdf.set_draw_color(*secondary)
    pdf.set_line_width(0.6)
    pdf.rect(30, box_top, 150, box_h)
    if quote_text:
        pdf.set_text_color(40, 40, 40)
        pdf.set_font("Times", "I", 13)
        quote_h = pdf.multi_cell(134, 6.5, quote_text, align="C", dry_run=True, output="HEIGHT")
        block_h = quote_h + (6 if quote_author else 0)
        y = box_top + (box_h - block_h) / 2
        pdf.set_xy(38, y)
        pdf.multi_cell(134, 6.5, quote_text, align="C")
        if quote_author:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(90, 90, 90)
            pdf.set_xy(0, y + quote_h + 1)
            pdf.cell(PAGE_W, 5, f"— {quote_author}", align="C")

    # Ornament rules to balance the lower page.
    pdf.set_draw_color(*secondary)
    pdf.set_line_width(0.4)
    pdf.line(85, 238, 125, 238)
    pdf.line(85, 240, 125, 240)

    # Footer.
    pdf.set_text_color(40, 40, 40)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(0, 262)
    pdf.cell(PAGE_W, 5, f"Sorted on {sorted_on}", align="C")
    pdf.set_text_color(150, 150, 150)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(0, 268.5)
    pdf.cell(PAGE_W, 4, "Generated by potter-pdf-maker-saas", align="C")

    pdf.output(str(output_path))
    return output_path
