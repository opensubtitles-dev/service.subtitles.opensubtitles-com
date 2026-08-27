"""Every shipped strings.po must be syntactically valid PO - Kodi silently
falls back to English for a catalog it cannot parse (an unquoted msgstr
shipped in zh_CN once)."""
import glob
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_all_po_files_have_quoted_msgid_msgstr():
    po_files = glob.glob(os.path.join(REPO, "resources", "language", "*", "strings.po"))
    assert po_files, "no language catalogs found"
    bad = []
    for po in po_files:
        with open(po, encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                s = line.strip()
                if s.startswith(("msgid", "msgstr", "msgctxt")):
                    payload = s.split(None, 1)[1] if " " in s else ""
                    if not re.fullmatch(r'"(?:[^"\\]|\\.)*"', payload):
                        bad.append(f"{os.path.relpath(po, REPO)}:{lineno}: {s}")
    assert not bad, "malformed PO lines:\n" + "\n".join(bad)
