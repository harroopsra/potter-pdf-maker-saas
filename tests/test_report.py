from pathlib import Path

from pypdf import PdfReader

from report import HOUSE_QUOTES, build_report, quotes_for

GRYFFINDOR = {
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


def extract_text(path: Path) -> str:
    return PdfReader(path).pages[0].extract_text()


def test_report_contains_all_house_details(tmp_path):
    out = tmp_path / "report.pdf"
    build_report(
        GRYFFINDOR,
        out,
        quote=("A test quote.", "The Sorting Hat"),
        sorted_on="01 January 2026",
    )

    text = extract_text(out)
    assert "GRYFFINDOR" in text
    assert "Godric Gryffindor" in text
    assert "Scarlet and gold" in text
    assert "House of the Lion" in text
    assert "Gryffindor Tower" in text
    assert "Nearly-Headless Nick" in text
    assert "A test quote." in text
    assert "— The Sorting Hat" in text
    assert "Sorted on 01 January 2026" in text


def test_report_fixes_known_trait_typo(tmp_path):
    out = tmp_path / "report.pdf"
    build_report(GRYFFINDOR, out, quote=("", ""), sorted_on="01 January 2026")

    text = extract_text(out)
    assert "Chivalry" in text
    assert "Chivalary" not in text


def test_report_is_single_page(tmp_path):
    out = tmp_path / "report.pdf"
    build_report(GRYFFINDOR, out)

    assert len(PdfReader(out).pages) == 1


def test_report_handles_unknown_house(tmp_path):
    out = tmp_path / "report.pdf"
    build_report({"name": "Unknown House"}, out)

    text = extract_text(out)
    assert "UNKNOWN HOUSE" in text


def test_every_house_has_a_sorting_hat_quote():
    for house_name in HOUSE_QUOTES:
        first_quote, author = quotes_for(house_name)[0]
        assert author == "The Sorting Hat"
        assert first_quote


def test_unknown_house_still_gets_general_quotes():
    options = quotes_for("Unknown House")
    assert options  # falls back to the general lore quotes
