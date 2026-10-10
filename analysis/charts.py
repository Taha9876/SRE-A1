"""Figures for the report (static PNG, light surface)."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).parent
OUT = HERE / "charts"
OUT.mkdir(exist_ok=True)
S = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))

SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, BLUE_SOFT = "#2a78d6", "#eb6834", "#cde2fb"

plt.rcParams.update({
    "font.family": "Segoe UI", "font.size": 9, "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": AXIS, "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE, "axes.spines.top": False,
    "axes.spines.right": False, "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
})


def finish(fig, name):
    fig.savefig(OUT / name, dpi=220, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


# ------------------------------------------------------------------ 1. CC rank distribution
ranks = [("A", "1-5"), ("B", "6-10"), ("C", "11-20"), ("D", "21-30"), ("E", "31-40"), ("F", "41+")]
dist = S["cc"]["rank_dist"]
vals = [dist.get(r, 0) for r, _ in ranks]
fig, ax = plt.subplots(figsize=(6.3, 2.9))
bars = ax.bar([f"{r}\n({rng})" for r, rng in ranks], vals, width=0.55, color=BLUE)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.02, str(v), ha="center", va="bottom", color=INK, fontsize=9)
ax.set_ylabel("Functions / methods")
ax.set_xlabel("Cyclomatic-complexity rank (range)")
ax.set_title(f"{sum(vals)} functions by cyclomatic-complexity rank")
ax.yaxis.grid(True, color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
ax.spines["left"].set_visible(False)
ax.tick_params(length=0)
ax.set_ylim(0, max(vals) * 1.12)
finish(fig, "cc_distribution.png")

# ------------------------------------------------------------------ 2. hotspot scatter
rows = [r for r in S["per_file"] if r["file"] != "markdown/test_tools.py"]
for r in rows:
    r["hot"] = r["churn_3y"] * r["cog_sum"]
top = sorted(rows, key=lambda r: -r["hot"])[:7]
top_names = {r["file"] for r in top}
fig, ax = plt.subplots(figsize=(6.3, 3.9))
rest = [r for r in rows if r["file"] not in top_names]
ax.scatter([r["churn_3y"] for r in rest], [r["cog_sum"] for r in rest], s=34, color=MUTED, alpha=0.75,
           edgecolor=SURFACE, linewidth=1.2, label="Other modules", zorder=3)
ax.scatter([r["churn_3y"] for r in top], [r["cog_sum"] for r in top], s=60, color=BLUE,
           edgecolor=SURFACE, linewidth=1.5, label="Top 7 hotspots (churn x complexity)", zorder=4)
offsets = {"markdown/htmlparser.py": (-8, 8, "right"), "markdown/extensions/md_in_html.py": (8, 0, "left"),
           "markdown/inlinepatterns.py": (8, 4, "left"), "markdown/treeprocessors.py": (8, 4, "left"),
           "markdown/extensions/abbr.py": (0, 9, "center"), "markdown/extensions/attr_list.py": (8, 4, "left"),
           "markdown/extensions/footnotes.py": (-8, 6, "right"), "markdown/blockprocessors.py": (-8, 9, "right"),
           "markdown/extensions/toc.py": (-8, -13, "right"), "markdown/extensions/smarty.py": (8, -3, "left")}
for r in top:
    dx, dy, ha = offsets.get(r["file"], (8, 4, "left"))
    ax.annotate(r["file"].replace("markdown/", "").replace("extensions/", "ext/"), (r["churn_3y"], r["cog_sum"]),
                xytext=(dx, dy), textcoords="offset points", ha=ha, fontsize=8.5, color=INK)
ax.set_xlabel("Change frequency: commits touching the file, last 3 years")
ax.set_ylabel("Cognitive complexity of the file (sum)")
ax.set_title("Hotspots: complex code that also changes often")
ax.grid(True, color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
ax.set_xlim(-0.6, max(r["churn_3y"] for r in rows) + 2)
ax.set_ylim(-8, max(r["cog_sum"] for r in rows) * 1.12)
ax.tick_params(length=0)
ax.legend(frameon=False, loc="upper left", fontsize=8.5, labelcolor=INK2)
finish(fig, "hotspots.png")

# ------------------------------------------------------------------ 3. dependency layers
D = json.loads((HERE / "deps.json").read_text(encoding="utf-8"))
fan_in = {r["module"]: r["fan_in"] for r in D["table"]}
fig, ax = plt.subplots(figsize=(6.6, 4.5))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")


def box(x, y, w, h, title, sub="", fill=SURFACE, edge=AXIS, bold=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2", linewidth=1,
                                edgecolor=edge, facecolor=fill, zorder=2))
    ax.text(x + w / 2, y + h / 2 + (1.7 if sub else 0), title, ha="center", va="center", fontsize=8.5,
            fontweight="bold" if bold else "normal", color=INK, zorder=3)
    if sub:
        ax.text(x + w / 2, y + h / 2 - 2.2, sub, ha="center", va="center", fontsize=7.2, color=INK2, zorder=3)


def arrow(x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=9, linewidth=1,
                                 color=MUTED, zorder=1, shrinkA=0, shrinkB=0))


def layer(y, label):
    ax.text(0, y, label, ha="left", va="center", fontsize=7.5, color=MUTED, rotation=90)


layer(92, "Entry")
box(6, 87, 26, 10, "__main__  (CLI)", "optparse, yaml*")
box(38, 87, 26, 10, "markdown/__init__", "public API facade")
box(70, 87, 26, 10, "18 extensions", "plug in to the stages below", fill=BLUE_SOFT, edge=BLUE)

layer(72, "Orchestration")
box(38, 68, 26, 10, "core.Markdown", "fan-out 8 (highest)")

layer(46, "Pipeline stages")
stage = [("preprocessors", 6, 49), ("blockparser", 27, 49), ("blockprocessors", 48, 49),
         ("treeprocessors", 69, 49), ("inlinepatterns", 16.5, 37), ("postprocessors", 37.5, 37),
         ("serializers", 58.5, 37)]
for name, x, y in stage:
    box(x, y, 19.5, 9, name, f"fan-in {fan_in['markdown.' + name]}", bold=False)
ax.add_patch(FancyBboxPatch((3.5, 34.5), 87.5, 26, boxstyle="round,pad=0,rounding_size=1.5", linewidth=0.8,
                            edgecolor=GRID, facecolor="none", zorder=0))

layer(19, "Foundation")
box(6, 14, 26, 10, "htmlparser", f"fan-in {fan_in['markdown.htmlparser']}")
box(38, 14, 26, 10, "util", f"fan-in {fan_in['markdown.util']} (shared kernel)", fill=BLUE_SOFT, edge=BLUE)
box(70, 14, 26, 10, "extensions/__init__", f"Extension base, fan-in {fan_in['markdown.extensions']}",
    fill=BLUE_SOFT, edge=BLUE)

arrow(19, 87, 45, 78.3)      # CLI -> package -> core
arrow(51, 87, 51, 78.3)      # facade -> core
arrow(51, 68, 51, 60.8)      # core -> stages
arrow(78, 87, 78, 60.8)      # extensions -> stages
ax.plot([93.5, 93.5], [87, 34.5], color=MUTED, linewidth=1, zorder=1)      # extensions -> Extension base (passes behind the stage group)
arrow(93.5, 34.5, 93.5, 24.3)
arrow(51, 34.5, 51, 24.3)    # stages -> util
arrow(16, 34.5, 16, 24.3)    # preprocessors -> htmlparser
arrow(70, 19, 64.3, 19)      # Extension base -> util
ax.text(6, 7, "Arrows point from the importing module to the module it depends on.  "
              "33 modules, 79 runtime import edges, 0 import cycles.\n"
              "* optional third-party imports: PyYAML (CLI config), Pygments (codehilite), pytidylib (test_tools). "
              "Everything else is the standard library.", fontsize=7.4, color=INK2, va="top")
finish(fig, "dependencies.png")
print("charts written:", [p.name for p in OUT.glob("*.png")])
