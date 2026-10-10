"""Build the group report (.docx) from the analysis outputs in this folder."""
import json
from pathlib import Path

from docx_helpers import (ACCENT, MUTED, add_footer, add_toc, bullets, code, figure, hyperlink, link_cell,
                          new_document, page_break, para, table)

HERE = Path(__file__).parent
OUT = HERE.parent / "i222429_i222595_i228780_A1.docx"
S = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
D = json.loads((HERE / "deps.json").read_text(encoding="utf-8"))
R = json.loads((HERE / "remediation.json").read_text(encoding="utf-8"))
M = json.loads((HERE / "manual_calc.json").read_text(encoding="utf-8"))
CPX = json.loads((HERE / "complexipy.json").read_text(encoding="utf-8"))
CC = json.loads((HERE / "radon_cc.json").read_text(encoding="utf-8"))

COMMIT = "0bf535bc406c95dad66050f07c8402af03fe07d5"
GROUP_REPO = "https://github.com/Taha9876/SRE-A1"
size, cc, cog, mi, cov, dup = S["size"], S["cc"], S["cognitive"], S["mi"], S["coverage"], S["duplication"]
files = S["per_file"]
core = [r for r in files if "/extensions/" not in r["file"]]
ext = [r for r in files if "/extensions/" in r["file"]]


def n(x):
    return f"{x:,}"


def short(f):
    return f.replace("markdown/", "", 1)


doc = new_document()
add_footer(doc, "SRE Assignment 1 - Technical Debt Inventory of Python-Markdown    |    github.com/Taha9876/SRE-A1")

# =================================================================== cover
for _ in range(5):
    doc.add_paragraph()
para(doc, "SRE - Assignment 1", size=13, align="center", color=MUTED, after=4)
para(doc, "**Technical Debt Inventory and Analysis**", size=26, align="center", color=ACCENT, after=2)
para(doc, "of the Python-Markdown code base", size=16, align="center", after=30)
para(doc, "Group Report", size=13, align="center", after=40)
table(doc, ["#", "Group member", "Roll number", "Individual files (Appendix A)"],
      [["1", "Taha Yasir", "i222429", "`extensions/def_list.py`, `extensions/meta.py`"],
       ["2", "Khizar", "i222595", "`extensions/admonition.py`, `extensions/wikilinks.py`"],
       ["3", "Hadeed Abbas", "i228780", "`postprocessors.py`, `extensions/legacy_attrs.py`"]],
      [1.0, 5.0, 3.5, 7.5], size=10, align="clll")
p = para(doc, "Report, analysis scripts and raw tool outputs:  ", size=10.5, align="center", before=20, color=MUTED)
hyperlink(p, GROUP_REPO, size=10.5)
page_break(doc)

para(doc, "**Contents**", size=16, color=ACCENT, after=8)
add_toc(doc)

# =================================================================== 1
doc.add_heading("1. Project Overview", level=1).paragraph_format.page_break_before = True
doc.add_heading("1.1 Repository and version analysed", level=2)
t = table(doc, ["Item", "Value"],
          [["Project", "Python-Markdown (PyPI package `Markdown`)"],
           ["Repository URL", "https://github.com/Python-Markdown/markdown"],
           ["Commit hash", f"`{COMMIT}`"],
           ["Commit position", "9 October 2026, branch `master`, 7 commits after release 3.11.0"],
           ["Language / licence", "Python (`requires-python >= 3.11`), BSD 3-Clause"],
           ["History", "Since March 2006; 1,672 commits, 191 contributors, 44 commits in the last 12 months"],
           ["Our analysis repository", GROUP_REPO]],
          [4.2, 12.8], size=9.5, bold_first_col=True)
link_cell(t, 2, 1, "https://github.com/Python-Markdown/markdown")
link_cell(t, 7, 1, GROUP_REPO)

doc.add_heading("1.2 System description and purpose", level=2)
para(doc, "Python-Markdown converts Markdown text to HTML. It is used as a library, as the `markdown_py` command, "
          "and as the rendering engine of documentation tools such as MkDocs.", align="justify")
para(doc, "It is a five-stage pipeline run by the `Markdown` class: **preprocessors** clean the lines, the **block "
          "parser** builds an element tree, **tree processors** apply the **inline patterns**, a **serializer** "
          "writes HTML, and **postprocessors** restore stashed fragments. An extension API lets plug-ins add "
          "processors to any stage; 18 extensions ship with the package.", align="justify")

doc.add_heading("1.3 Size and module count", level=2)
para(doc, "Business logic is the installable package `markdown/`. Tests, documentation and build files are not counted.")
table(doc, ["Measure (radon raw)", "Core (14 modules)", "Extensions (19 modules)", "Package total"],
      [["Physical lines of code (LOC)", n(sum(r["loc"] for r in core)), n(sum(r["loc"] for r in ext)), n(size["loc"])],
       ["Source lines (SLOC: no blanks, comments, docstrings)", n(sum(r["sloc"] for r in core)),
        n(sum(r["sloc"] for r in ext)), n(size["sloc"])],
       ["Functions and methods", str(sum(r["funcs"] for r in core)), str(sum(r["funcs"] for r in ext)), str(cc["blocks"])],
       ["Classes", "63", "48", str(cc["classes"])]],
      [7.4, 3.1, 3.5, 3.0], size=9.5, align="lrrr")
table(doc, ["Selection criterion", "Requirement", "Python-Markdown", "Met"],
      [["Size", "5,000 - 12,000 LOC", f"{n(size['loc'])} LOC ({n(size['sloc'])} SLOC)", "Yes"],
       ["Structure", "At least 10 classes / modules", f"{S['files']} modules, {cc['classes']} classes", "Yes"],
       ["Complexity", "Non-trivial decision logic", f"{cc['over_10']} functions with cyclomatic complexity above 10; "
                                                    f"maximum {cc['max']}", "Yes"],
       ["Language", "Java, Python, C#, C++ or React", "Python 3", "Yes"]],
      [3.0, 5.0, 7.6, 1.4], size=9.5, align="lllc")

