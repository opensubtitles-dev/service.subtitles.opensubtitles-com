#!/usr/bin/env python3
"""Greptile simulator: static gate encoding every finding class Greptile
raised across 37 review rounds (internal PRs #45-#82), so code that would
fail its review never ships.

Finding classes and where they came from are cataloged in
docs/greptile_findings_catalog.md. This gate covers the MECHANICALLY
detectable classes; the judgment-call classes (races, over-constrained
retries, degrade-not-abort) live in the catalog's review checklist.

Rules (each maps to a shipped regression):
  G01 type-identity comparison   `x is str` / `x is list`   (broken setters, 1.0.65)
  G02 nonexistent str methods    `.length()`                 (moviehash setter, 1.0.65)
  G03 raw exception in log       log(f"... {e}")             (token-bearing messages, 1.0.59/68)
  G04 raw sys.argv in log                                     (invocation-args leak, 1.0.52)
  G05 raw r.url / .url in log                                 (prepared-URL leak, 1.0.70)
  G06 whole dict interpolated in log                          (media_data/params leaks, 1.0.53/75/76)
  G07 os.path.basename on path-like args outside utilities    (token in basename, 1.0.29/42/57)
  G08 unquote(x.get(...)) without None guard                  (missing languages, 1.0.50)
  G09 true division feeding an index                           (multipart RAR, 1.0.71)
  G10 truthiness gate on season/episode coordinates            (season 0 dropped, 1.0.57/58)
  G11 bare int()/float() of external values outside try        (malformed size, 1.0.69)

Silence a deliberate exception with an inline pragma on the same line:
    ...  # greptile-ok: <reason>
"""
import ast
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# the shipped set only - dev tooling and tests are not reviewed upstream
SHIPPED_DIRS = ("resources/lib",)
SHIPPED_ROOT_GLOBS = ("service.py", "clear_cache.py", "check_updates.py",
                      "test_connection.py")

TYPE_NAMES = {"str", "list", "dict", "int", "float", "tuple", "set", "bytes"}
DICTISH_NAMES = {"item", "data", "media_data", "params", "query", "result",
                 "body", "payload", "file_data", "language_data", "attributes",
                 "response_json", "kwargs"}
COORD_NAMES = {"season", "episode", "season_number", "episode_number"}
EXTERNAL_VALUE_HINTS = ("getInfoLabel", "getProperty", "getSetting", "orig_",
                        "params[", "params.get", ".get(")
LOG_FUNC_NAMES = {"log", "logging", "error"}


def shipped_files():
    files = []
    for d in SHIPPED_DIRS:
        for root, _dirs, names in os.walk(os.path.join(REPO, d)):
            files += [os.path.join(root, n) for n in names if n.endswith(".py")]
    files += [os.path.join(REPO, g) for g in SHIPPED_ROOT_GLOBS
              if os.path.exists(os.path.join(REPO, g))]
    return sorted(files)


