"""One-off helper: build locale/tr/LC_MESSAGES/django.po from {% trans %} and gettext in code."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Sadece proje uygulamaları; site-packages veya yanlış eşleşmeleri dışla.
APP_TOPLEVEL = frozenset(
    {
        "accounts",
        "academic",
        "audit_logs",
        "config",
        "core",
        "courses",
        "dashboard",
        "enrollments",
        "instructors",
        "students",
    }
)


def po_escape(s: str) -> str:
    return s.replace("\\", r"\\").replace('"', r"\"").replace("\n", r"\n")


def main() -> int:
    strings: set[str] = set()
    for p in sorted(ROOT.glob("templates/**/*.html")):
        t = p.read_text(encoding="utf-8")
        for m in re.finditer(r'\{%\s*trans\s+"([^"]+)"\s*%\}', t):
            strings.add(m.group(1))
        for m in re.finditer(r'\{%\s*blocktrans\s*%\}\s*([^%]+)\s*\{%\s*endblocktrans\s*%\}', t, re.DOTALL):
            strings.add(m.group(1).strip())

    for p in ROOT.rglob("*.py"):
        if "migrations" in p.parts or p.name == "generate_django_po.py":
            continue
        try:
            rel = p.relative_to(ROOT)
        except ValueError:
            continue
        if not rel.parts or rel.parts[0] not in APP_TOPLEVEL:
            continue
        t = p.read_text(encoding="utf-8")
        for m in re.finditer(r'_\(\s*"([^"]+)"\s*\)', t):
            strings.add(m.group(1))

    out_dir = ROOT / "locale" / "tr" / "LC_MESSAGES"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "django.po"

    header = '''msgid ""
msgstr ""
"Project-Id-Version: student-academic\\n"
"Language: tr\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"

'''
    parts = [header]
    for s in sorted(strings):
        parts.append(f'msgid "{po_escape(s)}"\n')
        parts.append(f'msgstr "{po_escape(s)}"\n\n')

    out_path.write_text("".join(parts), encoding="utf-8")
    print(f"Wrote {out_path} ({len(strings)} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