# =================================================================== 2
doc.add_heading("2. Inventory Analysis", level=1)
doc.add_heading("2.1 Project assets", level=2)
table(doc, ["Asset type", "Location", "Size", "Content"],
      [["Code - core", "`markdown/*.py`", f"14 modules, {n(sum(r['loc'] for r in core))} LOC",
        "Pipeline engine, HTML parser, serializers, `util`, CLI"],
       ["Code - extensions", "`markdown/extensions/`", f"19 modules, {n(sum(r['loc'] for r in ext))} LOC",
        "`Extension` base class and 18 plug-ins"],
       ["Tests", "`tests/`", "37 files, 14,667 LOC, 1,123 test cases", "`unittest` suites plus 300 fixture files"],
       ["Libraries - runtime", "`pyproject.toml`", "0 mandatory, 2 optional",
        "Standard library only; optional Pygments and PyYAML"],
       ["Libraries - development", "`pyproject.toml`, `tox.ini`", "3 test, 8 documentation",
        "`coverage`, `pyyaml`, `pytidylib`; pinned docs tool chain"],
       ["Configuration / build", "repository root", "11 files",
        "`pyproject.toml`, `tox.ini`, `makefile`, `.coveragerc`, `mkdocs.yml`, `uv.lock` and others"],
       ["CI / process", "`.github/`", "6 workflows", "Test matrix, changelog checks, docs deploy"],
       ["Documentation", "`docs/`, root `*.md`", "68 Markdown pages", "User guide, extension reference, API guide, "
                                                                     "changelog"],
       ["UI", "`markdown/__main__.py`", "1 CLI module, 154 LOC", "No graphical UI; command line `markdown_py` only"]],
      [3.2, 3.6, 4.0, 6.2], size=8.5, bold_first_col=True)

doc.add_heading("2.2 Classification of assets", level=2)
table(doc, ["Asset", "Class", "Evidence"],
      [["`core.py`, `__init__.py`, `__meta__.py`, `__main__.py`", "Active", "Entry points and orchestrator"],
       ["`blockparser.py`, `blockprocessors.py`, `inlinepatterns.py`, `treeprocessors.py`, `preprocessors.py`, "
        "`htmlparser.py`", "Active", "Default conversion path; touched by 31 of the 71 commits of the last three years"],
       ["`postprocessors.py`", "Active (part deprecated)", "`UnescapePostprocessor` is marked `@deprecated`"],
       ["`util.py`", "Reusable", "Generic `Registry` and helpers; imported by 16 modules"],
       ["`extensions/__init__.py`", "Reusable", "`Extension` base class; imported by 20 modules"],
       ["`serializers.py`", "Reusable", "Generic ElementTree-to-HTML writer with no internal dependency"],
       ["`test_tools.py`", "Reusable", "`TestCase` helpers published for third-party extension authors"],
       ["16 extensions (`abbr`, `admonition`, `attr_list`, `codehilite`, `def_list`, `extra`, `fenced_code`, "
        "`footnotes`, `md_in_html`, `meta`, `nl2br`, `sane_lists`, `smarty`, `tables`, `toc`, `wikilinks`)", "Active",
        "Registered entry points; documented and tested"],
       ["`extensions/legacy_attrs.py`, `extensions/legacy_em.py`", "Deprecated (legacy)",
        "Kept only for documents written before version 3.0"],
       ["`AbbrPreprocessor`, `AbbrInlineProcessor`, `toc.get_name`, `toc.stashedHTML2text`, `attr_list.get_attrs`, "
        "`Markdown.docType`", "Deprecated", "`@deprecated` decorator or a TODO marking it unused"],
       ["`tests/test_legacy.py` and its 300 fixture files", "Deprecated (legacy)", "Older file-comparison tests"],
       ["Other tests, documentation, CI, build configuration", "Active", "Maintained with each release"]],
      [8.0, 3.0, 6.0], size=8.5)

doc.add_heading("2.3 Quality metrics per module", level=2)
para(doc, "CC = cyclomatic (radon); Cog = cognitive (complexipy); MI = maintainability index; Dup = duplicated lines "
          "(jscpd); Churn = commits in the last three years.", size=9.5)
rows = []
for r in files:
    rows.append([short(r["file"]), r["loc"], r["sloc"], r["funcs"], r["cc_sum"], r["cc_max"], r["cog_max"],
                 f'{r["mi"]:.1f}', f'{r["cov_stmt"]:.1f}', f'{r["cov_branch"]:.1f}', r["dup_lines"], r["churn_3y"]])
rows.append(["Package total / worst", n(size["loc"]), n(size["sloc"]), cc["blocks"], n(cc["total"]), cc["max"],
             cog["max"], f'{mi["min"]:.1f}', f'{cov["statement_pct"]:.1f}', f'{cov["branch_pct"]:.1f}',
             dup["duplicated_lines"], S["git"]["commits_3y_touching_pkg"]])
table(doc, ["Module", "LOC", "SLOC", "Fn", "CC sum", "CC max", "Cog max", "MI", "Stmt %", "Branch %", "Dup", "Churn"],
      rows, [4.3, 1.1, 1.1, 0.9, 1.2, 1.2, 1.3, 1.1, 1.2, 1.4, 1.0, 1.2], size=7.8, align="l" + "r" * 11,
      total_row=True, mono_cols=(0,))

doc.add_heading("2.4 Dependency mapping", level=2)
figure(doc, HERE / "charts" / "dependencies.png", 15.0, "Figure 1. Layered view of the internal dependencies")
tab = {r["module"]: r for r in D["table"]}
pick = ["markdown.extensions", "markdown.util", "markdown.blockprocessors", "markdown.inlinepatterns",
        "markdown.treeprocessors", "markdown.core", "markdown.extensions.fenced_code"]
