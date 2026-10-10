"""Build the worked-solution sheets for the individual manual calculations (to be copied out by hand)."""
import json
from pathlib import Path

from docx_helpers import MUTED, add_footer, code, hyperlink, new_document, page_break, para, table

HERE = Path(__file__).parent
OUT = HERE.parent / "Manual_Calculation_Worksheets.docx"
M = json.loads((HERE / "manual_calc.json").read_text(encoding="utf-8"))
CPX = json.loads((HERE / "complexipy.json").read_text(encoding="utf-8"))
CC = json.loads((HERE / "radon_cc.json").read_text(encoding="utf-8"))
RAW = {k.replace("\\", "/"): v for k, v in json.loads((HERE / "radon_raw.json").read_text(encoding="utf-8")).items()}

cpx = {(r["path"].replace("\\", "/"), r["function_name"].replace("::", ".")): r["complexity"] for r in CPX}
radon = {}
for f, items in CC.items():
    f = f.replace("\\", "/")

    def put(name, b):
        radon[(f, name)] = b["complexity"]
        for c in b.get("closures", []):
            radon[(f, f"{name}.<closure> {c['name']}")] = c["complexity"]

    for it in items:
        if it["type"] == "class":
            for m in it["methods"]:
                put(f'{it["name"]}.{m["name"]}', m)
        elif it["type"] == "function":
            put(it["name"], it)

OWNERS = ["Taha Yasir (i222429)", "Taha Yasir (i222429)", "Khizar (i222595)", "Khizar (i222595)",
          "Hadeed Abbas (i228780)", "Hadeed Abbas (i228780)"]
NOTES = {
    "markdown/extensions/def_list.py":
        "complexipy reports 19 for `DefListProcessor.run` because it also counts the list comprehension on lines "
        "43-44 (+2). The SonarSource rules do not, so the hand result is 17. Write both numbers on your sheet.",
    "markdown/postprocessors.py":
        "The nested function `substitute_match` (lines 75-86) has its own +1 for cyclomatic complexity, but its "
        "cognitive complexity is charged to `run` one nesting level deeper, so line 76 scores 2.",
    "markdown/extensions/legacy_attrs.py":
        "The nested function `attributeCallback` (line 59) has no decision point: cyclomatic 1, cognitive 0.",
}

doc = new_document(body_pt=10.5)
add_footer(doc, "Manual calculation worksheets - copy by hand    |    github.com/Taha9876/SRE-A1")

doc.add_heading("Manual Calculation Worksheets", level=1)
para(doc, "Worked steps for the individual component. Copy your two files by hand, scan the sheets and attach them "
          "to Appendix A. Line numbers refer to Python-Markdown at commit `0bf535bc`.")
hyperlink(para(doc, "Repository:  "), "https://github.com/Taha9876/SRE-A1")
table(doc, ["Member", "File 1", "File 2"],
      [["Taha Yasir (i222429)", "`markdown/extensions/def_list.py`", "`markdown/extensions/meta.py`"],
       ["Khizar (i222595)", "`markdown/extensions/admonition.py`", "`markdown/extensions/wikilinks.py`"],
       ["Hadeed Abbas (i228780)", "`markdown/postprocessors.py`", "`markdown/extensions/legacy_attrs.py`"]],
      [4.0, 6.5, 6.5], size=9.5, bold_first_col=True)

doc.add_heading("Rules to write at the top of your sheet", level=2)
para(doc, "**1. Comment density** (SonarQube definition)", after=2)
code(doc, '''Comment density = comment lines / (comment lines + code lines) x 100

blank line     : contains only whitespace (not counted anywhere)
comment line   : a line that is only a # comment, or any non-blank line of a docstring
code line      : every other non-blank line (code + trailing # comment = code line)''', size=9)
para(doc, "**2. Cyclomatic complexity** (McCabe, per function)", after=2)
code(doc, '''CC = D + 1        D = number of decision points in the function

+1 for each:  if, elif, for, while, except, conditional expression (a if c else b),
              each `and` / `or`, each `for` and each `if` inside a comprehension
+0 for:       else, try, finally, return, break
A nested function is its own unit with its own +1.     File CC = sum over all functions.''', size=9)
para(doc, "**3. Cognitive complexity** (SonarSource, G. A. Campbell)", after=2)
code(doc, '''Start at 0 for each function.
Structural increment  +1 : if, elif, else, for, while, except, conditional expression,
                           each sequence of the same boolean operator (a and b and c = +1)
Nesting increment     +N : added to if, for, while, except, conditional expression.
                           N = number of enclosing if/elif/else, loop, except
                           or nested-function blocks.
                           elif, else and boolean sequences get NO nesting increment.
Increment written in the tables below = 1 + N.''', size=9)

