"""Step-by-step Cyclomatic / Cognitive Complexity and comment-density derivations.

Produces, for each selected file, the line-by-line increments a person would write down when doing the
calculation by hand, so the hand-written appendix can be checked against it.

  python manual_calc.py            -> writes manual_calc.json for the six appendix files
  python manual_calc.py --validate -> compares the rule set against radon / complexipy for the whole package
"""
import ast
import io
import json
import sys
import tokenize
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parent / "markdown"

FILES = [
    "markdown/extensions/def_list.py",
    "markdown/extensions/meta.py",
    "markdown/extensions/admonition.py",
    "markdown/extensions/wikilinks.py",
    "markdown/postprocessors.py",
    "markdown/extensions/legacy_attrs.py",
]

FUNC = (ast.FunctionDef, ast.AsyncFunctionDef)


# ------------------------------------------------------------------ cyclomatic complexity (McCabe)
def cyclomatic(func, include_closures=True):
    """Return (total, steps). Rule: CC = 1 + number of decision points."""
    steps = []

    def add(node, what, n=1):
        steps.append({"line": node.lineno, "what": what, "inc": n})

    def walk(node):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, FUNC) and not include_closures:
                continue
            if isinstance(child, ast.If):
                add(child, "if / elif")
            elif isinstance(child, ast.IfExp):
                add(child, "conditional expression (x if c else y)")
            elif isinstance(child, (ast.For, ast.AsyncFor)):
                add(child, "for loop")
                if child.orelse:
                    add(child, "for ... else")
            elif isinstance(child, ast.While):
                add(child, "while loop")
                if child.orelse:
                    add(child, "while ... else")
            elif isinstance(child, ast.Try):
                for h in child.handlers:
                    add(h, "except clause")
                if child.orelse:
                    add(child, "try ... else")
            elif isinstance(child, ast.BoolOp):
                op = "and" if isinstance(child.op, ast.And) else "or"
                add(child, f"boolean operator '{op}' x{len(child.values) - 1}", len(child.values) - 1)
            elif isinstance(child, ast.comprehension):
                add(child.target, "comprehension 'for'")
                if child.ifs:
                    add(child.ifs[0], f"comprehension 'if' x{len(child.ifs)}", len(child.ifs))
            elif isinstance(child, ast.Assert):
                add(child, "assert")
            elif isinstance(child, ast.Match):
                add(child, f"match with {len(child.cases)} case(s)", len(child.cases))
            walk(child)

    walk(func)
    steps.sort(key=lambda s: s["line"])
    return 1 + sum(s["inc"] for s in steps), steps


