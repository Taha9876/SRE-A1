"""Sanity checks on the exported report PDF: no blank pages, contents page numbers match the real pages."""
import re
from pathlib import Path

import fitz

ROOT = Path(__file__).parent.parent
doc = fitz.open(ROOT / "i222429_i222595_i228780_A1.pdf")
texts = [p.get_text() for p in doc]
print("report pages:", len(doc), "| nearly empty pages:", [i + 1 for i, t in enumerate(texts) if len(t.strip()) < 120])

entry = re.compile(r"^(\d\. [A-Z][^\n.]+?|Appendix [AB]\. [^\n.]+?|\d\.\d [^\n.]+?)\s*\.{3,}\s*(\d+)\s*$", re.M)
bad = 0
count = 0
for m in entry.finditer(texts[1]):
    count += 1
    title, page = m.group(1).strip(), int(m.group(2))
    if page not in [i + 1 for i, t in enumerate(texts) if i > 1 and title in t]:
        bad += 1
        print("contents mismatch:", title, page)
print("contents entries checked:", count, "| mismatches:", bad)
print("worksheet pages:", len(fitz.open(ROOT / "Manual_Calculation_Worksheets.pdf")))
