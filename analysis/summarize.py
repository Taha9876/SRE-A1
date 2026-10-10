"""Aggregate the raw tool outputs in this folder into one summary (printed + summary.json)."""
import csv
import json
import statistics
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parent / "markdown"


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def norm(p):
    return str(p).replace("\\", "/")


out = {}

# ---------------------------------------------------------------- size (radon raw)
raw = {norm(k): v for k, v in load("radon_raw.json").items()}
tot = Counter()
for v in raw.values():
    for k in ("loc", "lloc", "sloc", "comments", "multi", "blank", "single_comments"):
        tot[k] += v[k]
out["size"] = dict(tot)
out["files"] = len(raw)

# ---------------------------------------------------------------- cyclomatic (radon cc)
cc = {norm(k): v for k, v in load("radon_cc.json").items()}
blocks = []           # functions + methods (classes excluded: radon reports them as an average)
n_classes = 0
per_file_cc = defaultdict(list)
def add_block(f, name, b):
    blocks.append((f, name, b["complexity"], b["rank"], b["lineno"], b["endline"]))
    per_file_cc[f].append(b["complexity"])
    for c in b.get("closures", []):          # nested functions are separate units for McCabe
        add_block(f, f'{name}.{c["name"]}', c)


for f, items in cc.items():
    for it in items:
        if it["type"] == "class":
            n_classes += 1
            for m in it.get("methods", []):
                add_block(f, f'{it["name"]}.{m["name"]}', m)
        elif it["type"] == "function":
            add_block(f, it["name"], it)
        # methods also appear top-level with type == "method": already counted via the class

ccs = [b[2] for b in blocks]
out["cc"] = {
    "blocks": len(blocks),
    "classes": n_classes,
    "total": sum(ccs),
    "mean": round(statistics.mean(ccs), 2),
    "median": statistics.median(ccs),
    "max": max(ccs),
    "rank_dist": dict(sorted(Counter(b[3] for b in blocks).items())),
    "over_10": sum(1 for c in ccs if c > 10),
    "over_15": sum(1 for c in ccs if c > 15),
    "top": sorted(blocks, key=lambda b: -b[2])[:15],
}

# ---------------------------------------------------------------- cognitive (complexipy)
cog_raw = load("complexipy.json")
cog = []
per_file_cog = defaultdict(list)
for row in cog_raw:
    f = norm(row.get("path") or row.get("file_name"))
    if not f.startswith("markdown/"):
        f = "markdown/" + f.split("markdown/", 1)[-1] if "markdown/" in f else "markdown/" + f
    cog.append((f, row["function_name"], row["complexity"]))
    per_file_cog[f].append(row["complexity"])
cogs = [c[2] for c in cog]
out["cognitive"] = {
    "functions": len(cog),
    "total": sum(cogs),
    "mean": round(statistics.mean(cogs), 2),
    "max": max(cogs),
    "over_15": sum(1 for c in cogs if c > 15),
    "over_25": sum(1 for c in cogs if c > 25),
    "top": sorted(cog, key=lambda c: -c[2])[:15],
}

# ---------------------------------------------------------------- maintainability index
mi = {norm(k): v for k, v in load("radon_mi.json").items()}
mis = [v["mi"] for v in mi.values()]
out["mi"] = {
    "mean": round(statistics.mean(mis), 2),
    "min": round(min(mis), 2),
    "rank_dist": dict(Counter(v["rank"] for v in mi.values())),
    "lowest": sorted(((f, round(v["mi"], 2), v["rank"]) for f, v in mi.items()), key=lambda x: x[1])[:8],
}
# SLOC-weighted MI
w = sum(mi[f]["mi"] * raw[f]["sloc"] for f in mi) / sum(raw[f]["sloc"] for f in mi)
out["mi"]["sloc_weighted"] = round(w, 2)

# ---------------------------------------------------------------- coverage
cov = load("coverage.json")
t = cov["totals"]
out["coverage"] = {
    "statements": t["num_statements"],
    "missing": t["missing_lines"],
    "statement_pct": round(100 * t["covered_lines"] / t["num_statements"], 2),
    "branches": t["num_branches"],
    "covered_branches": t["covered_branches"],
    "partial_branches": t["num_partial_branches"],
    "branch_pct": round(100 * t["covered_branches"] / t["num_branches"], 2),
    "combined_pct": round(t["percent_covered"], 2),
}
per_file_cov = {}
for f, v in cov["files"].items():
    s = v["summary"]
    per_file_cov[norm(f)] = {
        "stmt": round(100 * s["covered_lines"] / s["num_statements"], 1) if s["num_statements"] else 100.0,
        "branch": round(100 * s["covered_branches"] / s["num_branches"], 1) if s["num_branches"] else 100.0,
        "missing": s["missing_lines"],
        "missing_branches": s["num_branches"] - s["covered_branches"],
    }

# ---------------------------------------------------------------- duplication (jscpd)
js = load("jscpd/jscpd-report.json")
st = js["statistics"]["total"]
out["duplication"] = {
    "clones": st["clones"],
    "duplicated_lines": st["duplicatedLines"],
    "pct_lines": round(st["percentage"], 2),
    "pct_tokens": round(st.get("percentageTokens", 0), 2),
    "pairs": [
        (norm(d["firstFile"]["name"]), d["firstFile"]["start"], d["firstFile"]["end"],
         norm(d["secondFile"]["name"]), d["secondFile"]["start"], d["secondFile"]["end"], d["lines"])
        for d in js["duplicates"]
    ],
}
dup_by_file = Counter()
for d in js["duplicates"]:
    dup_by_file[norm(d["firstFile"]["name"])] += d["lines"]
    dup_by_file[norm(d["secondFile"]["name"])] += d["lines"]