# ------------------------------------------------------------------ cognitive complexity (SonarSource)
def cognitive(func, count_comprehension=False, lines=None):
    """Return (total, steps) following G. A. Campbell, 'Cognitive Complexity' (SonarSource).

    B1  +1 for each break in linear flow: if, elif, else, loop, except, conditional expression,
        each sequence of like boolean operators.
    B2  +1 extra per level of nesting for: if, loop, except, conditional expression
        (elif / else / boolean sequences get no nesting penalty).
    B3  nesting level rises inside: if / elif / else, loops, except, nested functions and lambdas.
    """
    steps = []

    def else_line(first_stmt_line):
        """Line of the `else:` keyword that precedes the first statement of an else block."""
        ln = first_stmt_line - 1
        while lines and ln > 0 and not lines[ln - 1].strip().startswith("else"):
            ln -= 1
        return ln if ln > 0 else first_stmt_line - 1

    def add(line, what, nesting, structural=True):
        steps.append({"line": line, "what": what, "nesting": nesting if structural else None,
                      "inc": 1 + (nesting if structural else 0)})

    def visit_if(node, nesting, is_elif=False):
        if is_elif:
            add(node.lineno, "elif", nesting, structural=False)
        else:
            add(node.lineno, "if", nesting)
        expr(node.test, nesting)
        body(node.body, nesting + 1)
        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If) \
                    and node.orelse[0].col_offset == node.col_offset:
                visit_if(node.orelse[0], nesting, is_elif=True)
            else:
                add(else_line(node.orelse[0].lineno), "else", nesting, structural=False)
                body(node.orelse, nesting + 1)

    def expr(node, nesting):
        """Walk an expression tree looking for boolean sequences, ternaries, lambdas, comprehensions."""
        if node is None:
            return
        if isinstance(node, ast.BoolOp):
            op = "and" if isinstance(node.op, ast.And) else "or"
            add(node.lineno, f"sequence of '{op}'", nesting, structural=False)
            for v in node.values:
                expr(v, nesting)
            return
        if isinstance(node, ast.IfExp):
            add(node.lineno, "conditional expression", nesting)
            expr(node.test, nesting)
            expr(node.body, nesting + 1)
            expr(node.orelse, nesting + 1)
            return
        if isinstance(node, ast.Lambda):
            expr(node.body, nesting + 1)
            return
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            if count_comprehension:
                for gen in node.generators:
                    add(gen.target.lineno, "comprehension 'for'", nesting)
                    for cond in gen.ifs:
                        add(cond.lineno, "comprehension 'if'", nesting, structural=False)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.expr, ast.comprehension, ast.keyword)):
                expr(child, nesting)

    def body(stmts, nesting):
        for st in stmts:
            stmt(st, nesting)

    def stmt(node, nesting):
        if isinstance(node, ast.If):
            visit_if(node, nesting)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            add(node.lineno, "for loop", nesting)
            expr(node.iter, nesting)
            body(node.body, nesting + 1)
            if node.orelse:
                add(else_line(node.orelse[0].lineno), "else (loop)", nesting, structural=False)
                body(node.orelse, nesting + 1)
        elif isinstance(node, ast.While):
            add(node.lineno, "while loop", nesting)
            expr(node.test, nesting)
            body(node.body, nesting + 1)
            if node.orelse:
                add(else_line(node.orelse[0].lineno), "else (loop)", nesting, structural=False)
                body(node.orelse, nesting + 1)
        elif isinstance(node, ast.Try):
            body(node.body, nesting)
            for h in node.handlers:
                add(h.lineno, "except", nesting)
                body(h.body, nesting + 1)
            body(node.orelse, nesting)
            body(node.finalbody, nesting)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                expr(item.context_expr, nesting)
            body(node.body, nesting)
        elif isinstance(node, FUNC):
            body(node.body, nesting + 1)          # closure: counted in the enclosing function
        elif isinstance(node, ast.ClassDef):
            body(node.body, nesting + 1)
        elif isinstance(node, ast.Match):
            add(node.lineno, "match", nesting)
            for case in node.cases:
                body(case.body, nesting + 1)
        else:
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.expr):
                    expr(child, nesting)

    body(func.body, 0)
    steps.sort(key=lambda s: s["line"])
    return sum(s["inc"] for s in steps), steps


# ------------------------------------------------------------------ line classification
def classify_lines(source):
    """Classify every physical line as blank / comment / docstring / code (+ 'mixed' flag)."""
    lines = source.splitlines()
    n = len(lines)
    kind = ["code"] * (n + 1)
    doc_lines = set()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        # any stand-alone string literal statement is documentation (docstring / attribute docstring)
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            doc_lines.update(range(node.lineno, node.end_lineno + 1))
    comment_only, mixed = set(), set()
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == tokenize.COMMENT:
            ln = tok.start[0]
            if lines[ln - 1].lstrip().startswith("#"):
                comment_only.add(ln)
            else:
                mixed.add(ln)
    for i in range(1, n + 1):
        text = lines[i - 1]
        if not text.strip():
            kind[i] = "blank"
        elif i in doc_lines:
            kind[i] = "docstring"
        elif i in comment_only:
            kind[i] = "comment"
        else:
            kind[i] = "code"
    return kind[1:], sorted(mixed)


def ranges(nums):
    out, start, prev = [], None, None
    for x in nums:
        if start is None:
            start = prev = x
        elif x == prev + 1:
            prev = x
        else:
            out.append((start, prev))
            start = prev = x
    if start is not None:
        out.append((start, prev))
    return [f"{a}" if a == b else f"{a}-{b}" for a, b in out]


# ------------------------------------------------------------------ per-file driver
def top_functions(tree):
    """Yield (qualified name, node) for functions and methods (closures stay inside their parent)."""
    for node in tree.body:
        if isinstance(node, FUNC):
            yield node.name, node
        elif isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, FUNC):
                    yield f"{node.name}.{sub.name}", sub


