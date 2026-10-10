"""The scanned handwritten sheets (in reading order) that both documents embed."""
from pathlib import Path

SCANS = Path(__file__).parent.parent / "scans"

SCAN_PAGES = {
    "Member 1": [("taha_1_def_list.jpg", "def_list.py: comment density, cyclomatic and cognitive complexity"),
                 ("taha_2_meta.jpg", "def_list.py summary; meta.py: comment density and cyclomatic complexity"),
                 ("taha_3_meta_cognitive.jpg", "meta.py: cognitive complexity and summary")],
    "Member 2": [("khizar_1_admonition.jpg", "admonition.py: comment density, cyclomatic and cognitive complexity"),
                 ("khizar_2_wikilinks.jpg", "admonition.py summary; wikilinks.py: comment density and cyclomatic "
                                            "complexity"),
                 ("khizar_3_wikilinks_cognitive.jpg", "wikilinks.py: cognitive complexity and summary")],
    "Member 3": [("hadeed_1_postprocessors.jpg", "postprocessors.py: comment density and cyclomatic complexity"),
                 ("hadeed_2_legacy_attrs.jpg", "postprocessors.py cognitive complexity and summary; legacy_attrs.py: "
                                               "comment density"),
                 ("hadeed_3_legacy_attrs_cognitive.jpg", "legacy_attrs.py: cyclomatic and cognitive complexity, "
                                                         "summary")],
}


def pages_for(label):
    """(path, caption) pairs for one member, skipping files that are not present."""
    return [(SCANS / f, c) for f, c in SCAN_PAGES[label] if (SCANS / f).exists()]