# ---------------------------------------------------------------- bandit (vulnerabilities)
ban = load("bandit.json")
out["bandit"] = {
    "by_severity": dict(Counter(r["issue_severity"] for r in ban["results"])),
    "by_confidence": dict(Counter(r["issue_confidence"] for r in ban["results"])),
    "by_test": dict(Counter(f'{r["test_id"]} {r["test_name"]}' for r in ban["results"])),
    "items": [(norm(r["filename"]), r["line_number"], r["test_id"], r["issue_severity"], r["issue_confidence"],
               r["issue_text"]) for r in ban["results"]],
}

# ---------------------------------------------------------------- pylint (bugs / smells)
pl = load("pylint.json")
msgs = pl["messages"]
out["pylint"] = {
    "score": pl["statistics"]["score"],
    "by_type": dict(Counter(m["type"] for m in msgs)),
    "by_symbol": Counter(m["symbol"] for m in msgs).most_common(40),
}
pylint_by_file = defaultdict(Counter)
for m in msgs:
    pylint_by_file[norm(m["path"])][m["type"]] += 1

# ---------------------------------------------------------------- git churn (hotspots)
log = subprocess.run(
    ["git", "-C", str(REPO), "log", "--since=3 years ago", "--name-only", "--format=@%H|%s", "--", "markdown"],
    capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
churn = Counter()
fix = Counter()
cur_fix = False
commits = 0
for line in log.splitlines():
    if line.startswith("@"):
        commits += 1
        subj = line.split("|", 1)[1].lower()
        cur_fix = any(k in subj for k in ("fix", "bug", "regress", "crash", "error", "issue"))
    elif line.strip():
        churn[line.strip()] += 1
        if cur_fix:
            fix[line.strip()] += 1
out["git"] = {"commits_3y_touching_pkg": commits}

alltime = subprocess.run(
    ["git", "-C", str(REPO), "log", "--name-only", "--format=", "--", "markdown"],
    capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
churn_all = Counter(l.strip() for l in alltime.splitlines() if l.strip())

# ---------------------------------------------------------------- per-file table
rows = []
for f in sorted(raw):
    r = raw[f]
    rows.append({
        "file": f,
        "loc": r["loc"], "sloc": r["sloc"], "lloc": r["lloc"],
        "comments": r["comments"], "multi": r["multi"], "blank": r["blank"],
        "comment_density": round(100 * (r["comments"] + r["multi"]) / r["loc"], 1) if r["loc"] else 0,
        "funcs": len(per_file_cc.get(f, [])),
        "cc_sum": sum(per_file_cc.get(f, [])),
        "cc_max": max(per_file_cc.get(f, [0])),
        "cc_avg": round(statistics.mean(per_file_cc[f]), 2) if per_file_cc.get(f) else 0,
        "cog_sum": sum(per_file_cog.get(f, [])),
        "cog_max": max(per_file_cog.get(f, [0])),
        "mi": round(mi[f]["mi"], 1), "mi_rank": mi[f]["rank"],
        "cov_stmt": per_file_cov.get(f, {}).get("stmt"),
        "cov_branch": per_file_cov.get(f, {}).get("branch"),
        "missing": per_file_cov.get(f, {}).get("missing", 0),
        "missing_branches": per_file_cov.get(f, {}).get("missing_branches", 0),
        "dup_lines": dup_by_file.get(f.split("markdown/", 1)[1], 0) or dup_by_file.get(f, 0),
        "churn_3y": churn.get(f, 0), "fix_3y": fix.get(f, 0), "churn_all": churn_all.get(f, 0),
        "pylint": dict(pylint_by_file.get(f, {})),
    })
out["per_file"] = rows

(HERE / "summary.json").write_text(json.dumps(out, indent=1), encoding="utf-8")

with open(HERE / "per_file_metrics.csv", "w", newline="", encoding="utf-8") as fh:
    cols = [c for c in rows[0] if c != "pylint"]
    w_ = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w_.writeheader()
    w_.writerows(rows)

for k in ("size", "files", "cc", "cognitive", "mi", "coverage", "bandit", "pylint", "git"):
    print(f"\n== {k}")
    print(json.dumps(out[k], indent=1))
print("\n== duplication")
print({k: v for k, v in out["duplication"].items() if k != "pairs"})
print("\n== per file")
print(f'{"file":40} {"loc":>5} {"sloc":>5} {"fn":>3} {"ccS":>4} {"ccM":>3} {"cgS":>4} {"cgM":>3} {"mi":>5} {"st%":>5} {"br%":>5} {"dup":>3} {"ch3":>3} {"fx3":>3} {"chA":>3}')
for r in rows:
    print(f'{r["file"]:40} {r["loc"]:5} {r["sloc"]:5} {r["funcs"]:3} {r["cc_sum"]:4} {r["cc_max"]:3} {r["cog_sum"]:4} {r["cog_max"]:3} {r["mi"]:5} {r["cov_stmt"]!s:>5} {r["cov_branch"]!s:>5} {r["dup_lines"]:3} {r["churn_3y"]:3} {r["fix_3y"]:3} {r["churn_all"]:3}')