table(doc, ["Module", "Fan-in (Ca)", "Fan-out (Ce)", "Instability Ce / (Ca + Ce)", "Depends on"],
      [[m.replace("markdown.", "") or "markdown", tab[m]["fan_in"], tab[m]["fan_out"], f'{tab[m]["instability"]:.2f}',
        ", ".join(x.replace("markdown.", "") for x in tab[m]["imports"]) or "(nothing internal)"] for m in pick],
      [4.3, 1.5, 1.6, 2.6, 7.0], size=8.5, align="lrrrl", mono_cols=(0,), keep_together=True)
bullets(doc, [
    f"**No cycles:** {D['modules']} modules, {D['edges_runtime']} import edges, 0 import cycles.",
    "**Healthy direction:** stable modules (`util` 0.00, `Extension` base 0.05) are depended on; every extension "
    "(1.00) depends on them.",
    "**Concentration risk:** `util` has fan-in 16, so a change there reaches half of the code.",
    "**Hidden coupling:** `wikilinks` reads `Markdown.Meta`, an attribute only the `meta` extension creates.",
    "**External:** standard library only at run time; Pygments, PyYAML and pytidylib are optional.",
])

# =================================================================== 3
doc.add_heading("3. Tool-Based Metrics", level=1)
para(doc, "We could not keep a SonarQube server running on the analysis laptop, so we used the open-source tools "
          "below, as the assignment permits. Section 5 applies SonarQube's SQALE formula for the debt ratio.")
table(doc, ["Metric", "Tool (version)", "Result"],
      [["Cyclomatic complexity", "radon cc (6.0.1)", f"total {n(cc['total'])}; mean {cc['mean']:.2f}; maximum "
                                                     f"{cc['max']}; {cc['over_10']} functions above 10"],
       ["Cognitive complexity", "complexipy (8.0.1)", f"total {n(cog['total'])}; mean {cog['mean']:.2f}; maximum "
                                                      f"{cog['max']}; {cog['over_15']} functions above 15"],
       ["Code duplication", "jscpd (5.4.0)", f"{dup['pct_lines']:.2f} % of lines ({dup['duplicated_lines']} lines, "
                                             f"{dup['clones']} clone pairs)"],
       ["Test coverage - statement", "coverage.py (7.16.2)", f"{cov['statement_pct']:.2f} % "
                                                             f"({n(cov['statements'] - cov['missing'])} of "
                                                             f"{n(cov['statements'])})"],
       ["Test coverage - branch", "coverage.py (7.16.2)", f"{cov['branch_pct']:.2f} % ({n(cov['covered_branches'])} of "
                                                          f"{n(cov['branches'])})"],
       ["Bugs", "pylint (4.1.2)", "0 errors; 20 reliability warnings"],
       ["Vulnerabilities", "bandit (1.9.4)", "0 high, 0 medium, 25 low"],
       ["Code smells", "pylint, flake8 (7.4.1), vulture (2.16)", "761 pylint messages; score 8.03 / 10"],
       ["Maintainability index", "radon mi (6.0.1)", f"mean {mi['mean']:.1f}; lowest {mi['min']:.1f}; all modules "
                                                     "rank A"]],
      [4.2, 5.0, 7.8], size=9, bold_first_col=True)

doc.add_heading("3.1 Cyclomatic complexity", level=2)
dist = cc["rank_dist"]
para(doc, f"Most functions are simple: {dist.get('A', 0)} of {cc['blocks']} "
          f"({100 * dist.get('A', 0) / cc['blocks']:.0f} %) are rank A and the median is {cc['median']}. The debt is in "
          f"the tail: {cc['over_10']} functions exceed 10 and {cc['over_15']} exceed 15.")
figure(doc, HERE / "charts" / "cc_distribution.png", 11.0, "Figure 2. Distribution of cyclomatic complexity (radon ranks)")

doc.add_heading("3.2 Cognitive complexity", level=2)
para(doc, f"{cog['over_15']} functions exceed SonarQube's limit of 15 and {cog['over_25']} exceed 25. The ten worst:")
ccmap = {}
for f, items in CC.items():
    for it in items:
        if it["type"] == "class":
            for m in it["methods"]:
                ccmap[(f.replace("\\", "/"), f'{it["name"]}.{m["name"]}')] = (m["complexity"], m["lineno"], m["endline"])
        elif it["type"] == "function":
            ccmap[(f.replace("\\", "/"), it["name"])] = (it["complexity"], it["lineno"], it["endline"])
worst = sorted(((r["complexity"], r["path"].replace("\\", "/"), r["function_name"].replace("::", "."))
                for r in CPX), reverse=True)[:10]
rows = []
for c, f, fn in worst:
    k = ccmap.get((f, fn), ("-", 0, 0))
    rows.append([fn, short(f), f"{k[1]}-{k[2]}", k[0], c])
table(doc, ["Function", "Module", "Lines", "Cyclomatic", "Cognitive"], rows, [7.6, 4.2, 1.6, 1.8, 1.8], size=8.3,
      align="lllrr", mono_cols=(0, 1))
para(doc, "`AttrListTreeprocessor.run` and `getLink` have nearly equal cyclomatic complexity (32 and 33), but the "
          "first is nested six levels deep, so its cognitive complexity is almost double.")

doc.add_heading("3.3 Code duplication", level=2)
para(doc, f"**{dup['pct_lines']:.2f} %** of lines are duplicated ({dup['duplicated_lines']} lines in {dup['clones']} "
          "clone pairs), below SonarQube's 3 % gate. The clones that matter:")
table(doc, ["Clone", "Location A", "Location B"],
      [["HTML escaping of `&`, `<`, `>`", "`serializers.py` 70-78, 85-92", "`extensions/toc.py` 120-127; `util.py` "
                                                                         "158-168"],
       ["Workaround for CPython bug gh-77057", "`htmlparser.py` 372-380", "`extensions/md_in_html.py` 292-302"],
       ["Split a block around a match", "`blockprocessors.py` 594-606", "`extensions/abbr.py` 167-179; "
                                                                        "`extensions/footnotes.py` 286-300"],
       ["Attribute escaping", "`serializers.py` 83-94", "`serializers.py` 102-113"]],
      [5.4, 5.0, 6.6], size=8.5)