def analyse(rel):
    src = (REPO / rel).read_text(encoding="utf-8")
    tree = ast.parse(src)
    kinds, mixed = classify_lines(src)
    count = {k: kinds.count(k) for k in ("blank", "comment", "docstring", "code")}
    comment_lines = count["comment"] + count["docstring"]
    funcs = []
    for name, node in top_functions(tree):
        # Cyclomatic: every function is its own unit, so a closure is listed separately (as radon does).
        # Cognitive: a closure is charged to the function that contains it, one nesting level deeper.
        cc, cc_steps = cyclomatic(node, include_closures=False)
        cog, cog_steps = cognitive(node, lines=src.splitlines())
        funcs.append({"name": name, "start": node.lineno, "end": node.end_lineno,
                      "cc": cc, "cc_steps": cc_steps, "cog": cog, "cog_steps": cog_steps})
        for inner in ast.walk(node):
            if isinstance(inner, FUNC) and inner is not node:
                icc, isteps = cyclomatic(inner, include_closures=False)
                funcs.append({"name": f"{name}.<closure> {inner.name}", "start": inner.lineno,
                              "end": inner.end_lineno, "cc": icc, "cc_steps": isteps,
                              "cog": None, "cog_steps": [], "closure": True})
    return {
        "file": rel,
        "total_lines": len(kinds),
        "counts": count,
        "mixed_lines": mixed,
        "line_ranges": {k: ranges([i + 1 for i, v in enumerate(kinds) if v == k])
                        for k in ("blank", "comment", "docstring", "code")},
        "comment_lines": comment_lines,
        "comment_density": round(100 * comment_lines / (comment_lines + count["code"]), 2),
        "comment_ratio_total": round(100 * comment_lines / len(kinds), 2),
        "functions": funcs,
        "cc_total": sum(f["cc"] for f in funcs),
        "cc_max": max(f["cc"] for f in funcs),
        "cc_avg": round(sum(f["cc"] for f in funcs) / len(funcs), 2),
        "cog_total": sum(f["cog"] or 0 for f in funcs),
        "cog_max": max(f["cog"] or 0 for f in funcs),
    }


def validate():
    radon = json.loads((HERE / "radon_cc.json").read_text(encoding="utf-8"))
    cpx = json.loads((HERE / "complexipy.json").read_text(encoding="utf-8"))
    cpx_map = {(r["path"].replace("\\", "/"), r["function_name"].replace("::", ".")): r["complexity"] for r in cpx}
    cc_bad = cog_bad = cog_bad_c = total = 0
    for path in sorted((REPO / "markdown").rglob("*.py")):
        rel = path.relative_to(REPO).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        rmap = {}
        for it in radon.get(rel.replace("/", "\\"), []):
            def tot(x):
                return x["complexity"] + sum(tot(c) for c in x.get("closures", []))
            if it["type"] == "class":
                for m in it["methods"]:
                    rmap[f'{it["name"]}.{m["name"]}'] = tot(m)
            elif it["type"] == "function":
                rmap[it["name"]] = tot(it)
        for name, node in top_functions(tree):
            total += 1
            cc, _ = cyclomatic(node)
            n_closures = sum(1 for x in ast.walk(node) if isinstance(x, FUNC) and x is not node)
            # radon reports closures separately, each with its own +1 base
            if cc + n_closures != rmap.get(name):
                cc_bad += 1
                print("CC  ", rel, name, "mine", cc + n_closures, "radon(+closures)", rmap.get(name))
            cog, _ = cognitive(node)
            cog_c, _ = cognitive(node, count_comprehension=True)
            ref = cpx_map.get((rel, name))
            if cog != ref:
                cog_bad += 1
            if cog_c != ref:
                cog_bad_c += 1
                print("COG ", rel, name, "sonar-rule", cog, "with-comprehension", cog_c, "complexipy", ref)
    print(f"functions={total}  CC mismatches={cc_bad}  cognitive mismatches: plain={cog_bad}, "
          f"counting comprehensions={cog_bad_c}")


if __name__ == "__main__":
    if "--validate" in sys.argv:
        validate()
    else:
        data = [analyse(f) for f in FILES]
        (HERE / "manual_calc.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
        for d in data:
            print(f'\n{d["file"]}: lines={d["total_lines"]} {d["counts"]} mixed={d["mixed_lines"]} '
                  f'density={d["comment_density"]}%  CC total={d["cc_total"]} max={d["cc_max"]}  '
                  f'Cog total={d["cog_total"]} max={d["cog_max"]}')
            for f in d["functions"]:
                print(f'   {f["name"]:45} CC={f["cc"]:3}  Cog={f["cog"]!s:>4}')
