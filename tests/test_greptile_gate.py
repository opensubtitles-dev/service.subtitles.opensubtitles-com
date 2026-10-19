"""The Greptile simulator must pass on every commit - it encodes the finding
classes from 37 review rounds so code that would fail review never ships."""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_greptile_gate_clean():
    result = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "greptile_gate.py")],
                            capture_output=True, text=True)
    assert result.returncode == 0, "greptile-gate findings:\n" + result.stdout


# --- G13: a response body must never reach a log line, in any shape ----------
#
# The 1.x line removed the last body-bearing log by hand (1.0.89/1.0.90) but
# never mechanized the rule, so v2's rate_subtitle reintroduced it as
# `resp.text[:100]`. These cases pin the PATTERN, not that one instance - the
# catalog's own lesson from the v1.0.78 self-audit round.

def _gate_findings(src):
    """Runs the gate's visitor over a source snippet, returns its findings."""
    import ast
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "greptile_gate", os.path.join(REPO, "scripts", "greptile_gate.py"))
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    tree = ast.parse(src)
    visitor = gate.Checker(src, "snippet.py") if hasattr(gate, "Checker") else None
    if visitor is None:  # name differs - find the ast.NodeVisitor subclass
        for obj in vars(gate).values():
            if isinstance(obj, type) and issubclass(obj, ast.NodeVisitor) \
                    and obj is not ast.NodeVisitor:
                visitor = obj(src, "snippet.py")
                break
    visitor.visit(tree)
    return visitor.findings


BODY_IN_LOG_CASES = [
    'logging(f"code {resp.status_code}: {resp.text[:100]}")',   # the real regression
    'logging(f"body: {resp.text}")',                            # bare attribute
    'logging(f"body: {r.content}")',                            # .content
    'logging(f"body: {str(resp.text)}")',                       # str() wrapper
    'logging(f"body: {resp.text.strip()}")',                    # method chain
    'logging(f"body: {(resp.text or \'\')[:50]}")',             # or-"" bypass attempt
    'logging(f"body: {requests.get(u).text}")',                 # inline response
]


def test_g13_flags_every_response_body_shape():
    for src in BODY_IN_LOG_CASES:
        findings = _gate_findings(src)
        assert any("G13" in f for f in findings), f"G13 missed: {src}"


BODY_SAFE_CASES = [
    # the sanctioned replacement: status plus emptiness, no body bytes
    'logging(f"rejected: status={resp.status_code}, empty={not (resp.text or \'\').strip()}")',
    'logging(f"size={len(resp.text)}")',          # a length is not a body
    'logging(f"label={label.text}")',             # a UI label is not a response
    'logging(f"status={resp.status_code}")',
]


def test_g13_does_not_fire_on_safe_shapes():
    for src in BODY_SAFE_CASES:
        findings = _gate_findings(src)
        assert not any("G13" in f for f in findings), f"G13 false positive: {src}"


def test_greptile_reviewer_config_present_and_exhaustive():
    """The 1.x line pinned the reviewer to strictness 1 with all comment types
    so a single mirror PR produced an exhaustive pass. The file was never
    forward-ported to the 2.x line, so v2 PRs were reviewed at default depth."""
    import json
    path = os.path.join(REPO, ".greptile", "config.json")
    assert os.path.exists(path), ".greptile/config.json missing - v2 PRs get shallow reviews"
    cfg = json.load(open(path))
    assert cfg["strictness"] == 1
    assert set(cfg["commentTypes"]) == {"logic", "syntax", "style"}


def test_findings_catalog_keeps_the_pattern_lesson():
    """The v1.0.78 self-audit section carries the rule that prevents the exact
    class of regression G13 catches: fix the PATTERN, not the instance."""
    cat = open(os.path.join(REPO, "docs", "greptile_findings_catalog.md")).read()
    assert "Self-audit round (v1.0.78)" in cat
    assert "grep for the PATTERN, not the" in cat
    assert "G13" in cat, "the new gate rule must be documented in the catalog"