doc.add_heading("3.4 Test coverage", level=2)
para(doc, f"Statement coverage is **{cov['statement_pct']:.2f} %** ({cov['missing']} of {n(cov['statements'])} "
          f"statements missed) and branch coverage is **{cov['branch_pct']:.2f} %** "
          f"({cov['branches'] - cov['covered_branches']} of {n(cov['branches'])} missed), from the project's 1,123 "
          "tests.")
para(doc, "This needed two combined runs. The code-highlighting tests skip unless Pygments is exactly 2.7.1; in a "
          "normal environment 111 tests are skipped and `codehilite.py` drops to 11 % (overall 94 %).")
low = sorted((r for r in files if r["cov_branch"] is not None), key=lambda r: r["cov_branch"])[:5]
table(doc, ["Module (lowest branch coverage)", "Statement %", "Branch %", "Missed statements", "Missed branches"],
      [[short(r["file"]), f'{r["cov_stmt"]:.1f}', f'{r["cov_branch"]:.1f}', r["missing"], r["missing_branches"]]
       for r in low], [6.0, 2.4, 2.4, 3.0, 3.0], size=8.5, align="lrrrr", mono_cols=(0,), keep_together=True)

doc.add_heading("3.5 Bugs, vulnerabilities and code smells", level=2)
table(doc, ["Category", "Tool and rule", "Count", "Assessment"],
      [["Bugs (confirmed)", "pylint error / fatal", "0", "None provable statically"],
       ["Bugs (potential)", "`super-init-not-called`", "8", "Base initialiser skipped"],
       ["", "`arguments-differ`, `arguments-renamed`", "6", "Override changes the base signature"],
       ["", "`inconsistent-return-statements`", "5", "Value on some paths, `None` on others"],
       ["", "`deprecated-method`", "1", "`logger.warn()` at `blockprocessors.py:490`"],
       ["Vulnerabilities", "bandit B405 (`xml.etree` import)", "20", "False positives: no XML input is parsed"],
       ["", "bandit B101 (`assert`)", "5", "Low: removed under `python -O`"],
       ["Code smells", "pylint convention", "554", "`line-too-long` 196, `invalid-name` 152, missing docstrings 62"],
       ["", "pylint refactor", "93", "`no-else-return` 24, `too-many-branches` 12"],
       ["", "pylint warning (remaining)", "98", "`attribute-defined-outside-init` 36, `redefined-builtin` 29"],
       ["", "flake8", "4", "But 17 modules switch flake8 off file-wide (Section 4.4)"],
       ["", "vulture (dead code)", "1", "One unused variable"]],
      [3.0, 5.6, 1.3, 7.1], size=8.5, align="llrl")

doc.add_heading("3.6 Maintainability index", level=2)
para(doc, f"All {S['files']} modules are rank A (above 19) with a mean of {mi['mean']:.1f}, but the spread is wide: "
          "seven modules holding 47 % of the lines score below 41.")
table(doc, ["Module (lowest MI)", "MI", "LOC", "Functions", "CC sum"],
      [[short(f), f"{v:.1f}", next(r["loc"] for r in files if r["file"] == f),
        next(r["funcs"] for r in files if r["file"] == f), next(r["cc_sum"] for r in files if r["file"] == f)]
       for f, v, _ in mi["lowest"][:5]], [6.0, 2.0, 2.0, 2.4, 2.0], size=8.5, align="lrrrr", mono_cols=(0,),
      keep_together=True)

# =================================================================== 4
doc.add_heading("4. Debt Identification", level=1)
table(doc, ["ID", "Debt type", "Weakness", "Evidence"],
      [["TD-01", "Code debt", "Over-complex functions",
        f"{cog['over_15']} functions above cognitive 15; worst `AttrListTreeprocessor.run` (CC 32, cognitive 102)"],
       ["TD-02", "Design debt", "Oversized module", "`inlinepatterns.py`: 1,052 lines, 24 classes, lowest MI (25.9)"],
       ["TD-03", "Design debt", "Duplicated logic", f"{dup['clones']} clone pairs; escaping helper exists three times"],
       ["TD-04", "Test debt", "Pinned tests, branch gaps",
        "111 tests skip unless Pygments is 2.7.1; 85 uncovered branches; 88 `pragma: no cover`"],
       ["TD-05", "Documentation debt", "Undocumented or misleading code",
        "62 missing docstrings (17 in `htmlparser.py`); stale TODOs"],
       ["TD-06", "Infrastructure debt", "Stale version workarounds",
        "Workaround \"until we drop Python < 3.13\" in two files; CLI on `optparse`"],
       ["TD-07", "Design debt (obsolescence)", "Deprecated and dead code", "10 items still shipped"],
       ["TD-08", "Code debt", "Inconsistent naming", "152 `invalid-name`: camelCase beside snake_case"],
       ["TD-09", "Code debt", "Lint findings, suppressed checks",
        "281 other pylint findings; 17 modules exempt from flake8"],
       ["TD-10", "Security debt", "Assertions as run-time checks", "5 `assert` statements in production paths"]],
      [1.3, 3.4, 4.3, 8.0], size=8.5, bold_first_col=True)

doc.add_heading("4.1 Example of code debt: a deeply nested method (TD-01)", level=2)
para(doc, "`AttrListTreeprocessor.run` (`extensions/attr_list.py`, lines 103-161) repeats the same block three times "
          "at nesting depth five:")
