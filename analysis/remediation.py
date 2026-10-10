"""SQALE-style remediation cost and Technical Debt Ratio from the tool outputs in this folder."""
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
S = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
PL = json.loads((HERE / "pylint.json").read_text(encoding="utf-8"))["messages"]
CPX = json.loads((HERE / "complexipy.json").read_text(encoding="utf-8"))
JS = json.loads((HERE / "jscpd" / "jscpd-report.json").read_text(encoding="utf-8"))

COG_THRESHOLD = 15
DEV_MIN_PER_LOC = 30          # SonarQube default: cost to develop one line of code = 30 min
HOURS_PER_DAY = 8

items = []


def item(key, category, debt_type, tool, count, unit, formula, minutes, note=""):
    items.append({"key": key, "category": category, "debt_type": debt_type, "tool": tool, "count": count,
                  "unit": unit, "formula": formula, "minutes": round(minutes), "note": note})


# 1. complex functions -------------------------------------------------------------------------
over = sorted(((r["complexity"], r["path"].replace("\\", "/"), r["function_name"].replace("::", "."))
               for r in CPX if r["complexity"] > COG_THRESHOLD), reverse=True)
cost = sum(5 + (c - COG_THRESHOLD) for c, _, _ in over)
item("R1", "Over-complex functions (cognitive complexity > 15)", "Code debt", "complexipy", len(over), "functions",
     "5 min + 1 min per point above 15", cost)

# 2. duplication --------------------------------------------------------------------------------
clones = JS["statistics"]["total"]["clones"]
item("R2", "Duplicated blocks", "Design debt", "jscpd", clones, "clone pairs",
     "20 min per clone pair (extract shared helper, redirect both call sites)", clones * 20)

# 3. coverage -----------------------------------------------------------------------------------
cov = S["coverage"]
unc_lines = cov["missing"]
unc_br = cov["branches"] - cov["covered_branches"]
item("R3", "Uncovered statements", "Test debt", "coverage.py", unc_lines, "lines", "2 min per uncovered line", unc_lines * 2)
item("R4", "Uncovered branches", "Test debt", "coverage.py", unc_br, "branches", "5 min per uncovered branch", unc_br * 5)
item("R5", "Version-pinned tests (Pygments == 2.7.1) that skip in a default environment", "Test debt",
     "unittest run", 1, "test design issue", "fixed estimate: 4 h to make 111 skipped tests version-tolerant", 240)

# 4. pylint findings ----------------------------------------------------------------------------
sym = Counter(m["symbol"] for m in PL)
names = Counter()
for m in PL:
    if m["symbol"] == "invalid-name":
        names[m["message"].split(" name ")[0]] += 1

doc = sum(v for k, v in sym.items() if k.startswith("missing-"))
item("R6", "Missing docstrings (module / class / function)", "Documentation debt", "pylint C0114-C0116", doc,
     "definitions", "5 min each", doc * 5)

public_names = sum(v for k, v in names.items() if k.split()[0] in ("Method", "Function", "Class", "Attribute"))
local_names = sum(names.values()) - public_names
item("R7", "Non-PEP 8 names in the public API (camelCase methods / attributes)", "Code debt", "pylint C0103",
     public_names, "names", "15 min each (snake_case alias + deprecation shim)", public_names * 15)
item("R8", "Non-PEP 8 local / argument / constant names", "Code debt", "pylint C0103", local_names, "names",
     "2 min each", local_names * 2)

PER_SYMBOL = {  # minutes per finding
    "consider-using-f-string": 2, "wrong-import-order": 1, "attribute-defined-outside-init": 5,
    "redefined-builtin": 5, "no-else-return": 2, "no-else-break": 2, "unnecessary-pass": 1,
    "super-init-not-called": 10, "inconsistent-return-statements": 10, "arguments-renamed": 10,
    "arguments-differ": 20, "logging-not-lazy": 2, "consider-iterating-dictionary": 2,
    "use-implicit-booleaness-not-len": 2, "consider-using-enumerate": 5, "deprecated-method": 5,
    "consider-using-with": 10, "superfluous-parens": 1, "unused-variable": 5, "unused-private-member": 5,
    "pointless-string-statement": 2, "bad-mcs-classmethod-argument": 2, "protected-access": 10,
    "import-outside-toplevel": 5, "fixme": 20,
}
EXCLUDED = {  # with the reason they carry no separate cost
    "line-too-long": "pylint default is 100 columns; the project standard is 119 (costed separately as R10)",
    "invalid-name": "costed as R7 / R8",
    "missing-function-docstring": "costed as R6", "missing-class-docstring": "costed as R6",
    "missing-module-docstring": "costed as R6",
    "too-many-branches": "same functions as R1", "too-many-nested-blocks": "same functions as R1",
    "too-many-statements": "same functions as R1", "too-many-locals": "same functions as R1",
    "duplicate-code": "costed as R2 (jscpd)",
    "too-few-public-methods": "accepted: one-method plug-in classes are the framework's extension pattern",
    "unused-argument": "accepted: signature is fixed by the base-class contract",
    "too-many-instance-attributes": "costed with the module split in R12",
    "too-many-public-methods": "costed with the module split in R12",
    "too-many-lines": "costed with the module split in R12",
}
other = {k: v for k, v in sym.items() if k not in EXCLUDED}
other_cost = sum(v * PER_SYMBOL.get(k, 5) for k, v in other.items())
item("R9", "Other pylint warnings / refactor / convention findings", "Code debt", "pylint",
     sum(other.values()), "findings", "1-20 min each, by rule (listed in `analysis/remediation.py`)", other_cost)

