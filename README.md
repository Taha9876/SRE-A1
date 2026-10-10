# SRE Assignment 1: Technical Debt Inventory of Python-Markdown

Group report and supporting analysis for a technical debt inventory of
[Python-Markdown](https://github.com/Python-Markdown/markdown), measured at commit
`0bf535bc406c95dad66050f07c8402af03fe07d5`.

| Member | Roll number |
|---|---|
| Taha Yasir | i222429 |
| Khizar | i222595 |
| Hadeed Abbas | i228780 |

## Contents

| Path | What it is |
|---|---|
| `i222429_i222595_i228780_A1.pdf` / `.docx` | The group report, with each member's scanned handwritten calculations in Appendix A |
| `scans/` | The nine handwritten sheets (three per member) that the report embeds |
| `Manual_Calculation_Worksheets.pdf` / `.docx` | Worked steps for the individual manual calculations |
| `analysis/` | Raw tool outputs (JSON, CSV, text), figures, and the scripts that build the report |

## Headline results

| Metric | Value |
|---|---|
| Size | 8,609 LOC, 4,451 SLOC, 33 modules |
| Cyclomatic complexity | total 1,309, mean 3.3, max 33 |
| Cognitive complexity | total 1,743, max 102 |
| Duplication | 2.38 % |
| Coverage | 98.07 % statement, 93.44 % branch |
| Remediation cost | 93.4 hours |
| Technical Debt Ratio | 4.2 % (rating A) |

## Reproducing

The analysed code is not stored here. Clone it next to `analysis/`:

```
git clone https://github.com/Python-Markdown/markdown.git
git -C markdown checkout 0bf535bc406c95dad66050f07c8402af03fe07d5
```

Tools: Python 3.13 with `radon`, `complexipy`, `coverage`, `pylint`, `bandit`, `flake8`, `vulture`,
`matplotlib`, `python-docx`, `pymupdf`; Node.js for `jscpd`; Microsoft Word for the PDF export.
The exact commands are listed in Appendix B of the report.

Then, from `analysis/`:

```
python summarize.py      # merge tool outputs into summary.json
python deps.py           # import graph
python remediation.py    # remediation cost and debt ratio
python manual_calc.py    # step tables for the manual calculations
python charts.py         # figures
python build_report.py
python build_worksheets.py
powershell -File to_pdf.ps1 -Files ..\i222429_i222595_i228780_A1.docx
python verify_pdf.py
```

`build_report.py` overwrites the `.docx`, so edits made by hand in Word are lost on a rebuild.