code(doc, '''119    if pos is None and elem[-1].tail:
121        m = RE.search(elem[-1].tail)
122        if m:
123            if not self.assign_attrs(elem, m.group(1), strict=True):
124                elem[-1].tail = elem[-1].tail[:m.start()]
125    elif pos is not None and pos > 0 and elem[pos-1].tail:
127        m = RE.search(elem[pos-1].tail)
128        if m:
129            if not self.assign_attrs(elem, m.group(1), strict=True):
130                elem[pos-1].tail = elem[pos-1].tail[:m.start()]
131    elif elem.text:  ...  # the same block a third time''')
para(doc, "Result: cyclomatic 32, cognitive 102 (almost seven times the limit), four branches untested.")

doc.add_heading("4.2 Example of design debt: one fix, two copies (TD-03)", level=2)
para(doc, "The same workaround is in `htmlparser.py` (line 372) and `extensions/md_in_html.py` (line 292):")
code(doc, '''if self.rawdata[i:i+3] == '<![' and not self.rawdata[i:i+9] == '<![CDATA[':
    # We have encountered the bug in #1534 (Python bug `gh-77057`).
    # Provide an override until we drop support for Python < 3.13.
    result = self.parse_bogus_comment(i)''')
para(doc, "Both are among the five most-changed files, and 11 of the 15 commits to `htmlparser.py` were bug fixes, so "
          "every parser fix has to be made twice.")

doc.add_heading("4.3 Example of test debt: tests tied to one library release (TD-04)", level=2)
code(doc, '''# tests/test_syntax/extensions/test_code_hilite.py
def setUp(self):
    if has_pygments and pygments.__version__ != required_pygments_version:
        self.skipTest(f'Pygments=={required_pygments_version} is required')''')
para(doc, "The expected HTML was captured from Pygments 2.7.1 (2020). With any other version the suite still passes "
          "while 111 tests are silently skipped, so a regression from a newer Pygments goes unnoticed.")

doc.add_heading("4.4 Example of documentation debt (TD-05)", level=2)
bullets(doc, [
    "`htmlparser.py`, the most-changed file: 18 of its 28 functions have no docstring.",
    "`core.py:119`: `# TODO: Maybe delete this. It does not appear to be used anymore.` on a public attribute.",
    "17 modules contain `# flake8: noqa: E501 116-119`. It reads as an exemption for four lines, but we tested it "
    "and flake8 then reports nothing for the whole file.",
])

doc.add_heading("4.5 Example of infrastructure debt (TD-06)", level=2)
para(doc, "`htmlparser.py:169` still says \"TODO: remove this when the bug is fixed in all supported Python "
          "versions\", and the override in 4.2 waits for Python 3.13. Nothing links these workarounds to the "
          "supported-version setting, so they outlive their purpose.")

# =================================================================== 5
doc.add_heading("5. Remediation Cost and Debt Ratio", level=1)
doc.add_heading("5.1 Method", level=2)
para(doc, "We applied the SQALE method used by SonarQube. The effort per finding is our own calibration; overlapping "
          "findings are costed once.")
code(doc, '''Remediation cost     = SUM over findings ( effort to fix the finding )
Development cost     = SLOC x 30 minutes          (SonarQube default: 30 min per line of code)
Technical Debt Ratio = Remediation cost / Development cost x 100 %''', size=9)

doc.add_heading("5.2 Tool outputs and cost per item", level=2)
SHORT = {
    "R1": "Functions with cognitive complexity above 15", "R2": "Duplicated blocks", "R3": "Uncovered statements",
    "R4": "Uncovered branches", "R5": "Tests pinned to Pygments 2.7.1", "R6": "Missing docstrings",
    "R7": "Non-PEP 8 names in the public API", "R8": "Non-PEP 8 local names", "R9": "Other pylint findings",
    "R10": "Lines over 119 columns", "R11": "Security findings", "R12": "Oversized `inlinepatterns.py`",
    "R13": "Deprecated or dead code", "R14": "Stale Python-version workarounds"}
RULE = {
    "R1": "5 min + 1 min per point above 15", "R2": "20 min per clone pair", "R3": "2 min per line",
    "R4": "5 min per branch", "R5": "fixed estimate, 4 h", "R6": "5 min each", "R7": "15 min each (alias + shim)",
    "R8": "2 min each", "R9": "1-20 min each, by rule", "R10": "1 min each", "R11": "10 min per assert, 2 min per review",
    "R12": "fixed estimate, 8 h", "R13": "15 min each", "R14": "30 min each"}
rows = [[i["key"], SHORT[i["key"]], i["debt_type"].replace(" / dependency", ""), f'{i["count"]} {i["unit"]}',
         RULE[i["key"]], n(i["minutes"])] for i in R["items"]]
rows.append(["", "Total remediation cost", "", "", f'{R["total_hours"]} h = {R["total_days"]} person-days',
             n(R["total_minutes"])])
table(doc, ["#", "Finding (tool output)", "Debt type", "Count", "Effort rule", "Minutes"], rows,
      [0.9, 5.2, 2.7, 2.6, 4.3, 1.3], size=8.3, align="lllllr", total_row=True)
para(doc, "Example (R1): `handle_endtag` has cognitive complexity 94, so 5 + (94 - 15) = 84 minutes.", size=9.5)
bt = sorted(R["by_type"].items(), key=lambda kv: -kv[1])
table(doc, ["Debt type", "Minutes", "Hours", "Share"],
      [[k.replace(" / dependency", ""), n(v), f"{v / 60:.1f}", f"{100 * v / R['total_minutes']:.0f} %"] for k, v in bt],
      [6.0, 2.2, 2.2, 2.2], size=9, align="lrrr", keep_together=True)