class Gate(ast.NodeVisitor):
    def __init__(self, path, source):
        self.path = path
        self.rel = os.path.relpath(path, REPO)
        self.source = source
        self.lines = source.splitlines()
        self.findings = []
        self.try_depth = 0
        self.except_names = []          # active exception-handler variable names

    # -- helpers ----------------------------------------------------------
    def ok(self, node):
        line = self.lines[node.lineno - 1] if node.lineno <= len(self.lines) else ""
        return "greptile-ok:" in line

    def flag(self, node, rule, msg):
        if not self.ok(node):
            self.findings.append(f"{self.rel}:{node.lineno}: {rule} {msg}")

    def _fstring_values(self, node):
        """FormattedValue expressions inside any JoinedStr below node."""
        for sub in ast.walk(node):
            if isinstance(sub, ast.FormattedValue):
                yield sub

    def _is_log_call(self, node):
        f = node.func
        name = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
        return name in LOG_FUNC_NAMES

    # -- visitors ---------------------------------------------------------
    def visit_Compare(self, node):
        # G01: `x is str` compares an instance to the type object
        left_is_type_call = (isinstance(node.left, ast.Call)
                             and isinstance(node.left.func, ast.Name)
                             and node.left.func.id == "type")
        for op, comp in zip(node.ops, node.comparators):
            if isinstance(op, (ast.Is, ast.IsNot)) and isinstance(comp, ast.Name) \
                    and comp.id in TYPE_NAMES and not left_is_type_call:
                self.flag(node, "G01", f"'is {comp.id}' compares against the type "
                                       "object - use isinstance()")
        self.generic_visit(node)

    def visit_Try(self, node):
        self.try_depth += 1
        for handler in node.handlers:
            if handler.name:
                self.except_names.append(handler.name)
        self.generic_visit(node)
        for handler in node.handlers:
            if handler.name and handler.name in self.except_names:
                self.except_names.remove(handler.name)
        self.try_depth -= 1

    def visit_Call(self, node):
        func = node.func
        # G02: nonexistent .length()
        if isinstance(func, ast.Attribute) and func.attr == "length":
            self.flag(node, "G02", ".length() does not exist on str - use len()")

        if self._is_log_call(node):
            self._check_log_call(node)

        # G07: os.path.basename on a path-like expression outside utilities.py
        if (isinstance(func, ast.Attribute) and func.attr == "basename"
                and not self.rel.endswith("utilities.py") and node.args):
            arg_src = ast.get_source_segment(self.source, node.args[0]) or ""
            if re.search(r"path|url", arg_src, re.IGNORECASE):
                self.flag(node, "G07", "basename on a path-like value - a URL keeps "
                                       "its query; use utilities.safe_media_filename")

        # G08: unquote(x.get("k")) - .get default None crashes unquote
        if isinstance(func, ast.Name) and func.id == "unquote" and node.args:
            a = node.args[0]
            if isinstance(a, ast.Call) and isinstance(a.func, ast.Attribute) \
                    and a.func.attr == "get" and len(a.args) == 1:
                self.flag(node, "G08", "unquote(x.get(...)) crashes when the key is "
                                       "missing - add a default or `or \"\"`")

        # G11: bare numeric coercion of external values outside try
        if isinstance(func, ast.Name) and func.id in ("int", "float") \
                and node.args and self.try_depth == 0:
            arg_src = ast.get_source_segment(self.source, node.args[0]) or ""
            if any(h in arg_src for h in EXTERNAL_VALUE_HINTS):
                self.flag(node, "G11", f"{func.id}() of an external value outside "
                                       "try - malformed input aborts the caller")
        self.generic_visit(node)

    def _check_log_call(self, node):
        # Non-f-string blind spots: bare Name arguments, %-format, .format()
        for arg in node.args:
            # log(__name__, attributes) / logging(params) - whole payload dumps
            if isinstance(arg, ast.Name):
                if arg.id in DICTISH_NAMES:
                    self.flag(node, "G06", f"whole '{arg.id}' passed to log - "
                                           "redact URL-shaped values first")
                if arg.id in self.except_names:
                    self.flag(node, "G03", f"raw exception '{arg.id}' passed to log "
                                           "- log type(e).__name__")
            # log("... %s" % media_data)
            if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Mod):
                right = arg.right
                names = [right] if isinstance(right, ast.Name) else (
                    [e for e in right.elts if isinstance(e, ast.Name)]
                    if isinstance(right, ast.Tuple) else [])
                for n in names:
                    if n.id in DICTISH_NAMES and not (
                            isinstance(arg.right, ast.DictComp) or "redact" in
                            (ast.get_source_segment(self.source, arg) or "")):
                        self.flag(node, "G06", f"whole '{n.id}' %-formatted into log "
                                               "- redact URL-shaped values first")
                    if n.id in self.except_names:
                        self.flag(node, "G03", f"raw exception '{n.id}' %-formatted "
                                               "into log - log type(e).__name__")
        # error(module, msg_id, e, ...) - the msg positional goes raw into log()
        f = node.func
        fname = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
        if fname == "error" and len(node.args) >= 3:
            third = node.args[2]
            if isinstance(third, ast.Name) and third.id in self.except_names:
                self.flag(node, "G03", "exception object passed as error() msg - "
                                       "it is logged raw; use detail= for the dialog")
        for fv in self._fstring_values(node):
            expr, src = fv.value, ast.get_source_segment(self.source, fv.value) or ""
            # G03: raw exception variable
            if isinstance(expr, ast.Name) and expr.id in self.except_names:
                self.flag(node, "G03", f"raw exception '{expr.id}' in log - messages "
                                       "embed paths/URLs; log type(e).__name__")
            # G04: sys.argv
            if "sys.argv" in src or (isinstance(expr, ast.Name) and expr.id == "argv"):
                self.flag(node, "G04", "sys.argv in log - caller add-ons embed "
                                       "tokens; log a whitelist of params")
            # G05: prepared request URL
            if isinstance(expr, ast.Attribute) and expr.attr == "url":
                self.flag(node, "G05", "raw .url in log - the prepared URL repeats "
                                       "every parameter; wrap in redact_path")
            # G06: whole dict-ish object
            if isinstance(expr, ast.Name) and expr.id in DICTISH_NAMES:
                self.flag(node, "G06", f"whole '{expr.id}' interpolated in log - "
                                       "redact URL-shaped values first")
        # G04/G06 also via %-format and str concat: cheap source check
        src = ast.get_source_segment(self.source, node) or ""
        if "sys.argv" in src and "G04" not in "".join(self.findings[-3:]):
            self.flag(node, "G04", "sys.argv reaches a log call")

    def visit_BinOp(self, node):
        # G09: true division whose result names/feeds an index or part count
        if isinstance(node.op, ast.Div):
            seg = ast.get_source_segment(self.source, node) or ""
            if re.search(r"size|count|body|split|index|seek", seg, re.IGNORECASE):
                self.flag(node, "G09", "true division on sizes/indices - Python 3 "
                                       "yields float; use // for indices")
        self.generic_visit(node)

    def visit_If(self, node):
        self._check_truthiness(node.test, node)
        self.generic_visit(node)

    def _check_truthiness(self, test, node):
        # G10: bare truthiness on season/episode drops legitimate 0
        values = test.values if isinstance(test, ast.BoolOp) else [test]
        for v in values:
            if isinstance(v, ast.Name) and v.id in COORD_NAMES:
                self.flag(node, "G10", f"truthiness on '{v.id}' drops 0 (specials) - "
                                       "compare against None/empty explicitly")


def run():
    all_findings = []
    for path in shipped_files():
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            all_findings.append(f"{os.path.relpath(path, REPO)}: SYNTAX {e}")
            continue
        gate = Gate(path, source)
        gate.visit(tree)
        all_findings += gate.findings
    return all_findings


if __name__ == "__main__":
    findings = run()
    if findings:
        print("== greptile-gate: FAILED ==")
        for f in findings:
            print("  " + f)
        sys.exit(1)
    print("== greptile-gate: PASSED (0 findings across shipped set) ==")
