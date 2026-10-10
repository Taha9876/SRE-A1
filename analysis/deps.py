"""Internal/external import graph of the markdown package (fan-in, fan-out, instability, cycles)."""
import ast
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).parent.parent / "markdown"
PKG = REPO / "markdown"

mods = {}
for p in sorted(PKG.rglob("*.py")):
    rel = p.relative_to(REPO).with_suffix("")
    name = ".".join(rel.parts)
    if name.endswith(".__init__"):
        name = name[: -len(".__init__")]
    mods[name] = p

internal = defaultdict(set)   # runtime imports
typing_only = defaultdict(set)
lazy = defaultdict(set)       # imports inside functions
external = defaultdict(set)
stdlib = set(sys.stdlib_module_names)


def resolve(mod, cur, level):
    if level:
        base = cur.split(".")
        is_pkg = mods[cur].name == "__init__.py"
        base = base if is_pkg else base[:-1]
        base = base[: len(base) - (level - 1)]
        return ".".join(base + ([mod] if mod else []))
    return mod or ""


for name, path in mods.items():
    tree = ast.parse(path.read_text(encoding="utf-8"))

    def visit(node, in_func=False, in_tc=False):
        for child in ast.iter_child_nodes(node):
            tc = in_tc
            if isinstance(child, ast.If):
                t = ast.unparse(child.test)
                if "TYPE_CHECKING" in t:
                    tc = True
            fn = in_func or isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                targets = []
                if isinstance(child, ast.Import):
                    targets = [a.name for a in child.names]
                else:
                    base = resolve(child.module, name, child.level)
                    for a in child.names:
                        cand = f"{base}.{a.name}" if base else a.name
                        targets.append(cand if cand in mods else base)
                for t in targets:
                    hit = None
                    parts = t.split(".")
                    for i in range(len(parts), 0, -1):
                        if ".".join(parts[:i]) in mods:
                            hit = ".".join(parts[:i])
                            break
                    if hit:
                        if hit == name:
                            continue
                        (typing_only if tc else lazy if in_func else internal)[name].add(hit)
                    else:
                        external[name].add(parts[0])
            visit(child, fn, tc)

    visit(tree)

fan_out = {m: len(internal[m] | lazy[m]) for m in mods}
fan_in = defaultdict(int)
for m in mods:
    for d in internal[m] | lazy[m]:
        fan_in[d] += 1

# cycles (Tarjan SCC) on runtime graph incl. lazy imports
graph = {m: sorted(internal[m] | lazy[m]) for m in mods}
index, low, onstack, stack, sccs, counter = {}, {}, set(), [], [], [0]


def strong(v):
    index[v] = low[v] = counter[0]
    counter[0] += 1
    stack.append(v)
    onstack.add(v)
    for w in graph[v]:
        if w not in index:
            strong(w)
            low[v] = min(low[v], low[w])
        elif w in onstack:
            low[v] = min(low[v], index[w])
    if low[v] == index[v]:
        comp = []
        while True:
            w = stack.pop()
            onstack.discard(w)
            comp.append(w)
            if w == v:
                break
        if len(comp) > 1:
            sccs.append(sorted(comp))


for m in mods:
    if m not in index:
        strong(m)

ext_all = sorted({e for s in external.values() for e in s})
result = {
    "modules": len(mods),
    "edges_runtime": sum(len(v) for v in internal.values()),
    "edges_lazy": sum(len(v) for v in lazy.values()),
    "edges_type_only": sum(len(v) for v in typing_only.values()),
    "cycles": sccs,
    "stdlib": [e for e in ext_all if e in stdlib],
    "third_party": [e for e in ext_all if e not in stdlib],
    "third_party_users": {e: sorted(m for m in mods if e in external[m]) for e in ext_all if e not in stdlib},
    "table": [
        {"module": m, "fan_in": fan_in[m], "fan_out": fan_out[m],
         "instability": round(fan_out[m] / (fan_in[m] + fan_out[m]), 2) if (fan_in[m] + fan_out[m]) else 0.0,
         "imports": sorted(internal[m]), "lazy": sorted(lazy[m]), "type_only": sorted(typing_only[m]),
         "external": sorted(external[m])}
        for m in mods
    ],
}
(Path(__file__).parent / "deps.json").write_text(json.dumps(result, indent=1), encoding="utf-8")

print("modules", result["modules"], "runtime edges", result["edges_runtime"], "lazy", result["edges_lazy"],
      "type-only", result["edges_type_only"])
print("cycles:", sccs)
print("stdlib:", result["stdlib"])
print("third-party:", result["third_party_users"])
print(f'{"module":40} {"Ca":>3} {"Ce":>3} {"I":>5}  imports')
for r in sorted(result["table"], key=lambda r: -r["fan_in"]):
    s = ", ".join(x.replace("markdown.", "") for x in r["imports"])
    if r["lazy"]:
        s += "  [lazy: " + ", ".join(x.replace("markdown.", "") for x in r["lazy"]) + "]"
    if r["type_only"]:
        s += "  [type: " + ", ".join(x.replace("markdown.", "") for x in r["type_only"]) + "]"
    print(f'{r["module"]:40} {r["fan_in"]:3} {r["fan_out"]:3} {r["instability"]:5}  {s}')
