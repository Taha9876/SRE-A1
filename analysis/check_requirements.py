"""Check the exported report PDF against each item of the assignment brief (prints page numbers as evidence)."""
import re
from pathlib import Path

import fitz

ROOT = Path(__file__).parent.parent
pages = [p.get_text() for p in fitz.open(ROOT / "i222429_i222595_i228780_A1.pdf")]
flat = [re.sub(r"\s+", " ", t) for t in pages]

CHECKS = [
    ("A1 Repository URL", r"github\.com/Python-Markdown/markdown"),
    ("A1 Commit hash (40 hex)", r"0bf535bc406c95dad66050f07c8402af03fe07d5"),
    ("A1 System description and purpose", r"1\.2 System description and purpose"),
    ("A1 Approximate LOC", r"8,609"),
    ("A1 Module count", r"33 modules"),
    ("A2 Asset list: code", r"Code - core"),
    ("A2 Asset list: libraries", r"Libraries - runtime"),
    ("A2 Asset list: configurations", r"Configuration / build"),
    ("A2 Asset list: tests", r"1,123 test cases"),
    ("A2 Asset list: documentation", r"68 Markdown pages"),
    ("A2 Asset list: UI", r"No graphical UI"),
    ("A2 Classification table: Active", r"2\.2 Classification of assets"),
    ("A2 Classification: Deprecated", r"Deprecated \(legacy\)"),
    ("A2 Classification: Reusable", r"Reusable"),
    ("A2 Quality metrics (per module)", r"2\.3 Quality metrics per module"),
    ("A2 Dependency mapping", r"2\.4 Dependency mapping"),
    ("A2 Dependency figure", r"Figure 1\. Layered view"),
    ("A3 Cyclomatic complexity", r"3\.1 Cyclomatic complexity"),
    ("A3 Cognitive complexity", r"3\.2 Cognitive complexity"),
    ("A3 Code duplication (%)", r"2\.38 %"),
    ("A3 Coverage: statement %", r"98\.07 %"),
    ("A3 Coverage: branch %", r"93\.44 %"),
    ("A3 Bugs", r"Bugs \(confirmed\)"),
    ("A3 Vulnerabilities", r"Vulnerabilities"),
    ("A3 Code smells", r"Code smells"),
    ("A3 Maintainability index", r"3\.6 Maintainability index"),
    ("A4 Mapping weaknesses -> debt types", r"TD-01.*TD-10"),
    ("A4 Example 1: code debt", r"4\.1 Example of code debt"),
    ("A4 Example 2: design debt", r"4\.2 Example of design debt"),
    ("A4 Example 3: test debt", r"4\.3 Example of test debt"),
    ("A4 Example 4: documentation debt", r"4\.4 Example of documentation debt"),
    ("A4 Example 5: infrastructure debt", r"4\.5 Example of infrastructure debt"),
    ("A5 Tool outputs + cost per item", r"5\.2 Tool outputs and cost per item"),
    ("A5 Remediation cost calculation explained", r"Remediation cost = SUM over findings"),
    ("A5 Technical Debt Ratio computed", r"5,605 / 133,530 x 100 = 4\.20 %"),
    ("A5 TDR justification", r"Justification\."),
    ("A6 Technique 1: hotspot analysis", r"6\.1 Technique 1: hotspot analysis"),
    ("A6 Technique 2: weighted scoring model", r"6\.2 Technique 2: weighted scoring model"),
    ("A6 Order justified with evidence", r"6\.3 Prioritised order and justification"),
    ("A7 Lessons learned", r"Lessons learned"),
    ("A7 Trade-offs considered", r"Trade-offs considered"),
    ("A7 Implications for maintenance/evolution", r"Implications for maintenance and evolution"),
    ("B  Appendix per student (3 members)", r"A\.3 Member 3"),
    ("Cover: Taha Yasir i222429", r"Taha Yasir.*i222429"),
    ("Cover: Khizar i222595", r"Khizar.*i222595"),
    ("Cover: Hadeed Abbas i228780", r"Hadeed Abbas.*i228780"),
    ("B  Interpretation file 1", r"Interpretation: extensions/def_list\.py"),
    ("B  Interpretation file 2", r"Interpretation: extensions/meta\.py"),
    ("B  Interpretation file 3", r"Interpretation: extensions/admonition\.py"),
    ("B  Interpretation file 4", r"Interpretation: extensions/wikilinks\.py"),
    ("B  Interpretation file 5", r"Interpretation: postprocessors\.py"),
    ("B  Interpretation file 6", r"Interpretation: extensions/legacy_attrs\.py"),
]

missing = 0
for label, pattern in CHECKS:
    hits = [i + 1 for i, t in enumerate(flat) if i != 1 and re.search(pattern, t)]   # page 2 is the contents list
    missing += not hits
    print(f'{"OK " if hits else "MISSING"}  {label:45} page(s) {hits}')
print(f"\n{len(CHECKS) - missing} of {len(CHECKS)} report items found")

print("\nPlaceholders still in the report:")
for ph in ("[Member 3 name]", "[Roll No.", "[Section]", "[Instructor]", "[Date]", "scanned handwritten calculation sheets after"):
    print(f"   {ph:48} on page(s)", [i + 1 for i, t in enumerate(flat) if ph in t and i != 1])

import json
M = json.loads((Path(__file__).parent / "manual_calc.json").read_text(encoding="utf-8"))
print("\nIndividual files (need 50+ LOC each, non-trivial):")
for d in M:
    print(f'   {d["file"]:38} lines={d["total_lines"]:4} code={d["counts"]["code"]:3} '
          f'maxCC={d["cc_max"]:2} maxCog={d["cog_max"]:2}')
