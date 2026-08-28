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