item("R10", "Lines over the project limit of 119 columns, in 17 modules that a `flake8: noqa` comment exempts",
     "Code debt", "line scan + flake8 config", 62, "lines", "1 min each", 62)

# 5. security -----------------------------------------------------------------------------------
ban = S["bandit"]["by_test"]
b101 = ban.get("B101 assert_used", 0)
b405 = ban.get("B405 blacklist", 0)
item("R11", "Security findings (assert in production code; xml.etree imports to review)", "Security debt", "bandit",
     b101 + b405, "findings", f"{b101} asserts x 10 min + {b405} import reviews x 2 min", b101 * 10 + b405 * 2)

# 6. structural items estimated by the team -------------------------------------------------------
item("R12", "Oversized module `inlinepatterns.py` (1,052 lines, 44 functions, MI 25.9): split by concern",
     "Design debt", "radon MI / raw", 1, "module", "fixed estimate: 8 h incl. re-export shim and test run", 480)
item("R13", "Deprecated or dead code still shipped (10 items)", "Design debt", "grep `deprecated`, pylint, TODOs",
     10, "items", "15 min each (remove + changelog entry)", 150)
item("R14", "Stale Python-version workarounds (gh-77057 override duplicated in 2 files; HTML parser TODO)",
     "Infrastructure / dependency debt", "grep", 3, "workarounds", "30 min each once the minimum Python allows", 90)

total = sum(i["minutes"] for i in items)
sloc = S["size"]["sloc"]
loc = S["size"]["loc"]
dev = sloc * DEV_MIN_PER_LOC
result = {
    "items": items,
    "total_minutes": total,
    "total_hours": round(total / 60, 1),
    "total_days": round(total / 60 / HOURS_PER_DAY, 1),
    "sloc": sloc, "loc": loc,
    "dev_cost_minutes": dev, "dev_cost_hours": round(dev / 60, 1),
    "tdr_pct": round(100 * total / dev, 2),
    "tdr_pct_physical_loc": round(100 * total / (loc * DEV_MIN_PER_LOC), 2),
    "over_threshold": [{"cog": c, "file": f, "function": fn, "minutes": 5 + c - COG_THRESHOLD} for c, f, fn in over],
    "pylint_other": sorted(((k, v, PER_SYMBOL.get(k, 5), v * PER_SYMBOL.get(k, 5)) for k, v in other.items()),
                           key=lambda x: -x[3]),
    "pylint_excluded": {k: (sym.get(k, 0), why) for k, why in EXCLUDED.items()},
    "invalid_name_kinds": dict(names),
    "by_type": {},
}
for i in items:
    result["by_type"][i["debt_type"]] = result["by_type"].get(i["debt_type"], 0) + i["minutes"]
(HERE / "remediation.json").write_text(json.dumps(result, indent=1), encoding="utf-8")

for i in items:
    print(f'{i["key"]:4} {i["minutes"]:5} min  {i["count"]:4} {i["unit"]:18} {i["category"][:70]}')
print("TOTAL", total, "min =", result["total_hours"], "h =", result["total_days"], "days")
print("dev cost", dev, "min =", result["dev_cost_hours"], "h ; TDR =", result["tdr_pct"], "%  (physical LOC:",
      result["tdr_pct_physical_loc"], "%)")
print("by type", result["by_type"])
print("invalid-name kinds", dict(names))
print("functions over threshold:", len(over))
for c, f, fn in over:
    print("   ", c, f, fn)
print("other pylint:", result["pylint_other"])