doc.add_heading("5.3 Technical Debt Ratio", level=2)
code(doc, f'''Remediation cost = {n(R["total_minutes"])} min  ({R["total_hours"]} hours)
Development cost = {n(R["sloc"])} SLOC x 30 min = {n(R["dev_cost_minutes"])} min  ({n(R["dev_cost_hours"])} hours)
TDR              = {n(R["total_minutes"])} / {n(R["dev_cost_minutes"])} x 100 = {R["tdr_pct"]:.2f} %''', size=9)
table(doc, ["SQALE maintainability rating", "A", "B", "C", "D", "E"],
      [["Technical Debt Ratio", "up to 5 %", "6 - 10 %", "11 - 20 %", "21 - 50 %", "above 50 %"],
       ["Python-Markdown", f"{R['tdr_pct']:.1f} %", "", "", "", ""]],
      [5.0, 2.2, 2.2, 2.2, 2.2, 2.2], size=9, align="lccccc", bold_first_col=True)
para(doc, f"**Justification.** {R['tdr_pct']:.1f} % is rating A, consistent with 97 % coverage, 2.4 % duplication and "
          "no import cycles. Three qualifications:")
bullets(doc, [
    f"**Size base:** we used SLOC as SonarQube does; with all {n(R['loc'])} physical lines the ratio would be "
    f"{R['tdr_pct_physical_loc']:.1f} %.",
    "**Concentration:** five of the 33 modules hold 61 % of the over-threshold cognitive complexity.",
    "**Not all should be repaid:** R7 (23 % of the total) means renaming public methods, which would break "
    "third-party extensions.",
])

# =================================================================== 6
doc.add_heading("6. Prioritization Strategy", level=1)
doc.add_heading("6.1 Technique 1: hotspot analysis", level=2)
para(doc, "A hotspot is code that is both complex and often changed. Score = commits touching the module in the last "
          "three years (`git log`, 71 commits) x its cognitive complexity.")
figure(doc, HERE / "charts" / "hotspots.png", 12.0, "Figure 3. Change frequency against cognitive complexity per module")
hs = sorted((r for r in files if r["file"] not in ("markdown/test_tools.py", "markdown/__meta__.py")),
            key=lambda r: -r["churn_3y"] * r["cog_sum"])[:6]
worst_fn = {}
for r in CPX:
    f = r["path"].replace("\\", "/")
    if r["complexity"] > worst_fn.get(f, ("", -1))[1]:
        worst_fn[f] = (r["function_name"].replace("::", "."), r["complexity"])
table(doc, ["Rank", "Module", "Commits", "Fixes", "Cognitive", "Score", "Worst function (cognitive)"],
      [[i + 1, short(r["file"]), r["churn_3y"], r["fix_3y"], r["cog_sum"], n(r["churn_3y"] * r["cog_sum"]),
        f'{worst_fn[r["file"]][0]} ({worst_fn[r["file"]][1]})'] for i, r in enumerate(hs)],
      [1.0, 4.3, 1.4, 1.1, 1.6, 1.2, 6.4], size=8.2, align="clrrrrl", mono_cols=(1, 6), keep_together=True)
para(doc, "The top four modules hold 40 % of the cognitive complexity and were touched by 32 of the 71 commits. "
          "In `htmlparser.py`, 11 of 15 commits were fixes. `_serialize_html` is the third most complex function "
          "but its file changed only twice, so it is not a priority.")

doc.add_heading("6.2 Technique 2: weighted scoring model", level=2)
para(doc, "Each debt item is scored 1 to 5 on four criteria: **Impact** on users (weight 0.30), **Risk** of defects "
          "(0.25), **Change** frequency of the affected code (0.25) and **Ease** of repayment (0.20).")
W = (0.30, 0.25, 0.25, 0.20)
wsm = [("TD-01", "Over-complex functions", 5, 5, 5, 2, "Worst functions are in the four hotspots"),
       ("TD-03", "Duplicated logic", 3, 4, 4, 4, "Parser fix duplicated in two hotspot files"),
       ("TD-04", "Pinned tests and branch gaps", 4, 4, 3, 3, "111 skipped tests hide regressions"),
       ("TD-02", "Oversized `inlinepatterns.py`", 3, 3, 5, 2, "11 commits in 3 years, MI 25.9"),
       ("TD-06", "Stale version workarounds", 2, 3, 5, 3, "In `htmlparser.py`; partly blocked until 3.13"),
       ("TD-05", "Missing documentation", 2, 2, 4, 5, "18 undocumented functions in `htmlparser.py`"),
       ("TD-10", "Assertions as run-time checks", 3, 2, 2, 5, "5 statements, 50 minutes"),
       ("TD-07", "Deprecated and dead code", 2, 2, 2, 5, "150 minutes"),
       ("TD-09", "Lint findings", 1, 2, 3, 4, "Mostly automatic fixes"),
       ("TD-08", "Naming inconsistency", 2, 1, 2, 1, "Renaming breaks third-party extensions")]
wsm = sorted(wsm, key=lambda x: -sum(w * s for w, s in zip(W, x[2:6])))
table(doc, ["Rank", "Item", "Debt", "Impact", "Risk", "Change", "Ease", "Score", "Evidence"],
      [[i + 1, x[0], x[1], x[2], x[3], x[4], x[5], f"{sum(w * s for w, s in zip(W, x[2:6])):.2f}", x[6]]
       for i, x in enumerate(wsm)],
      [1.0, 1.3, 3.9, 1.2, 1.0, 1.3, 1.0, 1.2, 5.1], size=8.3, align="cllccccrl", keep_together=True)

doc.add_heading("6.3 Prioritised order and justification", level=2)
para(doc, "Both techniques put the same thing first: the top-scoring item (TD-01) lies in the top-ranked hotspot "
          "modules.")