for idx, d in enumerate(M):
    page_break(doc)
    f = d["file"]
    doc.add_heading(f"{OWNERS[idx]} - File {idx % 2 + 1}: {f}", level=1)
    c = d["counts"]

    # ---------------------------------------------------------------- comment density
    doc.add_heading("Step 1. Comment density", level=2)
    table(doc, ["Category", "Line numbers", "Count"],
          [["Blank", ", ".join(d["line_ranges"]["blank"]), c["blank"]],
           ["# comment", ", ".join(d["line_ranges"]["comment"]), c["comment"]],
           ["Docstring", ", ".join(d["line_ranges"]["docstring"]), c["docstring"]],
           ["Code", ", ".join(d["line_ranges"]["code"]), c["code"]],
           ["Total", f'check: {c["blank"]} + {c["comment"]} + {c["docstring"]} + {c["code"]}', d["total_lines"]]],
          [2.6, 12.6, 1.8], size=9, align="llr", bold_first_col=True, total_row=True)
    if d["mixed_lines"]:
        para(doc, f"Line(s) {', '.join(map(str, d['mixed_lines']))}: code followed by a trailing `#` comment, "
                  "counted as code.", size=9.5)
    r = RAW[f]
    code(doc, f'''Comment lines   = {c["comment"]} + {c["docstring"]} = {d["comment_lines"]}
Code lines      = {c["code"]}
Comment density = {d["comment_lines"]} / ({d["comment_lines"]} + {c["code"]}) x 100 = {d["comment_lines"]} / {d["comment_lines"] + c["code"]} x 100 = {d["comment_density"]:.1f} %

Cross-check (radon raw): SLOC = {r["sloc"]} (matches the code count), blank = {r["blank"]}''', size=9)

    # ---------------------------------------------------------------- cyclomatic
    doc.add_heading("Step 2. Cyclomatic complexity", level=2)
    simple = [x for x in d["functions"] if x["cc"] == 1]
    for fn in d["functions"]:
        if fn["cc"] == 1:
            continue
        name = fn["name"].replace(".<closure> ", " > nested function ")
        para(doc, f"**{name}** (lines {fn['start']}-{fn['end']})", after=2, keep=True)
        rows, run = [["-", "function entry", "1", "1"]], 1
        for s in fn["cc_steps"]:
            run += s["inc"]
            rows.append([s["line"], s["what"], f'+{s["inc"]}', run])
        rows.append(["", f'CC = {run - 1} decision points + 1', "", fn["cc"]])
        table(doc, ["Line", "Decision point", "Add", "Running CC"], rows, [1.5, 10.0, 1.8, 2.7], size=9, align="rlrr",
              total_row=True)
        ref = radon.get((f, fn["name"]))
        para(doc, f"Tool cross-check: radon reports {ref}." + (" Match." if ref == fn["cc"] else " DIFFERENT."),
             size=9.5, color=MUTED)
    names = ", ".join(f"`{x['name'].split('.')[-1].replace('<closure> ', '')}`" for x in simple)
    para(doc, f"Functions with no decision point (CC = 1 each): {names}. That is {len(simple)} x 1 = {len(simple)}.")
    parts = " + ".join(str(x["cc"]) for x in d["functions"] if x["cc"] > 1)
    code(doc, f'''File cyclomatic complexity = {parts} + {len(simple)} = {d["cc_total"]}
Highest function = {d["cc_max"]}      Average = {d["cc_total"]} / {len(d["functions"])} functions = {d["cc_total"] / len(d["functions"]):.2f}''', size=9)

    # ---------------------------------------------------------------- cognitive
    doc.add_heading("Step 3. Cognitive complexity (stepwise)", level=2)
    zero = []
    for fn in d["functions"]:
        if fn.get("closure"):
            continue
        if not fn["cog"]:
            zero.append(fn["name"].split(".")[-1])
            continue
        para(doc, f"**{fn['name']}** (lines {fn['start']}-{fn['end']})", after=2, keep=True)
        rows, run = [], 0
        for s in fn["cog_steps"]:
            run += s["inc"]
            nest = "-" if s["nesting"] is None else s["nesting"]
            how = "+1" if s["nesting"] is None else (f'+1 +{s["nesting"]} nesting' if s["nesting"] else "+1")
            rows.append([s["line"], s["what"], nest, how, f'+{s["inc"]}', run])
        rows.append(["", "Cognitive complexity", "", "", "", fn["cog"]])
        table(doc, ["Line", "Construct", "Nesting level", "Increment", "Add", "Running total"], rows,
              [1.4, 5.4, 2.3, 3.4, 1.4, 2.3], size=9, align="rlclrr", total_row=True)
        ref = cpx.get((f, fn["name"]))
        para(doc, f"Tool cross-check: complexipy reports {ref}." +
             (" Match." if ref == fn["cog"] else " See the note below."), size=9.5, color=MUTED)
    para(doc, "Functions with a straight-line body (cognitive complexity 0): " +
         ", ".join(f"`{z}`" for z in zero) + ".")
    parts = " + ".join(str(x["cog"]) for x in d["functions"] if x["cog"])
    total = f'{parts} = {d["cog_total"]}' if "+" in parts else parts
    code(doc, f'''File cognitive complexity = {total}        Highest function = {d["cog_max"]}''',
         size=9)
    if f in NOTES:
        para(doc, "**Note.** " + NOTES[f], align="justify")

    doc.add_heading("Result to carry into Appendix A", level=3)
    table(doc, ["Comment density", "Cyclomatic (file / max)", "Cognitive (file / max)"],
          [[f'{d["comment_density"]:.1f} %', f'{d["cc_total"]} / {d["cc_max"]}', f'{d["cog_total"]} / {d["cog_max"]}']],
          [5.6, 5.7, 5.7], size=10, align="ccc")

doc.save(OUT)
print("saved", OUT)
