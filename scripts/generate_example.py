"""Regenerate examples/example_output.pdf with the real report builder."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from report import build_report  # noqa: E402

EXAMPLE_HOUSE = {
    "name": "Gryffindor",
    "houseColours": "Scarlet and gold",
    "founder": "Godric Gryffindor",
    "animal": "Lion",
    "element": "Fire",
    "ghost": "Nearly-Headless Nick",
    "commonRoom": "Gryffindor Tower",
    "traits": [
        {"name": "Courage"},
        {"name": "Chivalary"},
        {"name": "Determination"},
        {"name": "Bravery"},
    ],
}

if __name__ == "__main__":
    output = Path(__file__).resolve().parent.parent / "examples" / "example_output.pdf"
    build_report(
        EXAMPLE_HOUSE,
        output,
        quote=(
            "You might belong in Gryffindor, where dwell the brave at heart, "
            "their daring, nerve and chivalry set Gryffindors apart.",
            "The Sorting Hat",
        ),
    )
    print(f"wrote {output}")