table(doc, ["Order", "Action", "Items", "Effort", "Why now"],
      [["1", "Refactor the ten over-threshold functions in the four hotspot modules", "TD-01 (part)", "6 h",
        "Top of both rankings"],
       ["2", "Merge the duplicated parser workaround and escaping helpers", "TD-03 (part)", "2 h",
        "Cheap; prevents half-applied fixes"],
       ["3", "Unpin the Pygments tests; cover `smarty` and `footnotes` branches", "TD-04", "13 h",
        "Safety net before step 5"],
       ["4", "Replace asserts, delete dead code, document `htmlparser.py`", "TD-10, TD-07, TD-05", "9 h",
        "Quick wins"],
       ["5", "Split `inlinepatterns.py`; refactor the remaining complex functions", "TD-02, TD-01 (rest)", "14 h",
        "Valuable but risky"],
       ["6", "Remove version workarounds when Python 3.13 is the minimum", "TD-06", "1.5 h", "Blocked until then"],
       ["7", "Fix lint findings when a file is edited anyway", "TD-09", "17 h", "No user impact"],
       ["-", "Do not rename the camelCase public API", "TD-08", "(21 h avoided)", "Breaks third-party extensions"]],
      [1.1, 7.6, 2.8, 1.8, 3.7], size=8.3, align="cllll", keep_together=True)
para(doc, "Steps 1 to 4 take about 30 hours, one third of the total remediation cost.")

# =================================================================== 7
doc.add_heading("7. Reflection", level=1)
doc.add_heading("Lessons learned", level=3)
bullets(doc, [
    "**Averages hide debt.** Mean complexity 3.3 and 97 % coverage look healthy; the debt sits in 6 % of the "
    "functions and four files.",
    "**One metric is not enough.** Two functions with equal cyclomatic complexity differed twofold in cognitive "
    "complexity; coverage was 94 % or 97 % depending on one environment variable.",
    "**History is a metric.** Change frequency turned a list of complex functions into a ranking.",
])
doc.add_heading("Trade-offs considered", level=3)
bullets(doc, [
    "**Compatibility against cleanliness.** camelCase names and legacy extensions exist because third-party "
    "extensions depend on them, so we costed that debt but advise against repaying it.",
    "**Risk against benefit.** The parser needs refactoring most and is the most fix-prone, so test debt is ranked "
    "ahead of the large structural change.",
    "**Precision.** Our effort constants are estimates, so we rely on the ranking more than on the 4.2 % figure.",
])
doc.add_heading("Implications for maintenance and evolution", level=3)
bullets(doc, [
    "Manage debt where change happens: a CI rule against raising complexity in hotspot files costs almost nothing.",
    "Workarounds need an expiry: tie each to the minimum supported Python version in the release checklist.",
    "Suppressions (`noqa`, `pragma: no cover`) are debt too and should be reviewed like code.",
])

# =================================================================== Appendix A
doc.add_heading("Appendix A. Individual Component: Manual Calculations",
                level=1).paragraph_format.page_break_before = True
para(doc, "Each member calculated the three metrics by hand for two files. The scanned handwritten sheets follow "
          "each member's summary. Rules used:")
bullets(doc, [
    "**Cyclomatic complexity:** decision points + 1 per function (`if`, `elif`, `for`, `while`, `except`, each "
    "`and` / `or`, comprehension `for` / `if`, conditional expression).",
    "**Cognitive complexity** (SonarSource): +1 per `if`, `elif`, `else`, loop, `except`, conditional expression "
    "and boolean-operator sequence, plus +1 per nesting level for `if`, loops, `except` and conditional expressions.",
    "**Comment density** (SonarQube): comment lines / (comment lines + code lines) x 100; docstrings count as "
    "comments, blank lines are excluded.",
])
members = [("Member 1", "Taha Yasir", "i222429", [0, 1]),
           ("Member 2", "Khizar", "i222595", [2, 3]),
           ("Member 3", "Hadeed Abbas", "i228780", [4, 5])]
radon_cc = {r["file"]: r["cc_sum"] for r in files}
cpx_file = {}
for r in CPX:
    cpx_file[r["path"].replace("\\", "/")] = cpx_file.get(r["path"].replace("\\", "/"), 0) + r["complexity"]

INTERP = {
    "markdown/extensions/def_list.py": [
        "**Risks.** One method holds the complexity: `DefListProcessor.run` has cyclomatic 17 (rank C); the other "
        "four functions have 1. It is driven by compound conditions (six `and` operators) and a `state` variable "
        "set in three places, and it returns `False` on one path and nothing on the others.",
        "**Debt and maintenance.** Code debt with a documentation side: density is 36.4 %, but 15 of the 36 comment "
        "lines are licence header and a registration table, and `run` has no docstring. The file changed three "
        "times in three years, so interest is low; two extracted helpers would bring `run` under 10. The tool "
        "reports cognitive 19 against 17 by hand because it also counts the list comprehension on lines 43-44."],
    "markdown/extensions/meta.py": [
        "**Risks.** `MetaPreprocessor.run` is a hand-written line parser: a `while` loop with two `break` "
        "statements, `try / except KeyError` used as normal control flow, and three levels of nesting. Cognitive "
        "complexity (17) is well above cyclomatic (10), so nesting is the problem. Branch coverage is 90 %: a "
        "document that ends inside the metadata block is untested.",
        "**Debt and maintenance.** Design debt: `MetaExtension.reset` creates `Markdown.Meta` on an object it does "
        "not own, and `wikilinks.py` reads it with `hasattr`. Two extensions are coupled through an attribute no "
        "class declares, so a change to the metadata format can break a reader the maintainer cannot find."],
    "markdown/extensions/admonition.py": [
        "**Risks.** `parse_content` (cyclomatic 13, cognitive 19) nests a four-part `and` and a conditional "
        "expression inside a `while` loop; the conditional expression alone costs four points at nesting level 3. "
        "`test()` stores `current_sibling` and `content_indent` for `run()`, so the two methods are only correct "
        "when called in that order.",
        "**Debt and maintenance.** Code debt plus design debt (a hidden calling protocol). The class and three "
        "methods have no docstring and the comment on line 159 is garbled, so the 31.9 % density overstates the "
        "documentation. Statement and branch coverage are both 100 %, which makes refactoring safe."],
    "markdown/extensions/wikilinks.py": [
        "**Risks.** Low: every function is rank A and the highest cyclomatic value is 5. `_getMeta` repeats the "
        "same `if 'wiki_...' in self.md.Meta` block three times, and `handleMatch` returns an `Element` on one "
        "path and an empty string on the other.",
        "**Debt and maintenance.** Mild design debt: the file depends on the `meta` extension through the "
        "undeclared `Markdown.Meta` attribute. Fixing everything would take about half an hour and the file changed "
        "three times in three years, so it is low priority and a baseline for a low-debt extension."],
    "markdown/postprocessors.py": [
        "**Risks.** `RawHtmlPostprocessor.run` hides its logic in a nested function that calls itself through "
        "`pattern.sub(substitute_match, html)`, so recursion depth depends on the input. Per-function tools "
        "understate it: radon reports 2 for `run` and 5 for the closure, while cognitive complexity charges the "
        "closure to its parent and gives 10.",
        "**Debt and maintenance.** Obsolescence debt: `UnescapePostprocessor` is `@deprecated` but still shipped, "
        "and its two methods are the file's only uncovered lines. Documentation debt: three docstrings contain "
        "errors (lines 22, 49, 96) and the base `Postprocessor.run` is a bare `pass`, so a subclass that forgets "
        "to override it silently returns `None`."],
    "markdown/extensions/legacy_attrs.py": [
        "**Risks.** Only 27 code lines. `LegacyAttrs.run` reaches cyclomatic 7 from three `if` statements, two "
        "with an `and`, inside one loop. The callback in `handleAttributes` changes the element as a side effect "
        "and returns nothing, relying on `re.sub` treating `None` as an empty replacement.",
        "**Debt and maintenance.** The module is deliberate debt, kept so that pre-3.0 documents still render. Its "
        "52.6 % comment density is the highest measured, but 13 of the 30 comment lines are licence header and "
        "neither class has a docstring. The cost is small but permanent: it must pass on every new Python version "
        "until a major release removes it."],
}

for label, name, roll, idx in members:
    h = doc.add_heading(f"A.{label[-1]}  {label}: {name} ({roll})", level=2)
    h.paragraph_format.page_break_before = label != "Member 1"
    rows = []
    for i in idx:
        d = M[i]
        c = d["counts"]
        rows.append([short(d["file"]), d["total_lines"], c["blank"], c["comment"], c["docstring"], c["code"],
                     f'{d["comment_lines"]} / ({d["comment_lines"]} + {c["code"]}) = {d["comment_density"]:.1f} %'])
    table(doc, ["File", "Lines", "Blank", "# comment", "Docstring", "Code", "Comment density"], rows,
          [4.4, 1.3, 1.3, 1.8, 1.8, 1.3, 5.1], size=8.5, align="lrrrrrl", mono_cols=(0,))
    rows = []
    for i in idx:
        d = M[i]
        first = True
        for f in d["functions"]:
            if f["cc"] == 1 and not f["cog"]:
                continue
            rows.append([short(d["file"]) if first else "", f["name"].replace(".<closure> ", " > "), f["cc"],
                         "(in parent)" if f["cog"] is None else f["cog"]])
            first = False
        simple = sum(1 for f in d["functions"] if f["cc"] == 1 and not f["cog"])
        rows.append(["", f"{simple} other functions with no decision point", f"{simple} x 1", 0])
        rows.append(["", "File total (hand)  |  tool cross-check", f'{d["cc_total"]}  |  {radon_cc[d["file"]]}',
                     f'{d["cog_total"]}  |  {cpx_file[d["file"]]}'])
    table(doc, ["File", "Function", "Cyclomatic", "Cognitive"], rows, [4.4, 7.6, 2.5, 2.5], size=8.5, align="llrr",
          mono_cols=(0, 1))
    for i in idx:
        d = M[i]
        doc.add_heading(f"Interpretation: {short(d['file'])}", level=3)
        for txt in INTERP[d["file"]]:
            para(doc, txt, align="justify")
    para(doc, f"[ Insert {name}'s scanned handwritten calculation sheets after this page ]", align="center",
         color=MUTED, before=10)

# =================================================================== Appendix B
doc.add_heading("Appendix B. Reproducing the Measurements", level=1).paragraph_format.page_break_before = True
p = para(doc, "Scripts and raw tool outputs:  ")
hyperlink(p, GROUP_REPO)
code(doc, '''git clone https://github.com/Python-Markdown/markdown.git && cd markdown
git checkout 0bf535bc406c95dad66050f07c8402af03fe07d5

radon raw markdown -j        # size, comment lines
radon cc  markdown -s -a -j  # cyclomatic complexity
radon mi  markdown -s -j     # maintainability index
complexipy markdown --output-format json           # cognitive complexity
npx jscpd markdown --min-lines 5 --min-tokens 50    # duplication
pylint markdown --output-format=json2 --exit-zero   # bugs / code smells
bandit -r markdown -f json                          # vulnerabilities
flake8 markdown --max-line-length=119 ; vulture markdown --min-confidence 80

# coverage: two runs, combined; .coveragerc set aside so test_tools.py is measured too
coverage run -p --branch --source=markdown -m unittest discover tests      # without Pygments
pip install pygments==2.7.1 && set PYGMENTS_VERSION=2.7.1
coverage run -p --branch --source=markdown -m unittest discover tests      # with pinned Pygments
coverage combine && coverage report

git log --since="3 years ago" --name-only --format=@%H^|%s -- markdown     # change frequency''', size=7.8)
doc.add_heading("References", level=3)
bullets(doc, [
    "T. J. McCabe, \"A Complexity Measure\", IEEE Transactions on Software Engineering, 1976.",
    "G. A. Campbell, \"Cognitive Complexity\", SonarSource, 2018.",
    "J.-L. Letouzey, \"The SQALE Method for Managing Technical Debt\", 2016.",
    "A. Tornhill, \"Your Code as a Crime Scene\", Pragmatic Bookshelf, 2015.",
], size=9.5)

doc.save(OUT)
print("saved", OUT)
